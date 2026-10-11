"""What the autopilot runs, in WORKFLOW.md's order: the window's chain without its stops at the judging steps."""

import re
import sys
from pathlib import Path

from core.assetdata import load
from core.paths import feed_quality_dir
from pipeline.autopilot import tail
from ui.daemon.launch import chainplan
from ui.daemon.launch.steps import ELSEWHERE


def scanned(asset: str, do: list[dict]) -> None:
    """Refuse a plan that runs feedQuality on a feed step 4 never scanned, before any CPU is
    spent: the study reads the scan's `summary.json`, and without it the run died at step 8,
    after the build (📓 2026-10-04 NIKKEI225, 2026-10-05 USA500). The campaign asks the same
    before it queues (`pipeline.campaign.plan`).

    Args:
        asset: The project's asset.
        do: The plan's actions.
    """
    if not any("feedQuality" in a.get("tests", []) for a in do):
        return
    feed = load(asset)["sqx_symbol"]
    if not (feed_quality_dir(feed) / "summary.json").exists():
        sys.exit(f"el feed {feed} no está escaneado y el paso 8 lo lee: corre antes "
                 f"`python3 -m studies.data.feedQuality.scan --feed {feed}`")


def reopen(data: dict, out: Path) -> dict:
    """A python study that failed halfway left partial results the rail reads as done (OPEN #111):
    when the run before `out` (the newest stamp folder beside it) ended in `FALLO en el paso N` at a python step, `N` runs again."""
    try:
        said = (max(d for d in out.parent.iterdir() if d.is_dir() and d != out) / "estado.txt").read_text(encoding="utf-8").splitlines()[-1]
    except (OSError, IndexError, ValueError):
        return data
    m = re.search(r"FALLO en el paso (\S+):", said)
    for step in data["steps"]:
        if m and step["n"] == m[1] and step["kind"] == "python":
            step["state"] = "pending"
            for t in step["tests"]:
                t["state"] = "pending"
    return data


def plan(data: dict, given: dict = tail.NOTHING) -> dict:
    """Walk the rail as `chainplan.plan` does, judging instead of stopping.

    Args:
        data: GET /api/workflow's answer (`ui.daemon.workflow.api.workflow`).
        given: The tail's inputs (`tail.inputs`): the panel databanks of 21-22, step 26's
            parameters, the steps with rules. Without them the tail stops where it needs one.

    Returns:
        `do` — [{n, title, kind, tests}] in order — `skipped` — [{n, why}], the steps that do
        not apply to this project (11.7 without phase-2 tasks) — and `stop` — {n, why}, n None
        when the rail runs out. Up to 16.5 the kinds are sqx, python, judge, neighbours (step
        13's T1 batch, right before its SQX tasks) and variants: a judging
        step (8, 10, 12, 14, 16) gets a `judge` right before the next SQX step that still
        has to run: cutting before a step already done would cut for nothing. From 17 on
        the walk is `tail.walk`'s. It stops at what a person does (1-5), anything running,
        an SQX step with no task to start, and where the tail says. A judging step left
        pending at the stop is judged there: its facts are recorded, and a cut it makes is
        what the next step will read.
    """
    do, skipped, stale, pending, owed = [], [], False, None, None

    def judged() -> list[dict]:
        """The pending judge, after the tests a failed run left its step owing."""
        left = [owed] if owed and owed["n"] == pending and owed["tests"] else []
        return left + [{"n": pending, "title": "juicio", "kind": "judge", "tests": []}]

    def halt(n: str | None, why: str) -> dict:
        """The plan, ending before step `n` with the pending judge, if any, done first."""
        if pending:
            do.extend(judged())
        return {"do": do, "skipped": skipped, "stop": {"n": n, "why": why}}

    for step in data["steps"]:
        n, state = step["n"], step["state"]
        if chainplan.HOW[n] in chainplan.BEFORE:
            if state != "done":
                return halt(n, chainplan.BEFORE[chainplan.HOW[n]])
            continue
        if n == tail.FIRST:
            return tail.walk(data["steps"], do, stale, pending, data.get("family"), given)
        if state == "running":
            return halt(n, "está en marcha")
        if step["kind"] == "python":
            keys = chainplan.tests(step, stale) if stale or state != "done" else []
            if keys:
                do.append({"n": n, "title": step["title"], "kind": "python", "tests": keys})
            else:   # done by its evidence, yet a run that failed halfway never ran these
                owed = {"n": n, "title": step["title"], "kind": "python",
                        "tests": chainplan.tests(step, False)}
            pending = n if n in chainplan.JUDGES else pending
            continue
        if n == chainplan.PHASE2 and not step.get("titles"):
            # An older project has no phase-2 tasks: 11.7 is skipped. The 11.5 judge, when 11.5
            # runs in this plan, goes now where the SQX step would have flushed it, or the 12
            # would take its place; a 11.5 left done is not judged again.
            skipped.append({"n": n, "why": "el proyecto no lleva tareas de fase 2: se salta"})
            if pending and any(a["n"] == pending for a in do):
                do.append({"n": pending, "title": "juicio", "kind": "judge", "tests": []})
                pending = None
            continue
        if state == "done" and not stale:
            pending = None
            continue
        if n in chainplan.FILLED_BY_NEXT:
            continue
        if n == "16.5":       # the variant factory runs here, unattended (pipeline.autopilot.variants)
            if any(s["n"] == "19" and s["state"] == "missing" for s in data["steps"]):
                # trimmed to spp: the batch would feed steps this project does not carry
                return halt(n, "el proyecto no lleva sus tareas: acaba aquí")
            if pending:
                do.extend(judged())
                pending = None
            do.append({"n": n, "title": step["title"], "kind": "variants", "tests": []})
            stale = True
            continue
        if n in ELSEWHERE:
            return halt(n, ELSEWHERE[n])
        if not step.get("stage") and n != chainplan.PHASE2:
            return halt(n, "no tiene tareas de SQX que el autopiloto sepa lanzar")
        if state == "missing":      # a project trimmed to an earlier step (`workflow.trim`)
            return halt(n, "el proyecto no lleva sus tareas: acaba aquí")
        if pending:
            do.extend(judged())
            pending = None
        if n == "13":     # T1 first, on who step 12's cut left: its batch is measured before the
            # MC Retest's ingest is dated, and a run that fails in it leaves the 13 to do again
            do.append({"n": n, "title": "vecinas (T1)", "kind": "neighbours", "tests": []})
        do.append({"n": n, "title": step["title"], "kind": "sqx", "tests": []})
        stale = True
    return halt(None, "no queda ningún paso")
