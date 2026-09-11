#!/usr/bin/env python3
"""Move the strategies a verdict rejected into another databank, with the master shut down."""

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from core import manifest, worker
from core.paths import DATA, MASTER, databank_dir

DROP = "DESCARTAR"


def master_is_up() -> bool:
    """Whether anything is holding the master install.

    Returns:
        True if the master is running. Its databases take an exclusive lock, so the command
        line cannot open the install while the GUI has it, and a file edited underneath a
        running instance is silently undone by the next sync.
    """
    worker.require_posix()
    found = subprocess.run(["pgrep", "-f", f"{MASTER}/StrategyQuantX"],
                           capture_output=True, text=True)
    return found.returncode == 0


def sqcli(command: list[str]) -> str:
    """Run one command against the master install and return what it said.

    Args:
        command: Arguments after the executable, e.g. ["-databank", "action=count", ...].
            Each is passed as its own argument, so a value containing spaces — every SQX
            strategy name does — needs no quoting and no length limit.

    Returns:
        The command's output. This is the one place in the project that drives the master
        rather than the worker, because a project's databanks only exist in its own install.
    """
    worker.require_posix()
    clean = {k: v for k, v in os.environ.items() if k != "ELECTRON_RUN_AS_NODE"}
    return subprocess.run([str(MASTER / "sqcli"), *command], cwd=MASTER, env=clean,
                          capture_output=True, text=True, check=True).stdout


def snapshot(project: str, databank: str, day: str) -> Path:
    """Copy the source databank's files aside before anything is moved.

    Args:
        project: Project on the master.
        databank: Databank the strategies are leaving.
        day: Today, for the directory name.

    Returns:
        Where the copies went. Every sync deletes on-disk strategies that are not in memory,
        so the only safe backup is one taken outside the install.
    """
    dest = DATA / "snapshots" / day / project / databank.replace(" ", "_")
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(databank_dir(project, databank, MASTER).glob("*.sqx")):
        dest.joinpath(f.name).write_bytes(f.read_bytes())
    return dest


def main() -> None:
    """Print what would move; move it only when --apply is given and the master is closed."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--verdict", required=True, help="path of a verdict.csv")
    ap.add_argument("--into", required=True, help="databank to move the rejected into; create "
                                                  "it in the GUI first")
    ap.add_argument("--apply", action="store_true", help="without it nothing is touched")
    a = ap.parse_args()

    calls = pd.read_csv(a.verdict)
    names = sorted(calls.loc[calls.verdict == DROP, "strategy"])
    keep = len(calls) - len(names)
    print(f"{len(calls)} strategies judged: {keep} stay in {a.databank}, "
          f"{len(names)} move to {a.into}")
    for n in names[:10]:
        print(f"  {n}")
    if len(names) > 10:
        print(f"  ... and {len(names) - 10} more")
    if not a.apply:
        print("\ndry run. Re-run with --apply, with the master's GUI closed, to move them.")
        return

    if master_is_up():
        sys.exit(f"the master is running. Close its GUI first — nothing can write to {MASTER} "
                 f"while it is up, and a write that looks successful would be lost on its sync.")

    day = date.today().isoformat()
    saved = snapshot(a.project, a.databank, day)
    before = len(list(saved.glob("*.sqx")))
    print(f"backed up {before} strategies to {saved}")

    print(sqcli(["-databank", "action=move", f"project={a.project}", f"name={a.databank}",
                 f"destproject={a.project}", f"destdatabank={a.into}",
                 f"strategies={','.join(names)}"]))

    after = len(list(databank_dir(a.project, a.databank, MASTER).glob("*.sqx")))
    landed = len(list(databank_dir(a.project, a.into, MASTER).glob("*.sqx")))
    print(f"{a.databank}: {before} → {after}   {a.into}: {landed}")
    if before - after != len(names):
        sys.exit(f"expected {len(names)} to leave, {before - after} did. The backup is at "
                 f"{saved}; restore from there before running anything else.")

    manifest.write(saved,
                   {"project": a.project, "databank": a.databank, "into": a.into,
                    "verdict": a.verdict, "day": day},
                   f"apply_verdict.py --project {a.project} --databank {a.databank} "
                   f"--into {a.into} --apply",
                   {"judged": len(calls), "kept": keep, "moved": len(names)})


if __name__ == "__main__":
    main()
