"""What the data root holds, tree by tree: files, formats, newest write, and the manifests that sign it."""

from typing import Any
import os
import re
import time
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from core import manifest
from core.paths import DATA
from perf.inputs import config

DAY = 86400
TTL = 300         # seconds the walk of the data root is reused
DEPTH = 3          # levels of the tree the window shows
STAT_UP_TO = 20   # a folder with more files than this is dated by its own mtime, not by each file
# An archived strategy's folder is named by its identity, which the window never prints
# (encargo 22 §10): those branches are folded into `archive/`, whose row still counts them.
IDENTITY = re.compile(r"[0-9a-f]{64}")


@lru_cache(maxsize=1)
def _walk(bucket: int) -> dict[str, dict]:
    """One pass over the data root: files, formats, newest write and manifests of every branch.

    Args:
        bucket: `time // TTL`; the 4-million-file walk is kept for TTL seconds, then redone.

    Returns:
        {branch: row} for every folder down to `DEPTH` with a file somewhere under it. One
        `os.walk` and no `stat` per file in a big folder: the nested walks of the old inventory
        took minutes over the root's 4 million files (`reports/` holds 4 million of them), this
        takes seconds. ponytail: a folder of more than STAT_UP_TO files is dated by its own
        mtime, so a file rewritten in place in one of those does not move «última escritura».
    """
    rows: dict[str, dict] = {}
    for root, _, files in os.walk(DATA):
        parts = os.path.relpath(root, DATA).split(os.sep)
        if not files or parts == ["."]:
            continue
        if len(files) > STAT_UP_TO:
            newest = os.stat(root).st_mtime
        else:
            newest = max(os.stat(os.path.join(root, f)).st_mtime for f in files)
        kinds = Counter(f[f.rfind("."):] if f.rfind(".") > 0 else "none" for f in files)
        m = manifest.read(Path(root)) if "manifest.json" in files else None
        for depth in range(1, min(len(parts), DEPTH) + 1):
            r = rows.setdefault("/".join(parts[:depth]), {
                "files": 0, "kinds": Counter(), "newest": 0.0,
                "exports": 0, "signed": "", "command": ""})
            r["files"] += len(files)
            r["kinds"] += kinds
            r["newest"] = max(r["newest"], newest)
            if m is not None:
                r["exports"] += 1
                r["signed"] = max(r["signed"], str(m.get("date", "")))
                if depth == len(parts):
                    r["command"] = str(m.get("command", ""))
    return rows


def catalogue() -> dict[str, Any]:
    """Every tree of the data root with its files, formats, newest write and manifests.

    Returns:
        `{"root", "stale_days", "rows"}`, root being the data root's folder name only — never
        the machine's absolute path; each row carries `branch`, `depth`, `files`, `formats`,
        `newest` (date of the last write), `age_days`, `stale` and, from the manifests,
        `exports`, `signed` and `command`. Rows come most files first; the window nests them
        by `branch`. No size: the owner does not read it and it is what made this slow.
    """
    stale_days, now = config.load()["disk"]["stale_days"], time.time()
    rows = []
    for branch, r in sorted(_walk(int(now // TTL)).items(), key=lambda kv: -kv[1]["files"]):
        parts = branch.split("/")
        if any(IDENTITY.fullmatch(p) for p in parts):
            continue
        age = (now - r["newest"]) / DAY
        rows.append({"branch": branch, "depth": len(parts), "files": r["files"],
                     "formats": ", ".join(f"{k} x{n}" for k, n in r["kinds"].most_common(3)),
                     "age_days": age, "stale": age > stale_days,
                     "newest": datetime.fromtimestamp(r["newest"]).strftime("%Y-%m-%d"),
                     "exports": r["exports"], "signed": r["signed"], "command": r["command"]})
    return {"root": DATA.name, "stale_days": stale_days, "rows": rows}
