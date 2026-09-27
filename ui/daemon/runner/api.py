"""The run routes of the study viewer: start a study on one strategy or the population, its sub-tests, cancel."""

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon import jobs
from ui.daemon.runner import table

ROUTER = APIRouter()


class StudyRun(BaseModel):
    """One press of ▶, ▶▶ or ↻: which study, over what, with which overrides."""

    study: str
    scope: str = "one"
    project: str
    databank: str
    strategies: list[str] = []
    asset: str = ""
    overrides: list[str] = []
    only: str | None = None


@ROUTER.post("/api/study/run")
def study_run(req: StudyRun) -> dict[str, object]:
    """Queue a study: one job per strategy for `one`, one job for `many`.

    Args:
        req: The request; `overrides` go to the command as `--set`.

    Returns:
        `{"jobs": [job, ...]}`, or `{"error": sentence}` when it cannot start — a missing
        input, a scope the study has not, a study the window never runs (SQX, a skill, the
        ledger's family). A bad input from the window is shown, never raised.
    """
    if req.scope not in ("one", "many"):
        return {"error": f"alcance desconocido: {req.scope}"}
    try:
        planned = table.jobs(req.model_dump())
    except (FileNotFoundError, KeyError, ValueError) as e:
        return {"error": f"no se pudo preparar {req.study}: {e}"}
    if isinstance(planned, str):
        return {"error": planned}
    return {"jobs": [jobs.start(p["label"], p["argv"], p["about"]) for p in planned]}


@ROUTER.get("/api/study/only")
def study_only(study: str, project: str = "", databank: str = "",
               asset: str = "") -> dict[str, object]:
    """The sub-tests of a study that run alone.

    Args:
        study: A study folder name.
        project, databank, asset: Where; crossmarket's options are the markets of that export.

    Returns:
        `{"options": [{"key", "label"}]}`, empty when there are none.
    """
    try:
        return {"options": table.options(study, project, databank, asset)}
    except (FileNotFoundError, KeyError, ValueError):
        return {"options": []}


@ROUTER.post("/api/jobs/{job_id}/cancel")
def job_cancel(job_id: str) -> dict[str, object]:
    """Cancel a running or queued job.

    Args:
        job_id: The job's `id`.

    Returns:
        `{"ok": bool}` — false when no such job exists or it had already ended.
    """
    return {"ok": jobs.cancel(job_id)}
