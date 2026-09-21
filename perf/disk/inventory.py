"""What the data root actually holds: where the bytes are, in what format, and how old."""

import time
from collections import Counter
from pathlib import Path

from core.paths import DATA

DAY = 86400
DEPTH = 3


def _walk(where: Path) -> tuple[int, int, Counter, float]:
    """Everything under one directory, counted in one pass.

    Args:
        where: Directory to descend.

    Returns:
        Bytes, file count, a count per extension, and the newest modification time. One
        pass because the data root is 2 GB across tens of thousands of files, and walking
        it once per statistic is the difference between seconds and minutes.
    """
    total, files, kinds, newest = 0, 0, Counter(), 0.0
    for path in where.rglob("*"):
        if path.is_file():
            info = path.stat()
            total += info.st_size
            files += 1
            kinds[path.suffix or "none"] += 1
            newest = max(newest, info.st_mtime)
    return total, files, kinds, newest


def tree(cfg: dict, root: Path = DATA) -> list[dict]:
    """One row per branch of the data root, down to a fixed depth.

    Args:
        cfg: What config.load() returned.
        root: Where to start; the data root by default.

    Returns:
        Branch, bytes, files, the three commonest extensions, days since anything in it was
        written, and whether that is past `disk.stale_days`. Sorted biggest first, because
        the only branches worth a decision are the big ones.
    """
    rows, now = [], time.time()
    for path in sorted(root.rglob("*")):
        if not path.is_dir() or len(path.relative_to(root).parts) > DEPTH:
            continue
        total, files, kinds, newest = _walk(path)
        if not files:
            continue
        age = (now - newest) / DAY
        rows.append({"branch": str(path.relative_to(root)), "bytes": total, "files": files,
                     "formats": ", ".join(f"{k} x{n}" for k, n in kinds.most_common(3)),
                     "age_days": age, "stale": age > cfg["disk"]["stale_days"]})
    return sorted(rows, key=lambda r: r["bytes"], reverse=True)
