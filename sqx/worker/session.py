"""One worker session of a launcher: rule 5, wait for SQX to be ready, follow a run to «Project finished», the build's time cap."""

import os
import re
import sys
import time
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

from core import proc, worker
from sqx import log as sqxlog
from sqx import progress
from sqx.projects import taskcap
from sqx.worker import preflight

POLL, READY_TRIES = (
    3,
    200,
)  # s between two `action=status`; × POLL, the CLI's «not ready» ~20 s
START_WITHIN = (
    120  # s after `action=start` for «Starting project '<P>'» to reach the log
)


def say(pct: int, line: str) -> None:
    """One PROGRESS line, the only thing the job list reads from here."""
    print(f"PROGRESS {pct} {line}", flush=True)


def assets(symbol: str) -> None:
    """Hard rule 5: `python3 -m core.assets <SYMBOL>` before touching a project; stop on non-zero."""
    got = proc.run(
        [sys.executable, "-m", "core.assets", symbol],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    print(got.stdout.strip(), flush=True)
    if got.returncode:
        sys.exit(
            f"core.assets {symbol} salió con {got.returncode}: no se lanza nada\n"
            f"{got.stderr.strip()}"
        )


def graceful(_signum: int, _frame: object) -> None:
    """SIGTERM from the daemon's cancel: raise, so every `finally` stops the worker it started —
    without the export after the stop, which could outlast the daemon's grace period."""
    os.environ["ALGO_NO_EXPORT"] = "1"
    raise SystemExit("cancelado desde la ventana: se para el worker antes de salir")


STOP = re.compile(r'<StopCondition\b[^>]*hours="(\d+)"[^>]*minutes="(\d+)"')


def minutes(cfx: Path) -> int:
    """The time cap the builder wrote into the Build task's StopCondition, 0 when none.

    Owner, 2026-10-01: a build stops on N strategies or M minutes, whichever comes first
    (`databank.caps` in assets/_build.yaml). Under `databank-full` SQX ignores `minutes=`.
    """
    with zipfile.ZipFile(cfx) as z:
        for name in (n for n in z.namelist() if n.startswith("Build-")):
            got = STOP.search(z.read(name).decode("utf-8", "replace"))
            if got:
                return int(got.group(1)) * 60 + int(got.group(2))
    return 0


def enforce(project: str, role: str, now: dict[str, Any] | None, top: Path) -> bool:
    """Stop the project once its running build has used its minutes.

    Args:
        project: The project running.
        role: Its worker.
        now: The running task's row of `progress.state`, or None.
        top: The worker's install folder; the cap is read from the project's own file.

    Returns:
        True when it sent the stop. A stopped project does not go on to its next active task
        (🔬 2026-10-01): the caller runs what is left (`pipeline.autopilot.run`).
    """
    if not (now and now["type"] == "Build"):
        return False
    cap = minutes(top / "user" / "projects" / project / "project.cfx")
    if not cap or (now["elapsed_s"] or 0) < cap * 60:
        return False
    worker.call(f"-project action=stop name={project}", role)
    print(f"{now['title']}: {cap} min cumplidos, se para el build", flush=True)
    return True


SYNCING, SYNCED = b"Syncing databank(s) from files", b"Synchronization finished"


def syncing(top: Path) -> bool:
    """Whether SQX is still loading the databanks from their files: the last «Syncing
    databank(s) from files» of today's log has no «Synchronization finished» after it."""
    f = sqxlog.path(top, date.today())
    if not f.exists():
        return False
    with f.open("rb") as fh:
        fh.seek(max(0, f.stat().st_size - 4_000_000))
        tail = fh.read()
    return tail.rfind(SYNCING) > tail.rfind(SYNCED)


def ready(project: str, role: str) -> None:
    """Wait until the CLI answers, asking only `action=status`, and has its databanks loaded.

    The first `-project` command after a start makes SQX load every databank from its files.
    When another caller's status poll (the window's pulse) was that first command, this one
    is answered at once while the load goes on, and a task started then reads an empty input:
    🔬 2026-09-29, «WFM : No strategies to retest» at 11:52:35, «Loaded 21 strategies to
    databank SPP OOS» at 11:52:47.
    """
    top = preflight.WORKERS[role]["path"]
    for _ in range(READY_TRIES):
        try:
            answer = worker.call(f"-project action=status name={project}", role)
        except (
            OSError
        ):  # port not open yet: step 26 died on a refused connection 2026-10-16
            answer = "not ready"
        if "not ready" not in answer and not syncing(top):
            return
        time.sleep(POLL)
    sys.exit(f"el {role} no respondió tras {READY_TRIES * POLL} s")


def watch(project: str, role: str, offsets: dict[Path, int]) -> dict[str, Any]:
    """Follow the run until SQX logs «Project finished», bounded at both ends.

    Args:
        project: The project started.
        role: Its worker.
        offsets: `sqxlog.mark` taken just before `action=start`: only what the log gained
            since counts, so an earlier run's finish — today's or yesterday's — is never this one's.

    Returns:
        The last `run` read. Each poll sends `-project action=status` (`progress.state`), and
        `stop` once a build passes its minutes (`buildcap`); the log is read across midnight.
        SystemExit when the start never reaches the log within START_WITHIN, when the worker
        dies, on an abort line or a task past its deadline (`sqxlog.police`), or past worker.MAX_HOURS.
    """
    top, kept, began, cap = (
        preflight.WORKERS[role]["path"],
        [],
        time.monotonic(),
        taskcap.fresh(),
    )
    seen = stopped = (
        False  # once the start was read, losing it is never «did not start»
    )
    while True:
        time.sleep(POLL)
        if not worker.holding(top):
            sys.exit(f"el {role} se paró antes de «Project finished»")
        try:
            got = progress.state(role, project)
            live = got.get("status")
            now = next((t for t in got["tasks"] if t["status"] == "running"), None)
        except (OSError, ValueError, AttributeError, KeyError) as failed:
            # The status is only what the progress line shows. A log SQX is still writing must
            # never end the run: this loop's `finally` stops the worker (2026-09-28, a build).
            print(f"estado no legible ahora ({failed}); se sigue esperando", flush=True)
            live = now = None
        run = progress.run_state(sqxlog.grow(top, offsets, kept, fresh := []))
        sqxlog.police(cap, fresh, project, role, top, stopped)
        waited = time.monotonic() - began
        seen = seen or run["project"] == project
        if (
            waited > worker.MAX_HOURS * 3600
        ):  # before the `continue`: another project's start waited for ever
            sys.exit(
                f"{project} sigue sin «Project finished» tras {worker.MAX_HOURS} h: se para el "
                "worker para liberar el carril"
            )
        if run["project"] != project:
            if not seen and waited > START_WITHIN:
                sys.exit(
                    f"SQX no escribió «Starting project '{project}'» en {START_WITHIN} s "
                    "tras `action=start`: no arrancó; se para el worker"
                )
            continue
        if run["finished"]:
            return run
        stopped = stopped or enforce(project, role, now, top)
        # A retest's log carries no compute-thread figure: its share is done over its input
        # (📓 2026-09-29, «MCR 1 Bar 0 % · 122 probadas» with 122 of 200 done).
        percent = run["percent"]
        if percent is None and now and now["done"] is not None and now["total"]:
            percent = min(100, 100 * now["done"] // now["total"])
        of = f" de {now['total']}" if now and now["total"] else ""
        say(
            60 + (percent or 0) * 35 // 100,
            f"{run['current'] or 'esperando'}"  # a build: no %
            + (f" {percent} %" if percent is not None else "")
            + (
                f" · {live['generated']}{of} "
                f"probadas · {live.get('in_databank', '?')} en el databank"
                if live
                else ""
            ),
        )
