"""`sqxfile.identity` of many files across processes, the hashes kept in this process's cache."""

from pathlib import Path

from core import fanout, sqxfile


def _one(path: Path) -> str:
    """identity() by module name, so a task pickles whatever `sqxfile.identity` is bound to."""
    return sqxfile.identity(path)


def many(files: list[Path], workers: int) -> dict[Path, str]:
    """Identity of every file, hashed in forked children: 1.6 ms each in one process.

    The children's cache dies with them, so each hash is also handed to this process's:
    a later `identity()` of the same file (the export, the curate) reads it instead of opening
    the archive again. Do not call it from a process that holds threads.
    """
    stamps = {f: f.stat() for f in files}
    found = dict(fanout.run(_one, {f: 1 for f in files}, workers))
    for f, ident in found.items():
        sqxfile.remember(f, ident, stamps[f])
    return found
