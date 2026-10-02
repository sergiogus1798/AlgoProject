"""The gallery's routes: every project on one list, and where one strategy of a project lives."""

from fastapi import APIRouter

from ui.daemon.projects import sources

ROUTER = APIRouter()


@ROUTER.get("/api/projects/all")
def every_project() -> dict[str, object]:
    """Every project the window can open, one card each (encargo 22 §3).

    Returns:
        `projects`: as `sources.gallery`. Unlike `/api/projects`, a project with no reports
        yet is listed: it is found on its install.
    """
    try:
        return {"projects": sources.gallery()}
    except (OSError, KeyError, ValueError) as e:     # a project.cfx SQX is rewriting
        return {"projects": [], "error": f"no se pudieron leer los proyectos: {e}"}


@ROUTER.get("/api/projects/one")
def one_project(name: str) -> dict[str, object]:
    """One project's symbol, timeframe and template from `registry.csv` alone — what a zone
    titles itself with before the gallery's ~12 s list has arrived (📓 2026-09-30: «· ? · ?»).

    Returns:
        `symbol`, `timeframe`, `template` (library name); {} for a project the registry lacks.
    """
    row = sources.registered().get(name)
    if not row:
        return {}
    return {"symbol": row["symbol"], "timeframe": row["timeframe"],
            "template": sources.template(row["template"])}


@ROUTER.get("/api/projects/find")
def find_strategy(project: str, identity: str, databank: str = "") -> dict[str, object]:
    """The databank and name of one strategy of a project, by its identity.

    Args:
        project: Project name.
        identity: The strategy's identity.
        databank: Where to look first, or "".

    Returns:
        As `sources.locate`.
    """
    return sources.locate(project, identity, databank)
