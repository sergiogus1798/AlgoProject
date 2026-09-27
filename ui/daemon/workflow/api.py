"""The workflow rail's route: every step of one project, its state, its funnel and why."""

from fastapi import APIRouter

from ui.daemon.workflow import derive, ledgerview, sources
from ui.daemon.workflow.steps import STEPS

ROUTER = APIRouter()


def context(project: str) -> dict:
    """Everything the steps read, gathered once per request.

    Args:
        project: Project name.

    Returns:
        `project`, `asset`, `template`, `sqx` (the install's files, or None), and the
        ledger's `blind` door and `oos2` budget.
    """
    ids = ledgerview.studies_of(project)
    rows = ledgerview.frame(ids)
    asset = ledgerview.symbol(rows, project)
    where = sources.install(project)
    return {"project": project, "asset": asset, "template": sources.template(project, ids),
            "sqx": sources.sqx_view(*where, project) if where else None,
            "blind": ledgerview.blind(rows), "oos2": ledgerview.oos2(rows, asset)}


def workflow(project: str) -> dict:
    """The whole rail for one project.

    Args:
        project: Project name.

    Returns:
        `steps` in WORKFLOW.md order, `oos2` and `blind`, as SPEC §2 states them.
    """
    ctx = context(project)
    out = []
    for spec in STEPS:
        row = derive.HOW[spec["how"]](spec, ctx)
        if spec["how"] == "sqx" and spec["studies"] and row["state"] == "done":
            reading = derive.study(spec, ctx)
            if reading["state"] == "done":
                row |= {"in": reading["in"], "out": reading["out"],
                        "why": f"{row['why']} Análisis: {reading['why']}"}
        row = derive.seal(spec, row, ctx)
        out.append({"n": spec["n"], "title": spec["title"], "kind": spec["kind"],
                    "studies": spec["studies"], **row})
    return {"project": project, "asset": ctx["asset"], "steps": out, "oos2": ctx["oos2"],
            "blind": ctx["blind"]}


@ROUTER.get("/api/workflow")
def get_workflow(project: str) -> dict:
    """GET /api/workflow?project — the rail. A failure comes back as `error`, never a 500."""
    try:
        return workflow(project)
    except Exception as failed:  # noqa: BLE001 — the ui boundary: show it, do not die
        return {"error": f"No se pudo leer el workflow de {project}: {failed}"}
