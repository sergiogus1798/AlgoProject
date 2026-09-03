#!/usr/bin/env python3
"""Index every .sqx on this machine by the hash of its inner strategy XML."""

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core import sqxfile
from core.paths import STRATEGY_POOLS


def probe(path: Path) -> tuple:
    """Identity, symbol and feed of one strategy file.

    Args:
        path: A .sqx file.

    Returns:
        (path, hash, symbol, feed), or (path, None, error name, "") when the file cannot
        be read. The guard is deliberate: this corpus contains truncated .sqx, and one of
        them must not kill a 17k-file scan.
    """
    try:
        return path, sqxfile.identity(path), *sqxfile.symbol(path)
    except Exception as e:
        return path, None, type(e).__name__, ""


def main() -> None:
    """Index every pool in machine.yaml and write one JSON keyed by strategy identity."""
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--workers", type=int, default=48)
    a = ap.parse_args()

    jobs = {p: name for name, root in STRATEGY_POOLS.items() if root.is_dir()
            for p in root.rglob("*.sqx")}
    print(f"scanning {len(jobs)} .sqx across {len(STRATEGY_POOLS)} pools", file=sys.stderr)

    index, unreadable = {}, {}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for path, digest, symbol, feed in ex.map(probe, list(jobs), chunksize=64):
            if digest is None:
                unreadable[str(path)] = symbol
                continue
            record = index.setdefault(digest, {"symbol": symbol, "feed": feed, "copies": []})
            record["copies"].append({"path": str(path), "pool": jobs[path],
                                     "mtime": path.stat().st_mtime})
    a.out.write_text(json.dumps({"by_hash": index, "unreadable": unreadable}))
    print(f"unique strategies: {len(index)}   unreadable: {len(unreadable)}", file=sys.stderr)


if __name__ == "__main__":
    main()
