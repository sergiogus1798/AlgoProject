"""Where a study's input lives on the data root, found before a run is offered — never computed."""

import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from core.datapaths import variants_dir
from core.paths import DATA
from pipeline.ledger.state import work_dir
from sqx.projects import registry


def newest(root: Path, pattern: str) -> Path | None:
    """The last match of a glob in name order, which is date order for the dated trees.

    Args:
        root: Folder to search.
        pattern: Glob relative to it, e.g. "*/trades.parquet".

    Returns:
        The match, or None when there is none.
    """
    found = sorted(root.glob(pattern))
    return found[-1] if found else None


def distinct(trades: Path, column: str) -> list[str]:
    """The values one column of an export takes; empty when the export has no such column.

    Args:
        trades: A `trades.parquet`, file or partitioned folder.
        column: `Symbol`, `Sample type`, …

    Returns:
        Sorted values, read from that column alone.
    """
    if column not in pq.ParquetDataset(trades).schema.names:
        return []
    col = pq.read_table(trades, columns=[column]).column(column)
    if not pa.types.is_dictionary(col.type):
        return sorted(pc.unique(col).to_pylist())
    # Unique codes per chunk, not the dictionary itself: a categorical filtered before it
    # was written keeps categories no row uses. 12 M rows read in 0.25 s this way.
    return sorted({v for c in col.chunks for v in c.dictionary.take(pc.unique(c.indices)).to_pylist()})


def markets(trades: Path) -> list[str]:
    """The feeds an export's `Symbol` column names. Every export since 2026-09-24 carries
    `Symbol` even on one market, so a cross-market export is one naming more than one."""
    return distinct(trades, "Symbol")


def export_timeframe(day: Path) -> str | None:
    """The one timeframe an export's manifest declares, or None when it declares several or none.

    Args:
        day: `raw/<P>/<D>/<day>/`.

    Returns:
        e.g. "H1".
    """
    said = json.loads((day / "manifest.json").read_text(encoding="utf-8"))
    frames = said.get("source", {}).get("timeframes") or []
    return frames[0] if len(frames) == 1 else None


def harvest_timeframe(folder: Path) -> str | None:
    """The one build timeframe of a harvest, or None when it mixes several.

    Args:
        folder: `harvest/<P>/<D>/<day>/`.

    Returns:
        e.g. "M30", read off its `TimeFrame [IS]` column.
    """
    frames = pd.read_parquet(folder / "metrics.parquet", columns=["TimeFrame [IS]"])
    found = frames["TimeFrame [IS]"].astype(str).unique()
    return found[0] if len(found) == 1 else None


def batch(project: str, strategy: str, needs: tuple[str, ...]) -> Path | str:
    """One mother's variant batch, from the factory or from the pipeline.

    Args:
        project: Project name.
        strategy: The mother's name as SQX spells it.
        needs: Files the study reads inside the batch.

    Returns:
        The folder, or the sentence why none can be chosen: absent, or present in both
        places — the window does not pick one of two batches for the owner.
    """
    found = [d for d in (variants_dir(project, strategy), work_dir(project, strategy))
             if all((d / n).exists() for n in needs)]
    if not found:
        return (f"no hay lote de variantes con {', '.join(needs)} para {strategy} "
                "(skill /variants)")
    if len(found) > 1:
        return (f"hay dos lotes de {strategy}, {found[0]} y {found[1]}: córrelo desde la "
                "terminal con --work el que quieras")
    return found[0]


def scaling_day(project: str, trades: Path) -> str | None:
    """The cross-timeframe fabrication an export retested: the newest one its siblings came from.

    Args:
        project: Project name.
        trades: The export's `trades.parquet`, under `raw/<P>/<D>/<day>/`.

    Returns:
        The day of `crosstf/<P>/<day>/` whose `scaling.parquet` names a strategy the export
        holds, newest first and never after the export; None when none does — then this
        export is not a cross-timeframe retest.
    """
    held = set(pd.read_parquet(trades, columns=["strategy"])["strategy"].astype(str))
    for found in sorted((DATA / "crosstf" / project).glob("*/scaling.parquet"), reverse=True):
        if found.parent.name <= trades.parent.name and held & set(
                pd.read_parquet(found, columns=["name"])["name"]):
            return found.parent.name
    return None


def enrolled(project: str) -> dict | None:
    """The project's newest row of `AlgoData/projects/registry.csv` that names a template.

    Args:
        project: Project name.

    Returns:
        The row (symbol, timeframe, template, install…), or None when the builder never
        recorded it with a template.
    """
    return next((r for r in reversed(registry.rows())
                 if r["name"] == project and r["template"]), None)


def family(project: str) -> str | None:
    """The template family a project's ledger rows are signed under (owner, Q9 of plan 24).

    Args:
        project: Project name.

    Returns:
        The template's name — its folder in the library, since every library template is
        `<name>/template.sqx` and the file's own stem would sign every project "template" —
        or None when the registry names no template: then nothing is signed.
    """
    row = enrolled(project)
    if row is None:
        return None
    path = Path(row["template"])
    return path.parent.name if path.name == "template.sqx" else path.stem


def no_family(project: str) -> str:
    """The sentence a study that signs the ledger answers when the project has no template."""
    return (f"el proyecto {project} no tiene plantilla en projects/registry.csv: sin familia "
            "no se apunta la mirada en el ledger, así que no se corre (córrelo desde la "
            "terminal con --family si sabes cuál es)")
