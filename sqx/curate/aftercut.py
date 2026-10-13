"""What follows a verdict on the files: move or delete the rejected, and cut the trade export to match."""

import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from core import manifest, tradestore
from core.paths import export_dir


def remove(source: Path, into: Path | None, names: list[str]) -> tuple[int, list[str]]:
    """Take the named strategies' files out of a databank directory.

    Args:
        source: Databank directory holding them.
        into: Databank directory to move them to, created when missing; None deletes them.
        names: Strategy names, without the .sqx suffix.

    Returns:
        How many went, and the names with no file. Files are the only handle: over the HTTP
        API a name is cut at its first space and a one-shot sqcli never loads the records.
    """
    if into:
        into.mkdir(parents=True, exist_ok=True)
    gone, absent = 0, []
    for name in names:
        f = source / f"{name}.sqx"
        if not f.exists():
            absent.append(name)
            continue
        shutil.move(str(f), str(into / f.name)) if into else f.unlink()
        gone += 1
    return gone, absent


def _trimmed(frame: pd.DataFrame, kept: set[str]) -> pd.DataFrame | None:
    """`trades.parquet` cut to the kept strategies, as a fresh export of them would give it; None if unsure.

    The pack types a column over the WHOLE export: a column absent from, or typed another way in,
    one strategy is float64 for all, and a text column's categories are the values present. So a
    cut is the same frame only when (a) the categories are re-derived from what is left and (b)
    every float64 column shows a non-integral value (else it may have been an int64 column in
    every strategy left, which a fresh pack would keep int) and none is empty (a column only a
    dropped strategy had, e.g. `Ticket`, would not exist in a fresh pack). Row order is the
    export's: strategies by sorted file name, each one's trades in file order.
    """
    sub = frame[frame["strategy"].isin(kept)].reset_index(drop=True)
    for c in sub.columns:
        col = sub[c]
        if str(col.dtype) == "float64" and (col.isna().all() or (col.dropna() % 1 == 0).all()):
            return None
        if c in tradestore.CATEGORICAL and isinstance(col.dtype, pd.CategoricalDtype):
            sub[c] = col.cat.remove_unused_categories()
    return sub


def refilter(project: str, databank: str, before: dict[str, str], kept: set[str]) -> str:
    """After a cut, make the databank's trade export the subset it already was, instead of re-exporting it.

    Args:
        project, databank: The databank just cut.
        before: Name to identity of every file it held at the cut.
        kept: The names it holds now.

    Returns:
        "" when it left the export alone (stale, so the loader re-exports it as it always did),
        else the folder rewritten. The newest day's `trades.parquet`, `timeframes.csv`,
        `identity.csv` and `lineage.csv` are cut by name and the manifest is signed last, so a
        cut in between leaves it stale. Only when the export's `identity.csv` pairs EXACTLY the
        names and identities the databank held (it was made from these files) and the cut kept
        something. `lineage.csv` is cut as it is: a survivor's mother is read off the project's
        OTHER databanks, which a cut inside this one does not move.
    """
    days = sorted(d for d in export_dir(project, databank, "x").parent.glob("*")
                  if (d / "manifest.json").exists())
    if not days or not kept:
        return ""
    folder = days[-1]
    ident = folder / "identity.csv"
    names = ("trades.parquet", "timeframes.csv", "identity.csv", "lineage.csv")
    if not all((folder / n).exists() for n in names):
        return ""
    held = [ln.rsplit(",", 1) for ln in ident.read_text(encoding="utf-8").splitlines()[1:]]
    if dict(held) != before:
        return ""
    sub = _trimmed(pd.read_parquet(folder / "trades.parquet"), kept)
    if sub is None:
        return ""
    stamp = datetime.now().strftime("%H%M%S")
    text = {}
    for n, cut in (("timeframes.csv", 1), ("identity.csv", 1), ("lineage.csv", 2)):
        lines = (folder / n).read_text(encoding="utf-8").splitlines(keepends=True)
        text[n] = lines[:1] + [ln for ln in lines[1:] if ln.rsplit(",", cut)[0] in kept]
    doc = manifest.read(folder)
    old = doc["counts"]
    zones = sorted({ln.rsplit(",", 1)[1].strip() for ln in text["timeframes.csv"][1:]})
    counts = {**old, "strategies": len(text["identity.csv"]) - 1, "trades": len(sub),
              "kept_ticket": [n for n in old.get("kept_ticket", []) if n in kept],
              "torn_blocks": [n for n in old.get("torn_blocks", []) if n in kept], "timeframes": zones}
    for n, lines in text.items():
        (folder / f"{n}.{stamp}").write_text("".join(lines), encoding="utf-8")
    sub.to_parquet(folder / f"trades.parquet.{stamp}", compression="zstd", index=False)
    for n in names:
        os.replace(folder / f"{n}.{stamp}", folder / n)
    manifest.write(folder, doc["source"], doc["command"], {**counts, "cut_from": old["strategies"]})
    return str(folder)
