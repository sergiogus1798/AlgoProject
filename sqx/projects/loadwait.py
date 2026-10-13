"""The signal that `-databank action=load` has finished: SQX's own «Strategies loaded» log line."""

import time

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
            raise SystemExit(f"SQX no registró «Strategies loaded» en {seconds} s tras el load de {what}")
        time.sleep(poll)
