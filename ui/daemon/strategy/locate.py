"""Where one strategy's .sqx and its project.cfx are, by reading files only — never asking SQX."""

from pathlib import Path

from core import sqxfile
from core.paths import archive_dir, export_dir, project_dir
from ui.daemon import progress
from ui.daemon.loader import find

NOWHERE = "sin .sqx en ningún install"


def _exported(project: str, databank: str, identity: str) -> Path | None:
    """A copy of the strategy an export left under `raw/<P>/<D>/<day>/strategies/`.

    Args:
        project: Project name.
        databank: The databank asked for, whose exports are looked at first.
        identity: The strategy's identity; a file is taken only when it hashes to it.

    Returns:
        The newest matching file, or None.
    """
    root = export_dir(project, "x", "x").parent.parent
    files = sorted(root.glob("*/*/strategies/*.sqx"),
                   key=lambda f: (f.parents[2].name == databank.replace(" ", "_"),
                                  f.parents[1].name), reverse=True)
    return next((f for f in files if sqxfile.identity(f) == identity), None)


def sqx(project: str, databank: str, identity: str) -> tuple[Path | None, str]:
    """The strategy file, looked for where it is most likely to be current.

    Args:
        project: Project name.
        databank: Either spelling.
        identity: The strategy's identity.

    Returns:
        (the .sqx or None, where it came from as a sentence). First the install that holds
        the databank (`loader.find`, refused while SQX writes the project), then an export's
        copy, then the newest archived version; otherwise (None, `NOWHERE`).
    """
    spelled = find.spelled(project, databank)
    where = find.install_of(project, spelled)
    if where and find.writing(where[1], project):
        return None, f"SQX está escribiendo {project} en el {where[0]}: se lee cuando acabe"
    held = [f for f in find.files(where[1], project, spelled)
            if sqxfile.identity(f) == identity] if where else []
    if held:
        return held[0], f"{spelled} en el {where[0]}"
    copy = _exported(project, spelled, identity)
    if copy is not None:
        return copy, f"copia exportada de {copy.parents[2].name} del {copy.parents[1].name}"
    archived = sorted((archive_dir() / identity).glob("*/strategy.sqx"))
    if archived:
        return archived[-1], f"versión archivada {archived[-1].parent.name}"
    return None, NOWHERE


def cfx(project: str) -> Path | None:
    """The project.cfx of the install that has the project, workers first, or None."""
    return next((p for top in progress.installs().values()
                 if (p := project_dir(project, top) / "project.cfx").is_file()), None)
