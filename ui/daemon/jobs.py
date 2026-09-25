"""The daemon's job list: analysis commands started from the window, and how each one ended."""

import subprocess
import sys
from datetime import datetime

from core.paths import DATA, ROOT

LOGS = DATA / "logs" / "ui"
TAIL = 25

# In memory on purpose: a job is a process this daemon owns, and a daemon that dies takes its
# children with it, so a record that outlived it would describe processes that do not exist.
JOBS: list[dict] = []


def start(label: str, argv: list[str], about: dict) -> dict:
    """Start one command as a child of the daemon and record it.

    Args:
        label: What the window calls it, e.g. the module name.
        argv: The command, `python3 -m ...` spelled as a list so a name with spaces survives.
        about: `{project, databank, strategy}`, which the window matches jobs against.

    Returns:
        The job record, with `id`, `started` and `log` — stdout and stderr go to one file
        under the data root, tailed on demand.
    """
    LOGS.mkdir(parents=True, exist_ok=True)
    job_id = f"{datetime.now():%Y%m%d-%H%M%S}-{len(JOBS)}"
    log = LOGS / f"{job_id}-{label}.log"
    proc = subprocess.Popen([sys.executable, *argv], cwd=ROOT, stdout=log.open("w"),
                            stderr=subprocess.STDOUT)
    job = {"id": job_id, "label": label, "argv": argv, **about, "log": str(log),
           "started": datetime.now().isoformat(timespec="seconds"), "rc": None, "_proc": proc}
    JOBS.append(job)
    return public(job)


def public(job: dict) -> dict:
    """One job as the window sees it: its record, its exit code and the end of its log.

    Args:
        job: An entry of `JOBS`.

    Returns:
        The record without the process handle; `rc` is None while it runs.
    """
    job["rc"] = job["_proc"].poll()
    lines = open(job["log"], encoding="utf-8", errors="replace").read().splitlines()
    return {k: v for k, v in job.items() if k != "_proc"} | {"tail": lines[-TAIL:]}


def listing() -> list[dict]:
    """Every job this daemon started, oldest first.

    Returns:
        The public records.
    """
    return [public(j) for j in JOBS]
