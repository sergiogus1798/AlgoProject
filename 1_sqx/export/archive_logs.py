#!/usr/bin/env python3
"""Copy SQX's logs into the data root before it prunes them. SQX keeps only 14 days."""

import argparse
import gzip
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core import manifest
from core.paths import DATA, MASTER, WORKER

# 4.6 GB single-day logs exist, so stream rather than read; level 1 keeps a daily run cheap
# and text logs compress to a few per cent either way.
CHUNK = 1 << 22
LEVEL = 1


def logs(install: Path) -> list[Path]:
    """Every log file one install currently holds.

    Args:
        install: Top-level SQX folder.

    Returns:
        The launcher logs and the engine's own daily logs, oldest name first. Anything
        older than 14 days is already gone — SQX prunes on start.
    """
    return sorted((install / "user/log").rglob("*.log"))


def archive(source: Path, dest: Path) -> bool:
    """Compress one log into the archive unless an up-to-date copy is already there.

    Args:
        source: A .log file inside the install.
        dest: Where its .gz belongs.

    Returns:
        True when it was written. A log still being appended to today is rewritten on
        the next run, because its mtime moves past the archived copy's.
    """
    if dest.exists() and dest.stat().st_mtime >= source.stat().st_mtime:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as raw, gzip.open(dest, "wb", compresslevel=LEVEL) as out:
        shutil.copyfileobj(raw, out, CHUNK)
    return True


def main() -> None:
    """Archive both installs' logs and record what was taken."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", type=Path, action="append",
                    help="repeatable; default is the master and the worker")
    a = ap.parse_args()

    for install in a.install or [MASTER, WORKER]:
        if not (install / "user/log").exists():
            continue
        out_dir = DATA / "logs" / install.name
        written = {}
        for source in logs(install):
            dest = out_dir / source.relative_to(install / "user/log").with_suffix(".log.gz")
            if archive(source, dest):
                written[str(dest.relative_to(out_dir))] = source.stat().st_size
            print(f"{'archived' if str(dest.relative_to(out_dir)) in written else 'current '}"
                  f"  {source.name:26} {source.stat().st_size:>13,} bytes")
        manifest.write(out_dir, {"install": str(install), "from": "user/log"},
                       "python3 1_sqx/export/archive_logs.py", written)
        print(f"{install.name}: {len(written)} written, archive at {out_dir}\n")


if __name__ == "__main__":
    main()
