"""GET /api/jobs shared by every poller of the window: the answer one of them just got serves the rest."""

import time
from collections.abc import Callable

from PySide6.QtCore import QObject

from ui.desktop import background

TTL_S = 2.0      # the status bar reads the list every 2 s; a younger answer is not asked for again
_LAST: dict = {"at": 0.0, "got": {}}


def store(got: dict, at: float) -> None:
    """Remember an answer of `jobs` (the status bar's poll feeds it); an older one is ignored.

    Args:
        got: The answer.
        at: `time.monotonic()` taken BEFORE the GET was sent.
    """
    if "error" not in got and at >= _LAST["at"]:
        _LAST.update(at=at, got=got)


def read(done: Callable[[dict], None], key: str = "", owner: QObject | None = None,
         ttl: float = TTL_S) -> None:
    """Give `done` the job list: the last answer when younger than `ttl`, else a fresh GET.

    Args:
        done: Receives `{"jobs": [...]}`, or `{"error": sentence}`; called at once when cached.
        key: As `background.run`.
        owner: As `background.run`.
        ttl: Seconds a remembered answer stays good; 0 forces the GET (a press that just queued
            a job must see it).
    """
    if time.monotonic() - _LAST["at"] < ttl:
        return done(_LAST["got"])
    at = time.monotonic()
    background.get("jobs", lambda got: (store(got, at), done(got)), key, owner)
