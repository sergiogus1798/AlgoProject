"""The daemon's job list: analysis commands started from the window, queued, and how each one ended."""

import atexit
import os
import re
import subprocess
import sys
import threading
from datetime import datetime

import psutil

from core import fanout
from core.paths import DATA, ROOT
from ui.daemon import winddown

LOGS = DATA / "logs" / "ui"
TAIL = 25
# Python jobs share one budget of physical cores. A study that fans out over processes
# itself weighs half the machine, so two of them fill it, as before; a light one weighs 3, so
# sixteen run at once. 🔬 2026-09-27: a one-strategy study is 1-2 s, mostly Python starting,
# and 0.2-0.7 GB — sixteen stay near 11 GB, inside the owner's 20 GB for Python
# (knowhow/perf/ram-budget.md); two at a time left a 1,000-strategy batch queued for 15 min.
SLOTS = fanout.CORES
WIDE = {"crossmarket", "monkey", "gate", "mcRetest", "feedQuality", "cscv", "monteCarlo"}
LIGHT = 3
# Nothing new starts below this much free RAM unless the lane is empty. 20 GB is the owner's
# reserve for Python (knowhow/perf/ram-budget.md, 125 GB = heaps + Python 20 + OS 10-12):
# below it a new study would eat into what the custodian's JVM grows into while it runs.
FLOOR_GB = 20
PROGRESS = re.compile(r"^PROGRESS (\d+(?:\.\d+)?) ?(.*)$")
CANCELLED = -15
# Analyses run below the window and the daemon (owner, 2026-09-28: «que la UI sea ligera y
# fluida aunque haya tests corriendo»): at full load the scheduler serves those two first.
NICE = 10
READ_BYTES = 16_000        # the end of a log that holds TAIL lines and its last PROGRESS

# In memory on purpose: a job is a process this daemon owns, and a daemon that dies takes its
# children with it, so a record that outlived it would describe processes that do not exist.
JOBS: list[dict] = []
_LOCK = threading.RLock()


def _launch(job: dict) -> None:
    """Start a queued job's process, and pump the queue again the moment it exits."""
    # UTF-8 mode: on Windows a child printing to a file encodes as cp1252 and dies on the
    # first «→» or «ρ» of a Spanish report.
    lower = job["lane"] == "python" and hasattr(os, "nice")
    job["_proc"] = subprocess.Popen([sys.executable, *job["argv"]], cwd=ROOT,
                                    stdout=open(job["log"], "wb"), stderr=subprocess.STDOUT,
                                    env={**os.environ, "PYTHONUTF8": "1"},
                                    preexec_fn=(lambda: os.nice(NICE)) if lower else None)
    job["started"] = datetime.now().isoformat(timespec="seconds")
    threading.Thread(target=lambda: (job["_proc"].wait(), pump()), daemon=True).start()


