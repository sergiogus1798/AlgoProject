"""The signals that SQX has finished something, from its own log: «Strategies loaded» after a `-databank action=load`, «APP LOADED» after a start."""

import time
from collections.abc import Callable

from sqx.projects import live


def loaded(role: str, since: tuple, seconds: float, poll: float, what: str) -> None:
    """Block until SQX's log says «Strategies loaded» past `since`; SystemExit after `seconds` s.

    `load` is asynchronous (it replies in ~8 ms) and the line follows ~0.26 s later for 50 files
    (🔬 2026-10-13, encargo 66 live session 1). The line names no databank: one load at a time.
    `since` is `live.mark(role)` taken BEFORE the `load` call (past midnight, the next day's log is read whole).
    `what` names the load in the failure."""
    end = time.monotonic() + seconds
    while True:
        if "Strategies loaded" in live.tail(role, since):
            return
        if time.monotonic() > end:
            raise SystemExit(
                f"SQX no registró «Strategies loaded» en {seconds} s tras el load de {what}"
            )
        time.sleep(poll)


def booted(role: str, launch: Callable[[], object], seconds: int = 300) -> None:
    """Take the log mark, run `launch`, then block until SQX's log says «APP LOADED» past it.

    🔬 2026-10-13 (encargo 66 live session 3): a task started before that line never stops when its databank
    fills (5/5 looped), one started >= 25 s after it always does (5/5); the port answers well before.
    After `seconds` s the session is killed by PID and SystemExit raised, so no task is started."""
    since = live.mark(role)
    launch()
    for _ in range(seconds):
        if "APP LOADED" in live.tail(role, since):
            return
        time.sleep(1)
    live.kill(role)
    raise SystemExit(
        f"{role}: SQX no escribió «APP LOADED» en {seconds} s; sesión matada por PID, no se arranca ninguna tarea"
    )
