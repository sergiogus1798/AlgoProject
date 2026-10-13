"""Trade lists written from a live session's memory by the AlgoTrades snippet, in place of orderstocsv."""

import shutil
from pathlib import Path

from core.paths import databank_dir, export_dir, worker_dir
from sqx.projects import live
from sqx.snippets import install, toolproject

def folder(project: str, databank: str) -> Path:
    """Where the snippet writes one databank's CSVs: beside its dated exports."""
    return export_dir(project, databank, "x").parent / "_trades_mem"


def run(role: str, project: str, banks: list[str]) -> dict[str, int]:
    """Write each databank's trade CSVs from the live session's memory, one task run per databank.

    Args:
        banks: Databanks of `project` to export, already synced to disk.

    Returns:
        Strategies written per databank. Empty when the install has no tool project or its
        snippets are not compiled (`sqx.snippets.install`): `export_trades` then runs
        orderstocsv as before.
    """
    if not banks or not toolproject.cfx(role).exists() or install.pending(role):
        return {}
    wrote = {}
    for bank in banks:
        out = folder(project, bank)
        shutil.rmtree(out, ignore_errors=True)
        live.call(role, "updateTaskXML", projectName=toolproject.NAME, taskXMLFile=toolproject.MEMBER,
                  xmlConfig=toolproject.SETTINGS.format(args=f"{project}|{bank}|{out}"))
        end = live.run(role, toolproject.NAME, toolproject.CONFIG)
        if not (out / "_done.tsv").exists():     # `live.run` already raised on an aborted run
            raise SystemExit(f"{project}/{bank}: «Export trades» no escribió sus operaciones: {end}")
        wrote[bank] = len((out / "_done.tsv").read_text(encoding="utf-8").splitlines())
        on_disk = len(list(databank_dir(project, bank, worker_dir(role)).glob("*.sqx")))
        if wrote[bank] != on_disk:
            raise SystemExit(f"{project}/{bank}: la memoria dio {wrote[bank]} estrategias y el disco tiene {on_disk}")
    return wrote


def take(project: str, databank: str, names: set[str], newest: float, into: Path) -> bool:
    """Hand a finished memory export over as orderstocsv's output, when it is the databank's.

    Args:
        names: The strategies the export must hold, exactly.
        newest: Modification time of the databank's newest .sqx; an older export is another run's.
        into: Where orderstocsv would have written; must not exist.

    Returns:
        Whether `into` now holds the CSVs. The folder is consumed either way.
    """
    out = folder(project, databank)
    done = out / "_done.tsv"
    fresh = (done.exists() and done.stat().st_mtime >= newest
             and {line.split("\t")[0] for line in done.read_text(encoding="utf-8").splitlines()} == names)
    if fresh:
        done.unlink()
        out.rename(into)
    shutil.rmtree(out, ignore_errors=True)
    return fresh
