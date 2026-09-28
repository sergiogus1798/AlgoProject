"""The run routes of the study viewer: start a study, one sub-test beside the stored result, the screen as a page, cancel."""

import json
from datetime import datetime
from html import escape
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from core.paths import DATA
from core.study.render import page
from ui.daemon import jobs, runs
from ui.daemon.results import store
from ui.daemon.runner import table, transfer

ROUTER = APIRouter()
# The studies whose one.run() re-runs a sub-test alone (CONTRACT §1). The job is
# `ui.daemon.results.rerun`, which writes beside the stored result: `report --only` overwrote it.
RERUN = ("crossmarket", "monteCarlo")


class Screen(BaseModel):
    """The results on screen, cut down by the window to what it draws, to be written as a page."""

    results: list[dict]
    titles: list[str]
    path: str


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
        planned = _rerun(req) if req.only else table.jobs(req.model_dump())
    except (FileNotFoundError, KeyError, ValueError) as e:
        return {"error": f"no se pudo preparar {req.study}: {e}"}
    if isinstance(planned, str):
        return {"error": planned}
    return {"jobs": [jobs.start(p["label"], p["argv"], p["about"]) for p in planned]}


def _rerun(req: StudyRun) -> list[dict] | str:
    """The jobs of `↻ solo …`: one `ui.daemon.results.rerun` per strategy, or why none starts.

    Args:
        req: A run request with `only` set.

    Returns:
        `{label, argv, about}` per strategy, or the sentence the window shows instead.
    """
    if req.study not in RERUN or req.scope != "one":
        return f"{req.study} no sabe correr una sola subprueba: córrelo entero"
    if not req.strategies:
        return "elige al menos una estrategia"
    if not req.asset:
        return "elige el activo del proyecto: de él salen el feed y las ventanas"
    c = runs.context(req.project, req.databank, "", req.asset)
    why = ((None if c["multimarket"] else transfer.NO_CROSS) if req.study == "crossmarket"
           else runs.own_trades(c))
    if why:
        return f"{req.study}: {why}"
    return [{"label": req.study, "about": {"project": req.project, "databank": req.databank,
                                           "strategy": s, "study": req.study, "scope": "one"},
             "argv": ["-m", "ui.daemon.results.rerun", "--study", req.study, "--project",
                      req.project, "--databank", req.databank, "--asset", req.asset, "--day",
                      c["export"], "--strategy", s, "--only", req.only]
             + (["--set", *req.overrides] if req.overrides else [])}
            for s in req.strategies]


def _tests(project: str, databank: str, strategy: str) -> list[dict]:
    """The Monte Carlo sub-tests offered alone: the «Prueba» options of this strategy's newest result.

    Args:
        project, databank: Where.
        strategy: The strategy on screen; its block sweep depends on its own trade count.

    Returns:
        `[{"key", "label"}]` in the explorer's order, the title as both — the rerun command
        maps it back to its label; empty when the study never ran on this strategy here.
    """
    for day in store.days(project, databank, "monteCarlo"):
        path = Path(f"{store.bank(project, databank) / day / 'monteCarlo' / 'estrategias' / strategy}.json")
        if path.is_file():
            tab = next(t for t in json.loads(path.read_text(encoding="utf-8"))["tabs"]
                       if t["name"] == "explorer")
            prueba = next(s for s in tab["selectors"] if s["key"] == "prueba")
            return [{"key": o, "label": o} for o in prueba["options"]]
    return []


@ROUTER.get("/api/study/only")
def study_only(study: str, project: str = "", databank: str = "", asset: str = "",
               strategy: str = "") -> dict[str, object]:
    """The sub-tests of a study that run alone.

    Args:
        study: A study folder name.
        project, databank, asset: Where; crossmarket's options are the markets of that export.
        strategy: monteCarlo's options are the tests of this strategy's newest stored result;
            without it, none.

    Returns:
        `{"options": [{"key", "label"}]}`, empty when there are none.
    """
    try:
        if study == "monteCarlo":
            return {"options": (_tests(project, databank, strategy)
                                if project and databank and strategy else [])}
        return {"options": table.options(study, project, databank, asset)}
    except (FileNotFoundError, KeyError, ValueError, StopIteration):
        return {"options": []}


@ROUTER.post("/api/study/screen")
def study_screen(req: Screen) -> dict[str, object]:
    """Write what the window shows as one page, through `core.study.render` (22 §6.3 point 10).

    Args:
        req: The results as on screen (the window's `blocks.screen`), each column's title and
            the stored result's JSON, which says where the page goes.

    Returns:
        `{"html": path}` of `<study>/pantalla/<name>-<stamp>.html`, or `{"error": sentence}`.
    """
    if not req.results or len(req.titles) != len(req.results):
        return {"error": "nada que escribir: la pantalla no mandó ningún resultado"}
    base = Path(req.path)
    if not base.resolve().is_relative_to(DATA.resolve()):
        return {"error": f"{base} no está bajo el directorio de datos: no escribo ahí"}
    folder = base.parent.parent if base.parent.name == "estrategias" else base.parent
    name = req.results[0].get("strategy") or req.results[0]["module"].rsplit(".", 1)[-1]
    sections = []
    for result, title in zip(req.results, req.titles):
        sections += ([f"<h1>{escape(title)}</h1>"] if title else []) + page.body(result)
    out = folder / "pantalla" / f"{name}-{datetime.now():%Y%m%d-%H%M%S}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    head = f"{name} — lo que se ve"
    out.write_text(page.shell(head, [f"<h1>{escape(head)}</h1>"] + sections), encoding="utf-8")
    return {"html": str(out)}


@ROUTER.post("/api/jobs/{job_id}/cancel")
def job_cancel(job_id: str) -> dict[str, object]:
    """Cancel a running or queued job.

    Args:
        job_id: The job's `id`.

    Returns:
        `{"ok": bool}` — false when no such job exists or it had already ended.
    """
    return {"ok": jobs.cancel(job_id)}
