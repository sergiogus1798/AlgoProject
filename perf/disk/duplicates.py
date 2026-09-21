"""The same bytes stored twice: what could be deleted without losing anything."""

import hashlib
from collections import defaultdict
from pathlib import Path

from core.paths import DATA


def _fingerprint(path: Path, head: int) -> str:
    """A cheap identity for one file.

    Args:
        path: File to fingerprint.
        head: Bytes read from the start and from the end.

    Returns:
        A digest of the size, the first `head` bytes and the last `head` bytes. Two exports
        of the same databank differ in their first rows if they differ at all, so this
        catches them; hashing 1.5 GB files whole would take hours and is only needed to
        confirm a candidate this already found.
    """
    size = path.stat().st_size
    digest = hashlib.md5(str(size).encode())
    with path.open("rb") as handle:
        digest.update(handle.read(head))
        handle.seek(max(size - head, 0))
        digest.update(handle.read(head))
    return digest.hexdigest()


def groups(cfg: dict, root: Path = DATA) -> list[dict]:
    """Files that look like copies of each other.

    Args:
        cfg: What config.load() returned.
        root: Where to look; the data root by default.

    Returns:
        One row per group of two or more matching files, largest wasted space first, with
        every path so the owner can see which copy is the one to keep. Candidates, not a
        verdict: nothing here deletes anything, and a match is confirmed by comparing the
        files in full.
    """
    seen = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file() and path.stat().st_size >= cfg["disk"]["hash_bytes"]:
            seen[_fingerprint(path, cfg["disk"]["hash_head"])].append(path)
    rows = [{"copies": len(paths), "bytes": paths[0].stat().st_size,
             "wasted": paths[0].stat().st_size * (len(paths) - 1),
             "paths": [str(p.relative_to(root)) for p in paths]}
            for paths in seen.values() if len(paths) > 1]
    return sorted(rows, key=lambda r: r["wasted"], reverse=True)
