#!/usr/bin/env python3
"""Run SQX's own data update on the master, guarded against the two ways it destroys work."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from core.assets import write_dataranges
from core.datapaths import data_update_backups
from core.paths import MASTER
from core.worker import holding

UPDATE_TIMEOUT_S = 6 * 3600  # a full download of every symbol is hours; only a hung sqcli passes this
SNAPSHOTS = data_update_backups()


def inventory(install: Path) -> dict[str, int]:
    """Every strategy file on disk under one install's projects, with its size.

    Args:
        install: Top-level SQX folder.

    Returns:
        Path relative to user/projects, to size in bytes. This is the witness for hard
        rule 1: every sqcli run ends with "Synchronizing databanks to files", and that sync
        deletes on-disk `.sqx` the databank does not hold in memory.
    """
    root = install / "user" / "projects"
    return {str(p.relative_to(root)): p.stat().st_size for p in root.rglob("*.sqx")}


def save(snapshot: dict[str, int], when: str) -> Path:
    """Write one inventory to the data root, so a later session can still compare.

    Args:
        snapshot: What inventory() returned.
        when: Timestamp the file is named after.

    Returns:
        The file written.
    """
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOTS / f"{when}.json"
    path.write_text(json.dumps(snapshot, indent=1, sort_keys=True), encoding="utf-8")
    return path


def update(install: Path, symbol: str | None) -> tuple[str, int]:
    """Drive `-data action=update` on one install, the CLI form of the GUI's "Update all".

    Args:
        install: Top-level SQX folder. The master: a download on a worker is thrown away,
            because sqx-worker.sh rsyncs user/data master-to-worker on every start.
        symbol: One SQX symbol, or None for every symbol the install has configured.

    Returns:
        (everything sqcli printed, its exit code; 124 on timeout). It never raises, so the caller
        still checks rule 1 whatever happened: the sync ran either way. The same
        `env -u ELECTRON_RUN_AS_NODE ./sqcli` invocation bin/sqx-worker.sh uses, from the install's own directory, which sqcli requires.
    """
    cmd = ["./sqcli", "-data", "action=update"] + ([f"symbol={symbol}"] if symbol else [])
    try:
        done = subprocess.run(cmd, cwd=install, capture_output=True, text=True,
                              env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home())},
                              timeout=UPDATE_TIMEOUT_S)
    except subprocess.TimeoutExpired as e:
        out = [x.decode() if isinstance(x, bytes) else x or "" for x in (e.stdout, e.stderr)]
        return "".join(out) + f"\nsqcli -data update: timeout after {UPDATE_TIMEOUT_S} s", 124
    return done.stdout + done.stderr, done.returncode


def lost(before: dict[str, int], after: dict[str, int]) -> list[str]:
    """Strategy files the update cost, which is the failure hard rule 1 names.

    Args:
        before, after: Inventories taken either side of the run.

    Returns:
        One line per file that vanished or shrank to nothing. Empty is the expected result
        and the only acceptable one; anything here means the sync ate work.
    """
    return [f"{name} ({before[name]} bytes)" for name in sorted(before)
            if after.get(name, 0) == 0]


def main() -> None:
    """Update the master's data, refusing while its GUI is up and proving nothing was lost."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="really run it; otherwise a dry run")
    ap.add_argument("--symbol", help="one SQX symbol; default is every configured symbol")
    a = ap.parse_args()

    pids = holding(MASTER)
    if pids:
        sys.exit(f"SQX está corriendo desde {MASTER} (PID {', '.join(map(str, pids))}).\n"
                 "Ciérralo tú y vuelve a lanzarlo: la regla dura 2 prohíbe sqcli en el maestro\n"
                 "con la GUI levantada, y este comando acaba en un sync que borra .sqx de disco.")

    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    before = inventory(MASTER)
    print(f"{len(before)} .sqx en disco bajo {MASTER}/user/projects")
    if not a.apply:
        print(f"ENSAYO. Lanzaría: ./sqcli -data action=update"
              f"{' symbol=' + a.symbol if a.symbol else ''}  (cwd {MASTER})")
        print("Añade --apply para hacerlo de verdad.")
        return

    print(f"foto guardada en {save(before, when)}")
    out, rc = update(MASTER, a.symbol)
    print(out)

    after = inventory(MASTER)
    gone = lost(before, after)
    save(after, f"{when}-despues")
    if gone:
        print(f"\n⚠️ REGLA 1: el sync se llevó {len(gone)} .sqx:", *gone, sep="\n  ")
    else:
        print(f"\nregla 1 ok: los {len(before)} .sqx siguen en disco")

    moved = write_dataranges()
    print("\n".join(moved) if moved else "_policy.yaml ya estaba al día")
    if rc:
        sys.exit(f"sqcli -data update exited {rc}")


if __name__ == "__main__":
    main()
