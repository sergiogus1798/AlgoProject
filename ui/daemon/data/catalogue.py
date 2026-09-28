"""What the data root holds, tree by tree: size, files, newest write, and the manifests that sign it."""

import re
import time
from datetime import datetime

from core import manifest
from core.paths import DATA
from perf.disk import inventory
from perf.inputs import config

DAY = 86400
# An archived strategy's folder is named by its identity, which the window never prints
# (encargo 22 §10): those branches are folded into `archive/`, whose row still counts them.
IDENTITY = re.compile(r"[0-9a-f]{64}")


def _signed() -> dict[str, dict]:
    """Every branch's manifests: how many sit under it and the newest date one of them carries.

    Returns:
        {branch: {"exports": int, "signed": "YYYY-MM-DD", "command": str}} for every
        ancestor of every `manifest.json`, down to inventory's depth. `command` is the
        branch's own manifest's, empty when the manifest is further down.
    """
    out: dict[str, dict] = {}
    for path in DATA.rglob("manifest.json"):
        parts = path.parent.relative_to(DATA).parts
        m = manifest.read(path.parent)
        for depth in range(1, min(len(parts), inventory.DEPTH) + 1):
            row = out.setdefault("/".join(parts[:depth]),
                                 {"exports": 0, "signed": "", "command": ""})
            row["exports"] += 1
            row["signed"] = max(row["signed"], str(m.get("date", "")))
            if depth == len(parts):
                row["command"] = str(m.get("command", ""))
    return out


def catalogue() -> dict:
    """Every tree of the data root with its size, files, newest write and manifests.

    Returns:
        `{"root", "total_bytes", "stale_days", "rows"}`, root being the data root's folder
        name only — never the machine's absolute path; each row carries `branch`,
        `depth`, `bytes`, `files`, `formats`, `newest` (date of the last write), `age_days`,
        `stale` and, from the manifests, `exports`, `signed` and `command`. Rows come in
        `perf.disk.inventory`'s order, biggest first; the window nests them by `branch`.
    """
    cfg = config.load()
    now, signed = time.time(), _signed()
    rows = []
    for r in inventory.tree(cfg):
        parts = r["branch"].split("/")
        if any(IDENTITY.fullmatch(p) for p in parts):
            continue
        rows.append({**r, "depth": len(parts),
                     "newest": datetime.fromtimestamp(now - r["age_days"] * DAY).strftime("%Y-%m-%d"),
                     **signed.get(r["branch"], {"exports": 0, "signed": "", "command": ""})})
    return {"root": DATA.name, "stale_days": cfg["disk"]["stale_days"], "rows": rows,
            "total_bytes": sum(r["bytes"] for r in rows if r["depth"] == 1)}
