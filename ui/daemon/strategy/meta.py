"""The metadata panel's data: `sqx.inspect.strategymeta.read` on the located .sqx, or the archived one."""

import shutil
import tempfile
from pathlib import Path

from core.datapaths import tmp_dir
from sqx.inspect import strategymeta
from ui.daemon.loader import find
from ui.daemon.strategy import archived, locate


def live(project: str, databank: str, identity: str) -> dict:
    """The fields of a live strategy, with where its file was found.

    Args:
        project: Project name.
        databank: Either spelling.
        identity: The strategy's identity.

    Returns:
        `strategymeta.read`'s dict plus `origin` (a sentence), or `{"error"}` naming why no
        file was read. The reader matches the project's tasks by the .sqx's folder name, so
        a copy found outside the databank folder is read from a temporary folder named as
        the databank: otherwise it would say no task writes it.
    """
    path, origin = locate.sqx(project, databank, identity)
    if path is None:
        return {"error": origin}
    cfx = locate.cfx(project)
    spelled = find.spelled(project, databank)
    if path.parent.name == spelled or cfx is None:
        return strategymeta.read(path, cfx) | {"origin": origin}
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as tmp:
        folder = Path(tmp) / spelled
        folder.mkdir()
        shutil.copy2(path, folder / path.name)
        return strategymeta.read(folder / path.name, cfx) | {"origin": origin}


def frozen(identity: str, version: str = "") -> dict:
    """The fields archived beside the version, as E2's reader wrote them that day."""
    got = archived.load(identity, version)
    if isinstance(got, str):
        return {"error": got}
    if got["meta"] is None:
        return {"error": f"La versión {got['version']} se archivó sin metadatos."}
    return got["meta"] | {"origin": f"versión archivada {got['version']}"}
