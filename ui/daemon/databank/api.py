"""The databank panel's routes: tabs, table, columns, aggregate equity, funnel and reload."""

from collections.abc import Callable

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ui.daemon.databank import columns, equity, funnel, layout, segments, table
from ui.daemon.loader import api as loader
from ui.daemon.loader import find

ROUTER = APIRouter()


class Reload(BaseModel):
    """The databank whose «Recargar databank» the owner pressed."""

    project: str
    databank: str


def shown(what: str, read: Callable[..., dict], *args: str) -> dict:
    """One read for the window, a failure as `error` instead of a 500 (the ui boundary)."""
    try:
        return read(*args)
    except Exception as failed:  # noqa: BLE001 — a file SQX is rewriting, a report half-written
        return {"error": f"No se pudo leer {what} de {' / '.join(args)}: {failed}"}


@ROUTER.get("/api/databank/panels")
def get_panels(project: str) -> dict:
    """The two tab rows of one project, each sub-panel with its databank."""
    return shown("las pestañas", layout.panels, project)


@ROUTER.get("/api/databank/table")
def get_table(project: str, databank: str) -> dict:
    """One databank: a row per strategy, its metrics and every study's columns."""
    return shown("la tabla", table.table, project, databank)


@ROUTER.get("/api/databank/segments")
def get_segments(project: str, databank: str) -> dict:
    """The IS+OOS1 figures the column chooser can add, computed from the cosecha's trades."""
    return shown("la unión IS+OOS1", segments.segments, project, databank)


class View(BaseModel):
    """One table's choice against its default ({hidden, added, order}); None restores it."""

    project: str
    databank: str
    table: str
    view: dict | None = None


@ROUTER.get("/api/databank/columns")
def get_columns(project: str, databank: str) -> dict:
    """Every table's saved column choice of one databank, `views` {table: ids}."""
    return shown("las columnas", lambda p, d: {"views": columns.views(p, d)}, project, databank)


@ROUTER.post("/api/databank/columns")
def post_columns(req: View) -> dict:
    """Keep (or, with `view` None, forget) one table's choice under AlgoData/filters/."""
    return shown("las columnas",
                 lambda p, d: {"views": columns.save(p, d, req.table, req.view)},
                 req.project, req.databank)


class Visible(BaseModel):
    """The aggregate of only the rows a filter left visible; `ids` None for every row."""

    project: str
    databank: str
    ids: list[str] | None = None


@ROUTER.get("/api/databank/equity")
def get_equity(project: str, databank: str, ids: list[str] | None = Query(None)) -> dict:
    """The databank's aggregate daily curve, SQX's and at the real spread; `ids` (repeated)
    keeps only those strategies."""
    return shown("la equity agregada", lambda p, d: equity.equity(p, d, ids), project, databank)


@ROUTER.post("/api/databank/equity")
def post_equity(req: Visible) -> dict:
    """The same curve for a long list of visible identities, which a URL would not carry."""
    return shown("la equity agregada", lambda p, d: equity.equity(p, d, req.ids),
                 req.project, req.databank)


@ROUTER.get("/api/databank/funnel")
def get_funnel(project: str) -> dict:
    """The population's funnel of one project."""
    return shown("el embudo", funnel.funnel, project)


@ROUTER.post("/api/databank/reload")
def reload(req: Reload) -> dict:
    """«Recargar databank»: forget every cached roster, list the folder again and ask
    `POST /api/load` for what the databank now misses.

    Returns:
        `strategies` — the roster read now —, and `load`, what `/api/load` answered.
    """
    find.forget()
    held = shown("el databank", lambda p, d: {"n": len(find.roster(p, d))},
                 req.project, req.databank)
    return {"strategies": held.get("n"), "error": held.get("error"),
            "load": loader.load(loader.Load(project=req.project, databank=req.databank))}
