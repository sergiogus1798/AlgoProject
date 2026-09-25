"""The identity of a strategy named in an export, read from its .sqx wherever an install keeps it."""

from core import sqxfile
from core.paths import MASTER, WORKERS, databank_dir


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
