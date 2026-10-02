"""One databank's three tables, taken in a single staging of its files."""

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from core import exportdrv, fanout, sqxfile, sqxstats, tradepack, tradestore
from core.sqxview import LABEL, VIEW

PREFIX = {"IS": "IS__", "OOS": "OOS__"}   # which databank a staged file came from
# 🔬 2026-10-01, 2 x 5,130 strategies: the identities were hashed twice in one thread (33 s)
# and the 10,260 CSVs parsed in one (35 s) of a 204 s harvest whose JVM takes 45.
WORKERS = 8


def identities(files: list[Path]) -> dict[Path, str]:
    """`core.sqxfile.identity` of many files, across processes: 1.6 ms each in one."""
    return dict(fanout.run(sqxfile.identity, {f: 1 for f in files}, WORKERS))


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
    files = sorted(folder.glob("*.sqx"))
    ids = identities(files)
    return {ids[f]: f for f in files}


def measured(stats: dict[str, dict]) -> int:
    """Which of the two sample blocks this databank actually filled.

    Args:
        stats: Staged file stem to `sqxstats.stats()` of its main result.

    Returns:
        10 or 20. SQX fills the block its task is designated as and leaves the other at
        zero, and **which one that is cannot be assumed**: 🔬 measured 2026-09-23,
        `XAUUSD/SPP OOS` puts its retest numbers under (IS) and `XAU_ISOOS_ejemplo/OOS`
        puts them under (OOS). Taking the wrong one returns a column of zeros with nothing
        failing, so it is read off the data every time — on the metrics both blocks carry,
        since a structural one like `Param Count` holds a number whatever the task ran.

    Raises:
        SystemExit: Both blocks carry numbers, which means this databank was filled by a
            task that ran its own in/out split. Half its numbers would be dropped on a
            guess, so the gate refuses rather than picking.
    """
    paired = sorted({k for _, k in VIEW[10]} & {k for _, k in VIEW[20]})
    weight = {n: sum(abs(float(st.get(n, {}).get(k, 0))) for st in stats.values() for k in paired)
              for n in VIEW}
    filled = [n for n, w in weight.items() if w > 0]
    if len(filled) != 1:
        raise SystemExit(
            f"este databank llena {[LABEL[n] for n in filled] or 'ninguno'} de los dos bloques "
            f"de muestra, sobre {len(paired)} metricas pareadas {weight}. La puerta empareja "
            f"dos databanks de UNA ventana cada uno; uno que llena los dos corrio su propio "
            f"corte dentro y no se puede saber cual mitad es el retesteo")
    return filled[0]


def metrics(staged: dict[str, Path]) -> tuple[pd.DataFrame, str]:
    """One databank's metrics, the view's columns, read off each file with no SQX running.

    Args:
        staged: File stem to the .sqx.

    Returns:
        (one row per stem with `Strategy Name`, `TimeFrame` and the filled block's columns,
        the block's label). The timeframe is the feed's suffix inside the file's result name.
    """
    stats = {stem: sqxstats.stats(f) for stem, f in staged.items()}
    block = measured(stats)
    rows = {stem: {"Strategy Name": stem,
                   **({"TimeFrame": sqxfile.symbol(staged[stem])[1].rsplit("_", 1)[-1]}
                      if block == 10 else {}),
                   **{col: st[block][key] for col, key in VIEW[block]}}
            for stem, st in stats.items()}
    return pd.DataFrame.from_dict(rows, orient="index"), LABEL[block]


def tables(sides: dict[str, list[Path]], work: Path,
           exports: dict[str, Path] | None = None) -> dict:
    """Stage both databanks' strategies once, and take everything they hold in one pass.

    Args:
        sides: "IS" and "OOS" to the .sqx to take from each databank.
        work: Scratch directory; nothing in it survives this call.
        exports: Side to a folder that receives that side's `trades.parquet` as
            `sqx.export.export_trades` packs it, with what its manifest counts beside it in
            `packed` -- the same `orderstocsv` then serves the databank's own trade export.

    Returns:
        Per side: `metrics` (one row per identity, the view's columns of the block it filled,
        without the block's suffix), `trades`, `equity`, `seen` -- how many strategies that
        side holds -- `sample`, which of the two blocks it filled, and `packed`.

        Both sides go into ONE staging folder under a side prefix, because SQX names a
        loaded strategy after its file (`knowhow/sqx-format/loaded-name-is-filename.md`): the
        prefix keeps the two copies of a strategy apart, and it is what splits the trades back
        afterwards. The metrics and the curves are read off the files; the one JVM left is
        `orderstocsv`, a one-shot `sqcli` on the conductor -- the conductor cycle the metrics
        export needed (~36 s to start and stop) is gone.
    """
    shutil.rmtree(work, ignore_errors=True)       # what a run that died half-way left
    staged = work / "sqx"
    staged.mkdir(parents=True, exist_ok=True)
    known = identities([f for files in sides.values() for f in files])
    ids, side_of = {}, {}
    for side, files in sides.items():
        for f in files:
            stem = PREFIX[side] + f.stem
            shutil.copy(f, staged / f"{stem}.sqx")
            ids[stem], side_of[stem] = known[f], side

    # The curves and the metrics are read off the files while the JVM writes the trades: it
    # is a subprocess, and the wait for it was ~10 s of reading left for afterwards.
    with ThreadPoolExecutor(1) as jvm:
        exported = jvm.submit(exportdrv.trades, staged, work / "csv")
        curves = {stem: sqxstats.equity(staged / f"{stem}.sqx", "Main") for stem in sorted(ids)}
        read = {side: metrics({stem: staged / f"{stem}.sqx" for stem in ids
                               if side_of[stem] == side}) for side in sides}
        exported.result()

    out = {}
    for side in sides:
        # Each side's CSVs under the strategies' own names, so the pack names its rows as
        # the databank's export does: the prefix is constant, the order is the same.
        csvs = work / f"csv_{side}"
        csvs.mkdir()
        for f in sorted((work / "csv").glob(f"{PREFIX[side]}*.csv")):
            f.rename(csvs / f.name[len(PREFIX[side]):])
        packed = (exports or {}).get(side, work / side) / "trades.parquet"
        packed.parent.mkdir(parents=True, exist_ok=True)
        counts = tradepack.pack(sorted(csvs.glob("*.csv")), packed, per_market=False)
        drawn = pd.read_parquet(packed)
        mine, label = read[side]
        mine = mine.assign(identity=mine["Strategy Name"].map(ids),
                           **{"Strategy Name": mine["Strategy Name"].str[len(PREFIX[side]):]})
        own = {stem[len(PREFIX[side]):]: i for stem, i in ids.items() if side_of[stem] == side}
        equity = pd.DataFrame({ids[s]: c for s, c in curves.items() if side_of[s] == side})
        out[side] = {
            "metrics": mine.set_index("identity"),
            "trades": drawn.assign(identity=drawn["strategy"].astype(str).map(own)).drop(
                columns=["strategy"]),
            "equity": equity.rename_axis("day").reset_index().melt(
                id_vars="day", var_name="identity", value_name="equity").dropna(),
            "seen": len(mine), "sample": label, "packed": counts}
    # One set of categories over both sides, as one frame of both had: two sides that differ
    # in a text column would otherwise come out of their concat as plain text.
    for c in tradestore.CATEGORICAL:
        both = [o["trades"][c] for o in out.values() if c in o["trades"]]
        values = sorted(set().union(*(b.cat.categories for b in both)))
        for o in out.values():
            if c in o["trades"]:
                o["trades"][c] = o["trades"][c].cat.set_categories(values)
    shutil.rmtree(work)
    return out
