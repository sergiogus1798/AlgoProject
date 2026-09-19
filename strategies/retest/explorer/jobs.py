"""One job at a time, off the request thread, publishing what the panel shows while it waits."""

import threading
import traceback
from collections.abc import Callable
from datetime import datetime

LOCK = threading.Lock()
STATE = {"running": False, "what": "", "error": "", "result": None, "finished": ""}


def _run(work: Callable[[], object], what: str) -> None:
    """Run one job to the end and publish what it left behind.

    Args:
        work: A no-argument callable returning whatever the caller wants back.
        what: What to show while it runs.

    Returns:
        Nothing. A traceback is published rather than swallowed: the panel is the only
        place the owner sees it, so hiding it there hides it everywhere.
    """
    try:
        STATE["result"] = work()
    except Exception:
        STATE["error"] = traceback.format_exc()
    finally:
        STATE["running"] = False
        STATE["finished"] = datetime.now().strftime("%H:%M:%S")


def start(work: Callable[[], object], what: str) -> bool:
    """Begin a job unless one is already going.

    Args:
        work: What to run.
        what: What to show while it runs.

    Returns:
        False when another job holds the slot. One at a time on purpose: two analyses
        writing into one session store is a race nobody would ever see fail cleanly.
    """
    with LOCK:
        if STATE["running"]:
            return False
        STATE.update(running=True, what=what, error="", result=None, finished="")
    threading.Thread(target=_run, args=(work, what), daemon=True).start()
    return True


def snapshot() -> dict:
    """What the panel polls for.

    Returns:
        The state without the result payload, which can be megabytes and is fetched
        separately once the job is done.
    """
    return {k: v for k, v in STATE.items() if k != "result"}
