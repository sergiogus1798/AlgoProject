"""Cancelling a launcher job: let it stop the worker it started, and stop only that worker."""

import subprocess
from collections.abc import Callable

import psutil

from core import worker
from core.paths import WORKERS
from ui.daemon import workerguard

# Jobs that stop their worker in a `finally`: a cancel sends SIGTERM (their SystemExit) and
# waits GRACE_S — `sqx-worker.sh stop` waits up to 5 min — before SIGKILL; a worker still up
# after that is stopped here, but only one the job's own `workerguard` marker names.
LAUNCHERS = ("launch", "advance", "mt5verify")
GRACE_S = 360


def started(job: dict) -> str:
    """The role whose worker THIS job started and has not seen stop (`workerguard` marker with
    its PID), '' otherwise: a worker of anyone else is never stopped nor reported here."""
    mark = workerguard.marked(job.get("role")) if job["label"] in LAUNCHERS else None
    return mark["role"] if mark and job["_proc"] and mark["pid"] == job["_proc"].pid else ""


def left_up(job: dict) -> str:
    """`started`, when an SQX process still runs out of that role's install."""
    role = started(job)
    return role if role and worker.holding(WORKERS[role]["path"]) else ""


def wind_down(job: dict, kill: Callable[[dict], None], pump: Callable[[], None]) -> None:
    """End a launcher so its `finally` stops the worker: SIGTERM, GRACE_S, then SIGKILL of
    the children it had then and of itself; a worker it started and left up is stopped here.

    Args:
        job: The job record (`jobs.JOBS`), its process running.
        kill: `jobs._kill`, the tree kill.
        pump: `jobs.pump`, called once the lane is free.
    """
    proc = job["_proc"]
    try:
        children = psutil.Process(proc.pid).children(recursive=True)
    except psutil.NoSuchProcess:
        children = []
    proc.terminate()
    try:
        proc.wait(GRACE_S)
    except subprocess.TimeoutExpired:
        kill(job)
    for p in children:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    role = left_up(job)
    if role:
        with open(job["log"], "a", encoding="utf-8") as log:
            log.write(f"el demonio para el {role}, que este trabajo arrancó y dejó arrancado\n")
        try:
            worker.stop(role, export=False)
        except subprocess.CalledProcessError:
            pass        # still up: `jobs.public` says so in the job's state
        if not worker.holding(WORKERS[role]["path"]):
            workerguard.release(role)
    pump()
