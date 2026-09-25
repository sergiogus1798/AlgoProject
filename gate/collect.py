"""One databank's three tables, taken in a single staging of its files."""

import shutil
from pathlib import Path

import pandas as pd

from core import exportdrv, sqxfile, sqxstats, tradestore

SUFFIXES = (" (IS)", " (OOS)")   # the two blocks a paired view emits, by sampleType 10 and 20


def index(folder: Path) -> dict[str, Path]:
    """Every strategy of a databank, keyed by what identifies it across databanks.

    Args:
        folder: A databank directory.

    Returns:
        `core.sqxfile.identity` to the file. That identity hashes the definition with
        SQX's own bookkeeping stripped, and the stripping is load-bearing: 🔬 2026-09-23, a
        retest flips `makeExternal` on every <variable> and nothing else, so the RAW xml
        matched 0 of 115 across a build/retest pair while the normalised one matched
        115 of 115. The earlier "5 of 5" on `SPP IS`/`SPP OOS` held only because both
        sides of that pair had already been through a retest. The name cannot be the key
        either — SQX renames on collision, and two databanks of the same project were
        found holding entirely different strategies under one name.
    """
    return {sqxfile.identity(f): f for f in sorted(folder.glob("*.sqx"))}


def measured(metrics: pd.DataFrame) -> str:
    """Which of the view's two sample blocks this databank actually filled.

    Args:
        metrics: One databank's export, as the CSV gave it.

    Returns:
        " (IS)" or " (OOS)". SQX fills the block its task is designated as and leaves the
        other at zero, and **which one that is cannot be assumed**: 🔬 measured 2026-09-23,
        `XAUUSD/SPP OOS` puts its retest numbers under (IS) and `XAU_ISOOS_ejemplo/OOS`
        puts them under (OOS). Taking the wrong one returns a column of zeros with nothing
        failing, so it is read off the data every time.

    Raises:
        SystemExit: Both blocks carry numbers, which means this databank was filled by a
            task that ran its own in/out split. Half its numbers would be dropped on a
            guess, so the gate refuses rather than picking.
    """
    numeric = metrics.apply(pd.to_numeric, errors="coerce")
    # Only the metrics the view emits at BOTH sample types can tell the blocks apart. A
    # structural column like `Param Count (IS)` carries a number whatever the task ran,
    # and counting it would make every databank look like it filled the (IS) block.
    bare = {c[: -len(s)] for c in metrics.columns for s in SUFFIXES if c.endswith(s)}
    paired = sorted(n for n in bare if all(f"{n}{s}" in metrics.columns for s in SUFFIXES))
    weight = {s: numeric[[f"{n}{s}" for n in paired]].abs().sum().sum() for s in SUFFIXES}
    filled = [s for s, w in weight.items() if w > 0]
    if len(filled) != 1:
        raise SystemExit(
            f"este databank llena {filled or 'ninguno'} de los dos bloques de la vista, "
            f"sobre {len(paired)} metricas pareadas {weight}. La puerta empareja dos "
            f"databanks de UNA ventana cada uno; uno que llena los dos corrio su propio "
            f"corte dentro y no se puede saber cual mitad es el retesteo")
    return filled[0]


def tables(files: list[Path], work: Path, view: str) -> dict:
    """Stage a set of strategies once, and take everything they hold.

    Args:
        files: The .sqx to take, from one databank.
        work: Scratch directory; nothing in it survives this call.
        view: Databank view to export the metrics through.

    Returns:
        `metrics` (one row per identity, only the columns that carry numbers, their sample
        suffix stripped), `trades`, `equity`, `seen` — how many strategies the worker
        reported — and `sample`, which of the view's two blocks this databank had filled.
    """
    staged = work / "sqx"
    staged.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy(f, staged / f.name)
    ids = {f.stem: sqxfile.identity(f) for f in sorted(staged.glob("*.sqx"))}

    seen = exportdrv.metrics(staged, view, work / "metrics.csv")
    metrics = pd.read_csv(work / "metrics.csv", sep=";", encoding="utf-8-sig")
    suffix = measured(metrics)
    metrics["identity"] = metrics["Strategy Name"].map(ids)
    keep = [c for c in metrics.columns if c.endswith(suffix)]
    metrics = metrics[["identity", "Strategy Name"] + keep].rename(
        columns={c: c[: -len(suffix)] for c in keep}).set_index("identity")

    exportdrv.trades(staged, work / "csv")
    tradestore.pack(sorted((work / "csv").glob("*.csv")), work / "trades.parquet", False)
    trades = pd.read_parquet(work / "trades.parquet")
    trades["identity"] = trades["strategy"].astype(str).map(ids)

    curves = {ids[f.stem]: sqxstats.equity(f, "Main") for f in sorted(staged.glob("*.sqx"))}
    equity = pd.DataFrame(curves).rename_axis("day").reset_index().melt(
        id_vars="day", var_name="identity", value_name="equity").dropna()

    shutil.rmtree(work)
    return {"metrics": metrics, "trades": trades.drop(columns="strategy"), "equity": equity,
            "seen": seen, "sample": suffix.strip()}
