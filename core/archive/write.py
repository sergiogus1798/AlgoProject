"""Freeze one strategy into the archive: its .sqx, its cosecha rows, every study result, its provenance."""

import importlib
import importlib.util
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from core import sqxfile
from core.archive import collect, manifest, view
from core.manifest import code_version
from core.paths import archive_dir, project_dir
from ui.daemon.loader import find

STAMP = "%Y-%m-%dT%H%M"
META = "sqx.inspect.strategymeta"          # front E2's reader; frozen only once it exists


def _stamp() -> str:
    """This minute, as a version folder is named."""
    return datetime.now().strftime(STAMP)


def _source(project: str, databank: str, identity: str, sqx: Path | None) -> tuple[Path, Path | None]:
    """The strategy file to copy, and the project.cfx beside it.

    Args:
        project: SQX project name.
        databank: Either spelling.
        identity: The strategy's identity.
        sqx: A file named by hand, for a project whose databank no install holds any more.

    Returns:
        (the .sqx, the install's project.cfx or None). Only files are read; no command
        reaches SQX. Refused while SQX runs the project — a file read then may be half a
        strategy — and refused when the file named by hand is another strategy.
    """
    spelled = find.spelled(project, databank)
    where = find.install_of(project, spelled)
    if where and find.writing(where[1], project):
        raise RuntimeError(f"SQX está escribiendo {project} en {where[0]}: se archiva cuando acabe")
    cfx = project_dir(project, where[1]) / "project.cfx" if where else None
    if sqx is not None:
        if sqxfile.identity(sqx) != identity:
            raise ValueError(f"{sqx} es otra estrategia: su identidad no es la pedida")
        return sqx, cfx
    held = [f for f in find.files(where[1], project, spelled)
            if sqxfile.identity(f) == identity] if where else []
    if not held:
        raise FileNotFoundError(f"Ningún install guarda esa estrategia en {project}/{spelled}: "
                                "pasa el .sqx a mano con --sqx (se comprueba su identidad)")
    return held[0], cfx


def _meta(sqx: Path, cfx: Path | None) -> dict | None:
    """Front E2's metadata of the strategy, None while that reader does not exist."""
    if importlib.util.find_spec(META) is None:
        return None
    return importlib.import_module(META).read(sqx, cfx)


def _seal(folder: Path) -> None:
    """Make a version read-only: files 0444, folders 0555, deepest first."""
    for root, dirs, files in os.walk(folder, topdown=False):
        for name in files:
            os.chmod(Path(root) / name, 0o444)
        os.chmod(root, 0o555)


def archive(project: str, databank: str, identity: str, step: str, note: str = "", *,
            family: str, sqx: Path | None = None) -> Path:
    """Freeze one strategy with everything needed to show and judge it again without recomputing.

    Args:
        project: SQX project name.
        databank: The build databank whose cosecha the Ficha reads, either spelling.
        identity: SHA-256 of the strategy's normalised XML.
        step: The WORKFLOW step the strategy stood at, e.g. "13" or "16.5".
        note: The owner's words, kept verbatim.
        family: The template family naming the ledger study with the asset and timeframe.
        sqx: The strategy file, only when no install holds the databank any more.

    Returns:
        `archive/<identity>/<YYYY-MM-DDTHHMM>/`, sealed read-only. It is built beside its
        final name and renamed at the end, so a crash leaves no half version; a version
        that exists already is refused, never overwritten.
    """
    final = archive_dir() / identity / _stamp()
    if final.exists():
        raise FileExistsError(f"{final} ya existe: una versión archivada no se sobrescribe")
    source, cfx = _source(project, databank, identity, sqx)
    row = manifest.registry(project)
    work = final.with_name(f".{final.name}.partial")
    work.mkdir(parents=True)
    shutil.copy2(source, work / "strategy.sqx")
    entries, loose, skipped = collect.freeze(project, identity, work / "reports")
    bank = databank.replace(" ", "_")
    tear = view.tearsheet(project, bank, identity, work / "tearsheet")
    shown = {**view.results(project, identity, entries), "tearsheet": tear,
             "gate": None if isinstance(tear, str) else view.gate(project, bank, identity, tear["day"])}
    (work / "view.json").write_text(json.dumps(shown, indent=1, default=str), encoding="utf-8")
    meta = _meta(work / "strategy.sqx", cfx)
    if meta is not None:
        (work / "meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    doc = {"identity": identity, "project": project, "databank": databank, "step": step,
           "note": note, "archived_at": datetime.now().isoformat(timespec="seconds"),
           "code_version": code_version(), "registry": row,
           "sqx": {"from": str(source), "sha256": manifest.sha256(source), "by_hand": sqx is not None},
           "harvest": None if isinstance(tear, str) else {
               "folder": tear["folder"], "rows": collect.harvest_rows(
                   Path(tear["folder"]), identity, work / "harvest")},
           "studies": entries, "loose": loose, "skipped": skipped,
           "asset": manifest.asset(row["symbol"], work / "asset"),
           "ledger": manifest.ledger(row["symbol"], row["timeframe"], family),
           "meta": "meta.json" if meta is not None else None}
    (work / "manifest.json").write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    work.rename(final)
    _seal(final)
    return final
