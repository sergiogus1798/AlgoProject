"""Whether a worker is up, and the marker a launcher job leaves while the worker it started runs."""

import json
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

from core import worker
from core.paths import DATA

# One file per role, written by the job right after `worker.start` returned and removed once
# its `stop` left nothing running: the proof that THIS job started that worker. The daemon
# stops or warns about a worker only when the marker names one of its own jobs' processes.
MARKS = DATA / "logs" / "ui" / "workers"
# The seconds a log may be written after a job released its worker and still be that job's
# (the file's mtime against the clock, and the last flush of a stopping JVM).
RELEASE_SLACK_S = 60


def up(top: Path, port: int) -> str:
    """Whether a worker is up: an SQX process out of its install, or its port answering.

    Returns:
        The sign seen, '' when it is down. Read-only: /proc and a socket probe.
    """
    pids = worker.holding(top)
    if pids:
        return f"proceso(s) de SQX vivos en {top.name} (PID {', '.join(map(str, pids))})"
    with socket.socket() as probe:
        probe.settimeout(0.5)
        return f"el puerto {port} responde" if probe.connect_ex(("127.0.0.1", port)) == 0 else ""


def refuse_if_up(role: str, top: Path, port: int) -> None:
    """Right before a start: `sqx-worker.sh start` answers 0 on «already running», and the
    job would then take someone's worker over and stop it. Exits without touching it."""
    seen = up(top, port)
    if seen:
        sys.exit(f"el {role} ya estaba arrancado ({seen}): no se toca ni se para")


def mark(role: str, project: str) -> None:
    """Record that this process started the role's worker (call right after `worker.start`)."""
    MARKS.mkdir(parents=True, exist_ok=True)
    (MARKS / f"{role}.json").write_text(json.dumps(
        {"role": role, "project": project, "pid": os.getpid(),
         "since": datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")


def marked(role: str | None) -> dict | None:
    """The role's marker, or None."""
    f = MARKS / f"{role}.json"
    return json.loads(f.read_text(encoding="utf-8")) if role and f.exists() else None


def stopped(role: str, top: Path, port: int) -> str:
    """After `worker.stop` (which answers 0 even on «STILL RUNNING after 5 min»): the marker
    goes when nothing is left, else it stays and a line is printed.

    Returns:
        What is still up, '' when the worker stopped.
    """
    left = up(top, port)
    if left:
        print(f"⚠️ el {role} sigue arrancado tras `stop` ({left}): páralo con "
              f"bin/sqx-worker.sh --role {role} stop", flush=True)
    else:
        release(role)
        print(f"el {role} está parado", flush=True)
    return left


def release(role: str) -> None:
    """The worker this job started is down: drop its marker and say when it was let go.

    `<role>.released.json` is what lets the next launch tell the window's own last write to
    the install's log from anyone else's (owner, 2026-09-29: the 15-min quiet guard waited
    on the window's own runs). Written after the stop and its export, so every line this job
    caused is older than `at`.
    """
    MARKS.mkdir(parents=True, exist_ok=True)
    mark = marked(role) or {}
    (MARKS / f"{role}.released.json").write_text(json.dumps(
        {"role": role, "project": mark.get("project"), "pid": mark.get("pid", os.getpid()),
         "at": time.time()}), encoding="utf-8")
    (MARKS / f"{role}.json").unlink(missing_ok=True)


def own_last_write(role: str, log_mtime: float) -> bool:
    """Whether the install's log was last written by a window job that has released it.

    Args:
        role: A worker role.
        log_mtime: The modification time of the install's SQX log of today.

    Returns:
        True when a job released this worker at or after that write (`RELEASE_SLACK_S`
        of slack): nothing has touched the log since, so its recency is no sign of another
        session. Anything written later — a skill, an agent, a GUI — makes it False.
    """
    f = MARKS / f"{role}.released.json"
    if not f.exists():
        return False
    try:
        at = json.loads(f.read_text(encoding="utf-8"))["at"]
    except (ValueError, KeyError):
        return False
    return log_mtime <= at + RELEASE_SLACK_S


def orphans(own: set[int]) -> list[dict]:
    """Markers no job of this daemon owns — left by a window that closed: its job still
    running on its own, or dead with the worker it started maybe still up. Said, never acted on.

    Args:
        own: The PIDs of this daemon's jobs.

    Returns:
        {text, alive} per marker: `alive` while its job still runs.
    """
    out = []
    for f in sorted(MARKS.glob("*.json")) if MARKS.is_dir() else []:
        if f.name.endswith(".released.json"):
            continue
        m = json.loads(f.read_text(encoding="utf-8"))
        if m["pid"] in own:
            continue
        alive = psutil.pid_exists(m["pid"])
        out.append({"alive": alive, "text": (
            f"un lanzamiento de {m['project']} (PID {m['pid']}, desde {m['since']}) "
            + (f"sigue corriendo con el {m['role']} arrancado" if alive else
               f"terminó sin parar el {m['role']}: si sigue arrancado, "
               f"bin/sqx-worker.sh --role {m['role']} stop"))})
    return out
