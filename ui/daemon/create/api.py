"""The creations' routes: what can be chosen, and the two jobs on the conductor lane."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.datapaths import template_dir, template_draft
from core.paths import ASSETS
from sqx.projects import registry
from ui.daemon import jobs

ROUTER = APIRouter()
TIMEFRAMES = ("M15", "M30", "H1", "H4")
SIZE = {"max_strategies": 500, "minutes": 180}    # the form's defaults: a big project


class Author(BaseModel):
    """The chat's draft to author."""

    name: str


class Project(BaseModel):
    """The new project's form."""

    name: str
    template: str
    symbol: str
    timeframe: str
    max_strategies: int
    minutes: int
    purpose: str


@ROUTER.get("/api/create/options")
def options() -> dict:
    """Every template with a `.sqx`, every asset, the timeframes and the form's defaults."""
    library = template_dir("x").parent
    return {"templates": sorted(d.name for d in library.iterdir() if (d / "template.sqx").exists()),
            "symbols": sorted(f.stem for f in (ASSETS / "symbols").glob("*.yaml")),
            "timeframes": list(TIMEFRAMES), **SIZE}


@ROUTER.post("/api/create/template")
def author(req: Author) -> dict:
    """Queue the headless /sqx-strategy-template on the chat's draft, or say why not."""
    if not template_draft(req.name).exists():
        return {"error": f"no hay borrador «{req.name}»: termina antes la entrevista del chat"}
    return jobs.start("crear plantilla", ["-m", "ui.daemon.create.author", "--name", req.name],
                      {"project": "", "databank": "", "strategy": "", "template": req.name},
                      lane="conductor")


@ROUTER.post("/api/create/project")
def project(req: Project) -> dict:
    """Queue the builder for the form, or say why the name is refused (hard rule 6)."""
    why = registry.check_name(req.name)
    if why:
        return {"error": why}
    return jobs.start("crear proyecto", [
        "-m", "ui.daemon.create.project", req.name, "--template", req.template, "--symbol",
        req.symbol, "--timeframe", req.timeframe, "--max-strategies", str(req.max_strategies),
        "--minutes", str(req.minutes), "--purpose", req.purpose],
        {"project": req.name, "databank": "", "strategy": ""}, lane="conductor")
