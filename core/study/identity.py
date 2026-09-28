"""The identity of a strategy named in an export: from an install, the cosecha, or the export's .sqx."""

import json
from pathlib import Path

import pandas as pd

from core import sqxfile
from core.paths import DATA, MASTER, WORKERS, databank_dir


def lookup(project: str, databank: str, names: list[str]) -> dict[str, str | None]:
    """Each named strategy's identity, from the databank folder on the master or a worker.

    Args:
        project: SQX project the export came from.
        databank: Databank name as SQX shows it.
        names: Strategy names as the export carries them; a .sqx is named after its strategy.

    Returns:
        name -> SHA-256 of its normalised XML, or None when no install still holds the file.
        A trade export does not carry identity, and a databank is rebuilt and resynced, so a
        missing file is ordinary and the verdict says so rather than inventing one.
    """
    found: dict[str, str | None] = dict.fromkeys(names)
    for install in [MASTER] + [w["path"] for w in WORKERS.values()]:
        folder = databank_dir(project, databank, install)
        for name in [n for n, v in found.items() if v is None]:
            path = folder / f"{name}.sqx"
            if path.is_file():
                found[name] = sqxfile.identity(path)
    return found


def from_harvest(project: str, databank: str, names: list[str],
                 day: str | None = None) -> dict[str, str | None]:
    """Each named strategy's identity, from the newest cosecha that paired this databank.

    Args:
        project: SQX project.
        databank: Databank name, with spaces or underscores.
        names: Strategy names as this databank spells them.
        day: The export's date; a cosecha taken after it is not trusted to name the same
            strategies, since a databank rebuilt later reuses its names.

    Returns:
        name -> identity, None where no cosecha names it. A cosecha is indexed by the BUILD
        identity and names each strategy twice: `strategy_build` as the build databank spells
        it, `strategy` as its OOS databank does. The column is chosen by which of the two
        this databank was in the cosecha's manifest — never by a name read in another one.
    """
    found: dict[str, str | None] = dict.fromkeys(names)
    wanted = databank.replace("_", " ")
    for path in sorted((DATA / "harvest" / project).glob("*/*/metrics.parquet"),
                       key=lambda p: p.parent.name, reverse=True):
        if day and path.parent.name > day:
            continue
        source = json.loads((path.parent / "manifest.json").read_text(encoding="utf-8"))["source"]
        side = {source["databank"].replace("_", " "): "strategy_build",
                source["oos_databank"].replace("_", " "): "strategy"}.get(wanted)
        if side is None:
            continue
        table = pd.read_parquet(path, columns=[side])[side]
        known = dict(zip(table, table.index))
        return {n: known.get(n) for n in names}
    return found


def from_export(folder: Path, names: list[str]) -> dict[str, str | None]:
    """Each named strategy's identity, from what an exporter left beside its export.

    Args:
        folder: An export folder; its `identity.csv` (export_trades, export_retest) is read
            first, then `strategies/*.sqx` in it and in its parent (export_spp writes
            `<day>/spp/` beside `<day>/strategies/`).
        names: Strategy names; a .sqx is named after its strategy.

    Returns:
        name -> identity, None where nothing of that name was kept.
    """
    found: dict[str, str | None] = dict.fromkeys(names)
    if (folder / "identity.csv").is_file():
        kept = pd.read_csv(folder / "identity.csv", dtype=str)
        found |= {n: i for n, i in zip(kept["strategy"], kept["identity"]) if n in found}
    for where in (folder / "strategies", folder.parent / "strategies"):
        for name in [n for n, v in found.items() if v is None]:
            path = where / f"{name}.sqx"
            if path.is_file():
                found[name] = sqxfile.identity(path)
    return found


def resolve(project: str, databank: str, names: list[str], folder: Path | None = None,
            day: str | None = None) -> dict[str, str | None]:
    """Each named strategy's identity: the installs first, then the cosecha, then the export.

    Args:
        project, databank: Where the export came from.
        names: Strategy names as the export spells them.
        folder: The export folder, for its kept .sqx; None when the caller has none.
        day: The export's date, which bounds the cosecha consulted.

    Returns:
        name -> identity, None where no source names it: an empty identity is written and
        said (`note`), never filled by a name read in another databank.
    """
    found = lookup(project, databank, names)
    for step in (lambda left: from_harvest(project, databank, left, day),
                 lambda left: from_export(folder, left) if folder else {}):
        left = [n for n, v in found.items() if v is None]
        if left:
            found |= {n: v for n, v in step(left).items() if v}
    return found


NOTE = ("sin identidad: ni una instalación, ni la cosecha, ni los .sqx de la exportación la "
        "guardan; no se empareja por nombre entre databanks")


def note(found: dict[str, str | None]) -> str:
    """The Spanish line for the names left without identity, or "" when every one has it."""
    lost = sum(1 for v in found.values() if not v)
    return f"{lost} de {len(found)} {NOTE}." if lost else ""


def warning(ident: str | None) -> list[dict]:
    """The contract's warning for one strategy signed without identity, or none."""
    return [] if ident else [{"code": "identidad", "state": "watch", "text": NOTE.capitalize() + "."}]
