"""What the autopilot runs, in WORKFLOW.md's order: the window's chain without its stops at the judging steps."""

from ui.daemon.launch import chainplan
from ui.daemon.launch.steps import ELSEWHERE


def plan(data: dict) -> dict:
    """Walk the rail as `chainplan.plan` does, judging instead of stopping.

    Args:
        data: GET /api/workflow's answer (`ui.daemon.workflow.api.workflow`).

    Returns:
        `do` — [{n, title, kind: sqx|python|judge, tests}] in order — and `stop` —
        {n, why}, n None when the rail runs out. A judging step (8, 10, 12, 14, 16) gets a
        `judge` right before the next SQX step that still has to run: cutting before a step
        already done would cut for nothing. It stops where the chain does — what a person
        does (1-5), 16.5, the 19 that reads oos2, anything running, and an SQX step with no
        task to start (25.5). A judging step left pending at the stop is judged there: its
        facts are recorded, and a cut it makes is what the next step will read.
    """
    do, stale, pending = [], False, None

    def halt(n: str | None, why: str) -> dict:
        """The plan, ending before step `n` with the pending judge, if any, done first."""
        if pending:
            do.append({"n": pending, "title": "juicio", "kind": "judge", "tests": []})
        return {"do": do, "stop": {"n": n, "why": why}}

    for step in data["steps"]:
        n, state = step["n"], step["state"]
        if chainplan.HOW[n] in chainplan.BEFORE:
            if state != "done":
                return halt(n, chainplan.BEFORE[chainplan.HOW[n]])
            continue
        if state == "running":
            return halt(n, "está en marcha")
        if step["kind"] == "python":
            keys = chainplan.tests(step, stale) if stale or state != "done" else []
            if keys:
                do.append({"n": n, "title": step["title"], "kind": "python", "tests": keys})
            pending = n if n in chainplan.JUDGES else pending
            continue
        if state == "done" and not stale:
            pending = None
            continue
        if n in chainplan.FILLED_BY_NEXT:
            continue
        if n in chainplan.OOS2 or n in ELSEWHERE:
            return halt(n, chainplan.OOS2.get(n) or ELSEWHERE[n])
        if not step.get("stage"):
            return halt(n, "no tiene tareas de SQX que el autopiloto sepa lanzar")
        if pending:
            do.append({"n": pending, "title": "juicio", "kind": "judge", "tests": []})
            pending = None
        do.append({"n": n, "title": step["title"], "kind": "sqx", "tests": []})
        stale = True
    return halt(None, "no queda ningún paso")
