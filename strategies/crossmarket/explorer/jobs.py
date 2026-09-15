"""One job at a time, off the request thread, publishing step-by-step progress."""

import threading
import traceback
from collections.abc import Callable
from datetime import datetime

LOCK = threading.Lock()
STATE = {"running": False, "what": "", "stage": "", "share": 0.0, "step": 0, "steps": 0,
         "error": "", "result": None, "finished": ""}


def step(stage: str, share: float) -> None:
    """Move the progress bar to a fraction of the whole job.

    Args:
        stage: What is running right now, shown on the progress line.
        share: How much of the job is done, 0 to 1.

    Returns:
        Nothing. The analysis reports a continuous share rather than counting steps: one
        market under one null model is drawn in batches, so the bar advances several times
        inside every model rather than jumping once per market.
    """
    STATE["stage"] = stage
    STATE["share"] = min(max(share, 0.0), 1.0)


def _run(work: Callable[[], object], what: str) -> None:
    """Run one job to the end and publish what it left behind.

    Args:
        work: A no-argument callable returning whatever the caller wants back.
        what: What to call this job on screen.

    Returns:
        Nothing. A traceback is stored rather than printed: the panel has to be able to say
        what broke, and a server log nobody opens is not saying it.
    """
    try:
        STATE["result"] = work()
    except Exception:                                    # noqa: BLE001 - shown to the user
        STATE["error"] = traceback.format_exc(limit=6)
    finally:
        STATE["running"] = False
        STATE["share"] = 1.0
        STATE["stage"] = f"{what} — terminado"
        STATE["finished"] = datetime.now().isoformat(timespec="seconds")


def start(work: Callable[[], object], what: str, steps: int) -> bool:
    """Begin a job, unless one is already running.

    Args:
        work: A no-argument callable doing the analysis.
        what: What to call it on screen.
        steps: Only for the counter beside the bar; the bar itself is driven by step().

    Returns:
        False when another job holds the machine, in which case nothing was started. Only
        one job runs at a time: two would fight over the same session record.
    """
    with LOCK:
        if STATE["running"]:
            return False
        STATE.update({"running": True, "what": what, "stage": what, "share": 0.0,
                      "step": 0, "steps": steps, "error": "", "result": None, "finished": ""})
    threading.Thread(target=_run, args=(work, what), daemon=True).start()
    return True


def status() -> dict:
    """What the panel polls while a job runs.

    Returns:
        Everything but the result itself, which can be sizeable and is fetched once, when
        the job is done.
    """
    return {k: v for k, v in STATE.items() if k != "result"}


def take() -> object:
    """The finished job's result, once.

    Returns:
        What the job returned, or None. It is left in place: the server decides whether to
        cache it, and a second reader of the same finished job gets the same object.
    """
    return STATE["result"]
