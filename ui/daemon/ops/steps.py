"""«En marcha» in the workflow's order: SQX tasks and Python steps in one list, WFC counted by mother."""

from typing import Any
import csv
import time
from typing import cast

from core.researchpaths import autopilot_runs
from sqx.projects import stage
from sqx import jobs, progress, tasklog
from ui.daemon.workflow import api as workflow, derive
from sqx.workflow.steps import STEPS

# The step each SQX stage belongs to (the workflow's number, 16.5 for the WFC legs).
STAGE_STEP = {
    "build": 6,
    "oos": 7,
    "crossmarket": 9,
    "crosstf": 11,
    "mcretest": 13,
    "spp": 15,
    "wfc": 16.5,
    "wfm": 19,
}
STALE_S = 6 * 3600  # an estado.txt older than this is a run that died without saying so
STATE_OF = {"empezó": "running", "hecho": "done", "falló": "failed"}
STATE = {
    "done": "done",
    "sealed": "done",
    "running": "running",
    "pending": "pending",
    "blocked": "pending",
    "missing": "pending",
}


def ranks() -> dict[str, float]:
    """Task title → the workflow step it belongs to."""
    return {t: n for s, n in STAGE_STEP.items() for t in stage.titles(s)}


def step_of(title: str, known: dict[str, float]) -> float | None:
    """The step of a task title, a longer title («CrossTF H1») taking its stage's («CrossTF»).

    Returns:
        The number, or None for a task no stage names.
    """
    if title in known:
        return known[title]
    return next((n for t, n in known.items() if title.startswith(t + " ")), None)


def mothers(runs: list[dict], title: str, of: int | None) -> dict | None:
    """Which mother a WFC leg is on, counted from SQX's own starts.

    The variants factory loads one mother's variants, starts the three legs, clears, and loads
    the next: one start of each leg per mother (🤔 the log carries no mother name). So the
    mothers a leg has been through are its starts in the unbroken tail of WFC starts; a
    re-run of the same mother counts again, which the tooltip says.

    Args:
        runs: `tasklog.task_runs`, oldest first.
        title: A WFC leg's title.
        of: How many mothers there are (SPP OOS on disk), or None.

    Returns:
        `{"n", "of"}`, `of` None when unknown or smaller than `n`.
    """
    legs = set(stage.titles("wfc"))
    n = 0
    for r in reversed(runs):
        if r["title"] not in legs:
            break
        n += r["title"] == title
    return {"n": n, "of": of if of and of >= n else None} if n else None


def autopilot_marks(project: str, now: float | None = None) -> dict[str, str]:
    """Each step's last word in the newest autopilot run's `pasos.csv`: running, done or failed.

    A step that only started counts as running while the run's `estado.txt` is fresh; a run
    that died without a word leaves it «pending» again rather than running forever.
    """
    runs = sorted((autopilot_runs() / project).glob("*/pasos.csv"))
    if not runs:
        return {}
    last = {}
    for n, word, _ in csv.reader(runs[-1].read_text(encoding="utf-8").splitlines()):
        for part in n.split("+"):
            last[part] = word
    alive = (now or time.time()) - runs[-1].with_name(
        "estado.txt"
    ).stat().st_mtime < STALE_S
    return {n: STATE_OF[w] for n, w in last.items() if w != "empezó" or alive}


def python_rows(project: str) -> list[dict]:
    """Every Python step of the workflow with its state: pendiente, en curso, hecho or falló.

    State is the rail's (`derive`: the results on disk, or a window job still running), then
    the newest autopilot run's `pasos.csv` for a step it is on or failed in, then a window
    job of the step that ended with an error. Files and the daemon's job list only.
    """
    ctx = workflow.context(project)
    marks = autopilot_marks(project)
    failed = {
        j.get("step")
        for j in jobs.listing()
        if j.get("project") == project and j["rc"] not in (None, 0, jobs.CANCELLED)
    }
    rows = []
    for spec in (s for s in STEPS if s["kind"] == "python"):
        row = derive.HOW[spec["how"]](spec, ctx)
        status = STATE[row["state"]]
        if status != "done":
            status = marks.get(spec["n"]) or (
                "failed" if spec["n"] in failed else status
            )
        rows.append(
            {
                "kind": "python",
                "step": float(cast(str, spec["n"])),
                "n": spec["n"],
                "title": f"Paso {spec['n']} · {spec['title']}",
                "status": status,
                "why": row["why"],
            }
        )
    return rows


def order(
    tasks: list[dict], python: list[dict], runs: list[dict], of: int | None
) -> list[dict]:
    """SQX tasks and Python steps in the workflow's order.

    A task no stage names keeps its place after the task before it in the project's file.
    The WFC leg that runs gets `mother` (the legs also run in steps 23 and 24, so a finished
    leg's count would mix them in).

    Args:
        tasks: `progress.state`'s rows.
        python: `python_rows`.
        runs: `tasklog.task_runs`.
        of: Mothers there are.

    Returns:
        One list, each row with `kind` («sqx» or «python») and `step`; stable inside a step.
    """
    known, wfc, last = ranks(), set(stage.titles("wfc")), 0.0
    rows = []
    for t in tasks:
        last = step_of(t["title"], known) or last
        rows.append(
            {
                **t,
                "kind": "sqx",
                "step": last,
                **(
                    {"mother": mothers(runs, t["title"], of)}
                    if t["title"] in wfc and t["status"] == "running"
                    else {}
                ),
            }
        )
    return sorted(rows + python, key=lambda r: r["step"])


def state(role: str, project: str) -> dict[str, Any]:
    """`progress.state` plus `rows`: what the zone paints."""
    got = progress.state(role, project)
    folder = progress.installs()[role] / "user" / "projects" / project
    return got | {
        "rows": order(
            got["tasks"],
            python_rows(project),
            tasklog.task_runs(folder),
            got["banks"].get("SPP OOS"),
        )
    }
