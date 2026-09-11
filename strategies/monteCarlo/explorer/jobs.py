"""One analysis at a time, run off the request thread, with the progress the terminal shows."""

import threading
import traceback
from collections.abc import Callable
from datetime import datetime

from strategies.monteCarlo import engine

LOCK = threading.Lock()
STATE = {"running": False, "what": "", "stage": "", "title": "", "share": 0.0,
         "done": 0, "total": 0, "step": 0, "steps": 0, "error": "", "result": None,
         "finished": ""}
LATE = "Familias D y E — cientos de ventanas y terciles cortos, sin barra"


def _report(done: int, total: int, title: str) -> None:
    """What engine.PROGRESS calls on every batch of simulations.

    Args:
        done: Simulations finished in the current sub-test.
        total: Simulations that sub-test asked for.
        title: The sub-test's name.

    Returns:
        Nothing. A new title means a sub-test started, which is the only place the step
        counter moves: the engine does not know how many sub-tests a job has.
    """
    if title != STATE["title"]:
        STATE["title"] = title
        STATE["step"] = min(STATE["step"] + 1, STATE["steps"] or STATE["step"] + 1)
    STATE["done"], STATE["total"] = done, total
    fraction = done / total if total else 0.0
    if STATE["steps"]:
        STATE["share"] = min((STATE["step"] - 1 + fraction) / STATE["steps"], 1.0)
        STATE["stage"] = LATE if STATE["share"] >= 1.0 else STATE["title"]
    else:
        STATE["share"], STATE["stage"] = fraction, title


def _run(work: Callable[[], object], what: str) -> None:
    """Run one job to the end and publish what it left behind.

    Args:
        work: A no-argument callable returning whatever the caller wants back.
        what: What to call this job on screen.

    Returns:
        Nothing. A traceback is stored rather than printed: the panel has to be able to say
        what broke, and a server log nobody opens is not saying it.
    """
    engine.PROGRESS = _report
    try:
        STATE["result"] = work()
    except Exception:                                    # noqa: BLE001 - shown to the user
        STATE["error"] = traceback.format_exc(limit=6)
    finally:
        engine.PROGRESS = None
        STATE["running"] = False
        STATE["share"] = 1.0
        STATE["stage"] = f"{what} — terminado"
        STATE["finished"] = datetime.now().isoformat(timespec="seconds")


def start(work: Callable[[], object], what: str, steps: int) -> bool:
    """Begin a job, unless one is already running.

    Args:
        work: A no-argument callable doing the analysis.
        what: What to call it on screen.
        steps: How many simulated sub-tests it will run, for the progress bar. Zero when
            the job is a single sub-test and the bar is that sub-test's own.

    Returns:
        False when another job holds the machine, in which case nothing was started. Only
        one job runs at a time on purpose: two would fight over every core and neither
        progress bar would mean anything.
    """
    with LOCK:
        if STATE["running"]:
            return False
        STATE.update({"running": True, "what": what, "stage": what, "title": "",
                      "share": 0.0, "done": 0, "total": 0, "step": 0, "steps": steps,
                      "error": "", "result": None, "finished": ""})
    threading.Thread(target=_run, args=(work, what), daemon=True).start()
    return True


def status() -> dict:
    """What the panel polls while a job runs.

    Args:
        None.

    Returns:
        Everything but the result itself, which can be megabytes and is fetched once, when
        the job is done.
    """
    return {k: v for k, v in STATE.items() if k != "result"}


def take() -> object:
    """The finished job's result, once.

    Args:
        None.

    Returns:
        What the job returned, or None. It is left in place: the server decides whether to
        cache it, and a second reader of the same finished job gets the same object.
    """
    return STATE["result"]
