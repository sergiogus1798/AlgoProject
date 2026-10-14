"""Proof that a run left a folder alone: a fingerprint before and after, or the folder made read-only."""

import hashlib
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def fingerprint(folder: Path, pattern: str = "*") -> str:
    """One hash of every file under a folder whose name matches: path, size and mtime.

    Args:
        folder: The tree to watch.
        pattern: A file-name glob, e.g. "PORTFOLIO_*" for the ledger studies only a
            portfolio run writes — other sessions append to the rest of the real ledger.

    Returns:
        A sha256 that moves when a matching file appears, disappears, grows or is rewritten.
    """
    rows = sorted(
        f"{f.relative_to(folder)}|{f.stat().st_size}|{f.stat().st_mtime_ns}"
        for f in folder.rglob(pattern)
        if f.is_file()
    )
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


@contextmanager
def untouched(folder: Path, pattern: str = "*") -> Iterator[None]:
    """Fail the block when it changed a matching file of the folder.

    Raises:
        RuntimeError: The fingerprint moved between entry and exit.
    """
    before = fingerprint(folder, pattern)
    yield
    if fingerprint(folder, pattern) != before:
        raise RuntimeError(f"la ejecución de prueba ha tocado {folder} ({pattern})")


@contextmanager
def readonly(folder: Path) -> Iterator[None]:
    """Take the write bit off a whole tree for the block, then put every mode back.

    ⚠️ Every process loses the write, not only this one: never on a folder another session
    or a running autopilot appends to — which the real ledger is. Use `untouched` there.
    """
    modes = {
        p: p.stat().st_mode for p in [folder, *folder.rglob("*")] if not p.is_symlink()
    }
    for p, mode in modes.items():
        os.chmod(p, mode & ~0o222)
    try:
        yield
    finally:
        for p, mode in modes.items():
            os.chmod(p, mode)