def weight(job: dict) -> int:
    """How much of the core budget one job takes: a batch its workers (`runner.batch`), half
    of it when it fans out, LIGHT if not."""
    return job.get("weight") or (SLOTS // 2 if job["study"] in WIDE else LIGHT)


def pump() -> None:
    """Start queued jobs, oldest first per lane: python while the core budget and the free
    RAM allow, conductor one at a time — `sqx-worker.sh` refuses a second `sqcli` on one
    install, and a job that came second would die instead of waiting."""
    with _LOCK:
        running = [j for j in JOBS if _alive(j)]
        used = sum(weight(j) for j in running if j["lane"] == "python")
        busy = any(j["lane"] == "conductor" for j in running)
        blocked = False
        for job in [j for j in JOBS if j["_proc"] is None and not j["cancelled"]]:
            if job["lane"] == "conductor":
                if not busy:
                    _launch(job)
                    busy = True
                continue
            free_gb = psutil.virtual_memory().available / 1e9
            if blocked or (any(j["lane"] == "python" for j in running)
                           and (used + weight(job) > SLOTS or free_gb < FLOOR_GB)):
                blocked = True     # python stays in the order pressed
                continue
            _launch(job)
            running.append(job)
            used += weight(job)


def start(label: str, argv: list[str], about: dict, lane: str = "python",
          weight: int | None = None) -> dict:
    """Queue one command as a child of the daemon, and start it if a slot is free.

    Args:
        label: What the window calls it, e.g. the module name.
        argv: The command, `python3 -m ...` spelled as a list so a name with spaces survives.
        about: `{project, databank, strategy}`, which the window matches jobs against, and
            optionally `study` and `scope` (`one` | `many`).
        lane: `python`, or `conductor` for a command that runs a one-shot `sqcli` there.
        weight: Cores it takes from the python budget; None for `weight`'s default.

    Returns:
        The job record, with `id`, `started` and `log` — stdout and stderr go to one file
        under the data root, tailed on demand. `started` is when it was queued until it
        starts, then when it started: the older views slice it as a time and never see None.
    """
    LOGS.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        job_id = f"{datetime.now():%Y%m%d-%H%M%S}-{len(JOBS)}"
        log = LOGS / f"{job_id}-{label}.log"
        log.touch()
        job = {"id": job_id, "label": label, "argv": argv, "study": label,
               "scope": "one" if about.get("strategy") else "many", **about, "lane": lane,
               "log": str(log), "started": datetime.now().isoformat(timespec="seconds"), "rc": None, "cancelled": False, "_proc": None,
               **({"weight": weight} if weight else {})}
        JOBS.append(job)
        pump()
        return public(job)


def _kill(job: dict) -> None:
    """SIGKILL a job's whole tree: the studies fan out with multiprocessing, and killing only
    the parent leaves its workers computing. psutil does this on Windows as well."""
    if job["_proc"].poll() is not None:
        return
    tree = psutil.Process(job["_proc"].pid)
    for p in [*tree.children(recursive=True), tree]:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass   # a worker that finished between the listing and the kill
    job["_proc"].wait()


def _alive(job: dict) -> bool:
    """Its process runs, or a cancel is still stopping the worker it started: the lane stays busy."""
    return bool(job["_proc"]) and (job["_proc"].poll() is None
                                   or ("_down" in job and job["_down"].is_alive()))


def cancel(job_id: str) -> bool:
    """Stop a job: kill its process tree if it runs, drop it from the queue if it waits. A
    launcher that runs is wound down in a thread (`winddown.wind_down`), so its worker stops.

    Args:
        job_id: A job's `id`.

    Returns:
        False when no such job exists or it had already ended.
    """
    with _LOCK:
        job = next((j for j in JOBS if j["id"] == job_id), None)
        if job is None or job["cancelled"] or (job["_proc"] and job["_proc"].poll() is not None):
            return False
        job["cancelled"] = True
        if job["_proc"] and job["label"] in winddown.LAUNCHERS:
            job["_down"] = threading.Thread(target=winddown.wind_down, args=(job, _kill, pump))
            job["_down"].start()
        elif job["_proc"]:
            _kill(job)
    pump()
    return True


def _progress(lines: list[str]) -> tuple[int | None, str]:
    """The last `PROGRESS <0..100> <state>` line of a log, as (percent, state)."""
    for line in reversed(lines):
        found = PROGRESS.match(line)
        if found:
            return int(float(found.group(1))), found.group(2)
    return None, ""


def public(job: dict) -> dict:
    """One job as the window sees it: its record, its exit code, its progress and its log's end.

    Args:
        job: An entry of `JOBS`.

    Returns:
        The record without the process handle; `rc` is None while it runs or waits, and
        -15 once cancelled. `percent` is the last PROGRESS line's, 100 once it ended well;
        `state` that line's words, or what became of it; `queued` its place in the queue
        (1 = next), None once started.
    """
    if "_final" in job:
        return job["_final"]
    proc = job["_proc"]
    alive = _alive(job)
    job["rc"] = ((None if alive else CANCELLED) if job["cancelled"]
                 else (proc.poll() if proc else None))
    with open(job["log"], "rb") as f:
        cut = max(0, f.seek(0, 2) - READ_BYTES)
        f.seek(cut)
        lines = f.read().decode("utf-8", errors="replace").splitlines()[1 if cut else 0:]
    percent, state = _progress(lines)
    waiting = [j["id"] for j in JOBS if j["_proc"] is None and not j["cancelled"]]
    if job["cancelled"]:
        state = ("cancelando" + (": parando el worker" if winddown.started(job) else "")) if alive \
            else "cancelado"
    elif proc is None:
        state = "en cola"
    elif job["rc"] == 0:
        percent, state = 100, state or "terminado"
    elif job["rc"] is not None:
        state = f"falló, código {job['rc']}"
    left = winddown.left_up(job) if job["rc"] is not None else ""   # /proc only behind a marker
    if left:
        state += f" · ⚠ el {left} sigue arrancado: bin/sqx-worker.sh --role {left} stop"
    out = ({k: v for k, v in job.items() if not k.startswith("_")}
           | {"tail": lines[-TAIL:], "percent": percent or 0, "state": state,
              "queued": waiting.index(job["id"]) + 1 if job["id"] in waiting else None})
    if job["rc"] is not None and not alive and not left:
        job["_final"] = out     # an ended job never changes: its log is not read again
    return out


def listing() -> list[dict]:
    """Every job this daemon started or queued, oldest first.

    Returns:
        The public records.
    """
    pump()
    with _LOCK:
        return [public(j) for j in JOBS]


@atexit.register
def _reap() -> None:
    """At a normal interpreter exit only, stop every job, a launcher given its grace first.

    Closing the window sends the daemon SIGTERM, and uvicorn re-raises it with the default
    handler: atexit is skipped and this never runs (verified, exit 143). That is the intended
    behaviour for launchers: an orphaned job runs to its natural end and stops the worker it
    started; the next window sees it through its `workerguard` marker (`/api/launch/steps`).
    """
    for job in list(JOBS):
        cancel(job["id"])
    for job in list(JOBS):
        if job.get("_down"):
            job["_down"].join()
