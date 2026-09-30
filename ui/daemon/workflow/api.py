"""The workflow rail's routes: every step of one project with its tests and tab, and its run buttons."""

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon import jobs
from ui.daemon.launch import chainplan
from ui.daemon.runner import where
from ui.daemon.workflow import derive, ledgerview, needs, run, sources, tests
from ui.daemon.workflow.steps import STEPS

ROUTER = APIRouter()
# The databank panel's top tabs, in the order the rail meets them (encargo 22 §4.3).
TABS = list(dict.fromkeys(s["tab"] for s in STEPS if s["tab"]))


class RailRun(BaseModel):
    """One press of a run button: the ticked tests, and the panel's databank and strategies."""

    project: str
    tests: list[dict]
    databank: str = ""
    strategies: list[str] = []


class Backfill(BaseModel):
    """The press of «rehacer las filas de 17-19»."""

    project: str


def context(project: str) -> dict:
    """Everything the steps read, gathered once per request.

    Args:
        project: Project name.

    Returns:
        `project`, `asset`, `template`, `family` (the registry's, or None), `sqx` (the
        install's files, or None), the ledger's `blind` door — asked of the one study
        blindJoint signs, never the union of the project's studies — and `oos2` budget.
    """
    ids = ledgerview.studies_of(project)
    rows = ledgerview.frame(ids)
    asset = ledgerview.symbol(rows, project)
    found = sources.install(project)
    return {"project": project, "asset": asset, "template": sources.template(project, ids),
            "family": where.family(project),
            "sqx": sources.sqx_view(*found, project) if found else None,
            "blind": ledgerview.door(project),
            "oos2": ledgerview.oos2(rows, asset)}


def workflow(project: str) -> dict:
    """The whole rail for one project.

    Args:
        project: Project name.

    Returns:
        `steps` in WORKFLOW.md order — each with its `tab`, `sub`, `stage`, `tests`,
        `panel` (its tests read the databank the panel shows) and `needs` (the steps it
        needs done first, `needs.of`) —
        `tabs`, `oos2`, `blind`, `backfill`, the offer to rebuild the rows of 17-19, and
        `chain`: what «Correr workflow» would run now and where it would stop.
    """
    ctx = context(project)
    live = tests.running(project)
    out, raw = [], []
    for spec in STEPS:
        row = derive.HOW[spec["how"]](spec, ctx)
        if spec["how"] == "sqx" and spec["studies"] and row["state"] == "done":
            reading = derive.study(spec, ctx)
            if reading["state"] == "done":
                row |= {"in": reading["in"], "out": reading["out"],
                        "why": f"{row['why']} Análisis: {reading['why']}"}
        raw.append({"n": spec["n"], "state": row["state"]})
        row = derive.seal(spec, row, ctx)
        out.append({"n": spec["n"], "title": spec["title"], "kind": spec["kind"],
                    "studies": spec["studies"], "tab": spec["tab"], "sub": spec["sub"],
                    "stage": spec.get("stage"), "panel": spec["feeds"] == (),
                    "needs": needs.of(spec, ctx), "tests": tests.of_step(spec, ctx, live),
                    **row})
    return {"project": project, "asset": ctx["asset"], "family": ctx["family"],
            "steps": out, "tabs": TABS, "oos2": ctx["oos2"], "blind": ctx["blind"],
            "backfill": run.backfill(ctx, run.blind_on_disk(raw)),
            "chain": chainplan.plan({"steps": out})}


@ROUTER.get("/api/workflow")
def get_workflow(project: str) -> dict:
    """GET /api/workflow?project — the rail. A failure comes back as `error`, never a 500."""
    try:
        return workflow(project)
    except Exception as failed:  # noqa: BLE001 — the ui boundary: show it, do not die
        return {"error": f"No se pudo leer el workflow de {project}: {failed}"}


@ROUTER.post("/api/workflow/run")
def post_run(req: RailRun) -> dict:
    """Queue the ticked tests: `{jobs, refused}`, or `{error}` shown, never raised."""
    try:
        return run.start(context(req.project), req.tests, req.databank, req.strategies)
    except Exception as failed:  # noqa: BLE001 — the ui boundary
        return {"error": f"No se pudo lanzar: {failed}"}


@ROUTER.post("/api/workflow/backfill")
def post_backfill(req: Backfill) -> dict:
    """Queue `ledger.backfill --blind … --write` when the rail offers it: `{job}` or `{error}`."""
    try:
        offer = workflow(req.project)["backfill"]
        if not offer["offer"]:
            return {"error": offer["why"]}
        return {"job": jobs.start("backfill", offer["argv"],
                                  {"project": req.project, "databank": "", "strategy": ""})}
    except Exception as failed:  # noqa: BLE001 — the ui boundary
        return {"error": f"No se pudo rehacer las filas: {failed}"}
