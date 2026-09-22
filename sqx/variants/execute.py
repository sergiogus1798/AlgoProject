#!/usr/bin/env python3
"""Retest a fabricated batch on the custodian and read the IS/OOS panel back out."""

import argparse
import json
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import worker
from sqx.variants import inputs

TESTED = re.compile(r"Total tested\s+(\d+)")
SETTLE = 8          # seconds SQX needs after `load` before the databank answers for them all


def _call(command: str, cfg: dict) -> str:
    """One sqcli command against the install that holds the batch.

    Args:
        command: The sqcli command line.
        cfg: The `execute` block of config.yaml.

    Returns:
        Whatever the worker printed.
    """
    return worker.call(command, role=cfg["role"])


def awake(cfg: dict) -> bool:
    """Bring the install up if it is not already, and say whether this call did it.

    Args:
        cfg: The `execute` block of config.yaml.

    Returns:
        True when this call started it, so the caller knows to put it back. An install
        that was already awake is left awake: somebody else is using it.

        The port answers for about twenty seconds before the CLI does, replying
        `Error: CLI not ready.` in the meantime. That is normal and is polled through, not
        treated as a failure.
    """
    try:
        if "not ready" not in _call("-project action=list", cfg):
            return False
    except OSError:
        pass
    worker.start(cfg["role"])
    for _ in range(cfg["ready_tries"]):
        time.sleep(cfg["poll_seconds"])
        if "not ready" not in _call("-project action=list", cfg):
            return True
    raise SystemExit(f'{cfg["role"]} no respondio tras '
                     f'{cfg["ready_tries"] * cfg["poll_seconds"]} s')


def load(folder: Path, cfg: dict) -> None:
    """Put the batch into the harness's input databank, and nothing else with it.

    Args:
        folder: Directory of fabricated `.sqx`.
        cfg: The `execute` block.

    Returns:
        Nothing. Both databanks are cleared first so the count afterwards is the batch and
        not the batch plus whatever the last run left. Loading the same folder twice does
        NOT de-duplicate -- SQX renames the second copy `P00000(1)` and keeps both.
    """
    for bank in (cfg["input"], cfg["output"]):
        _call(f'-databank action=clear project={cfg["project"]} name={bank}', cfg)
        time.sleep(2)
    _call(f'-databank action=load project={cfg["project"]} name={cfg["input"]} '
          f"folder={folder}", cfg)
    time.sleep(SETTLE)


def run(expected: int, cfg: dict, progress: Callable[[int, str], None]) -> int:
    """Run the harness's retest task and wait for it.

    Args:
        expected: How many strategies were loaded.
        cfg: The `execute` block.
        progress: Called with a percentage and a status line as the run advances.

    Returns:
        How many strategies SQX reports as tested.

        ⚠️ `action=startOnlyTask` is NOT used: on this install it reports the project
        started and then tests nothing, silently, forever. `action=start` runs the task.
        The harness project holds exactly one task, so "start the project" and "start the
        task" are the same thing here -- and it must stay that way: a project with a Build
        task or a GoToTask would loop forever under `action=start`.
    """
    _call(f'-project action=start name={cfg["project"]}', cfg)
    done = 0
    while done < expected:
        time.sleep(cfg["poll_seconds"])
        status = _call(f'-project action=status name={cfg["project"]}', cfg)
        done = int(TESTED.search(status).group(1))
        progress(done * 100 // expected, f"{done} de {expected} reteseadas")
    return done


def panel(out: Path, cfg: dict) -> Path:
    """Export the retested databank as a CSV.

    Args:
        out: Directory to write into.
        cfg: The `execute` block.

    Returns:
        Path to the CSV. `action=export` is the only safe reader: `action=count` runs a
        sync-from-files first and destroys what `action=load` put in memory.
    """
    csv = out / "retest.csv"
    _call(f'-databank action=export project={cfg["project"]} name={cfg["output"]} '
          f"file={csv}", cfg)
    return csv


def main() -> None:
    """Load one batch, retest it, and leave the raw panel beside it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds sqx/ and manifest.parquet")
    a = ap.parse_args()

    cfg = inputs.load()["execute"]
    folder = a.work / "sqx"
    n = len(list(folder.glob("*.sqx")))

    print(f"PROGRESS 2 despertando el {cfg['role']}", flush=True)
    ours = awake(cfg)

    def say(pct: int, line: str) -> None:
        """Fold the retest's own percentage into the stage's, after the load."""
        print(f"PROGRESS {5 + pct * 90 // 100} {line}", flush=True)

    # One job, then the install goes back down -- but only if this run is what woke it.
    # A worker left running is a worker that will auto-sync, and a sync deletes the .sqx
    # it does not hold in memory (hard rule 1).
    try:
        print(f"PROGRESS 5 cargando {n} variantes en {cfg['project']}/{cfg['input']}",
              flush=True)
        load(folder, cfg)
        done = run(n, cfg, say)
        csv = panel(a.work, cfg)
    finally:
        if ours:
            worker.stop(cfg["role"])

    print(f"PROGRESS 100 {done} reteseadas, panel en {csv.name}", flush=True)
    (a.work / "ran.json").write_text(
        json.dumps({"n_loaded": n, "n_returned": done, "panel": csv.name}, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
