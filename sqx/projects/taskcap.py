"""A live task's deadline: 3× the longest its title ever took in SQX's own log; past it, the abort."""

import json
import re
import time
from pathlib import Path

from core.fsio import atomic_write
from core.paths import WORKERS
from core.researchpaths import autopilot_runs
from sqx.projects import stage
from typing import Any, TypedDict

# `OOS : ================================` opens a task; `OOS : Task finished in 21.10 s.` closes it.
LINE = re.compile(r"ProgressEngine - (.+?) : (?:={8,}|Task finished in ([0-9.]+) s\.)")
TIMES, FLOOR, UNKNOWN = (
    3,
    20 * 60,
    60 * 60,
)  # s: the deadline's floor, and a title never seen


def _history() -> Path:
    """Longest seconds per task title, learnt from every «Task finished» a wait read (seeded from the logs)."""
    return autopilot_runs() / "task-durations.json"


class Cap(TypedDict):
    """What one wait tracks: the task running now, when its start line was read, and the history."""

    task: str | None
    since: float
    longest: dict[str, Any]


def _longest() -> dict:
    """The history on disk now."""
    f = _history()
    return json.loads(f.read_text()) if f.exists() else {}


def fresh() -> Cap:
    """What one wait tracks: the task running now, when its start line was read, and the history."""
    return {"task": None, "since": 0.0, "longest": _longest()}


def note(cap: Cap, line: str) -> None:
    """One log line: a start line opens the task's deadline, a finish line closes it and teaches the history."""
    m = LINE.search(line)
    if not m:
        return
    task, seconds = m.groups()
    if seconds is None:
        cap.update(task=task, since=time.monotonic())
        return
    # Two waits at once (conductor and custodian) each hold their own copy: the file is read
    # again and merged by max, or the later writer lowered the other's record and `enforce`
    # aborted a healthy long task. Whole file or nothing, for a reader in the middle.
    known = {**cap["longest"], task: max(cap["longest"].get(task, 0), float(seconds))}
    for title, longest in _longest().items():
        known[title] = max(known.get(title, 0), longest)
    cap.update(task=None, longest=known)
    atomic_write(
        _history(),
        json.dumps(known, indent=1, sort_keys=True).encode("utf-8"),
        durable=True,
    )


def enforce(cap: Cap, role: str, log: Path) -> None:
    """SystemExit — NOT worded as the transient abort — once the running task outlives its deadline.

    The build is left alone: it ends on its own time-limit (owner, 2026-10-06: a task that
    does not advance is a step failure, so the three retries apply). A hung MC Retest kept
    4 of 96 cores busy for 1 h 40 with nothing in the log (🔬 2026-10-06), so the only
    observable is the clock against the title's own history. No thread dump: `jstack` cannot
    attach to SQX's JVM and its Go launcher swallows SIGQUIT (🔬 2026-10-06) — the stuck
    threads print their stack as `Cross check exception` when `exitapp` ends them. No rerun in
    the same session: the wedged task kept its input, and `loadFilesToDatabank clear=true`
    beside it left 7 strategies for 3 files (🔬 2026-10-06) — the step fails, the session
    is killed and the campaign's tries restart SQX.
    """
    task = cap["task"]
    if not task or task in stage.titles("build"):
        return
    seen = cap["longest"].get(task)
    limit = max(FLOOR, TIMES * seen) if seen else UNKNOWN
    ran = time.monotonic() - cap["since"]
    if ran <= limit:
        return
    why = f"3× su máximo sano de {seen:.0f} s" if seen else "tarea nunca vista"
    raise SystemExit(
        f"SQX no avanza: «{task}» lleva {ran / 60:.0f} min sin «Task finished» en {role} "
        f"(tope {limit / 60:.0f} min, {why}); sus hilos salen como «Cross check exception» "
        f"en {WORKERS[role]['path'] / 'user/log/worker-daemon.log'} al cerrar ({log})"
    )
