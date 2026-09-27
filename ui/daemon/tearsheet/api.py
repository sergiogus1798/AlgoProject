"""The Ficha's routes: one strategy's tear sheet, and its P&L by exit reason, from the newest cosecha."""

from fastapi import APIRouter

from ui.daemon.tearsheet import exits, harvest, sheet

ROUTER = APIRouter()


def _answer(project: str, databank: str, identity: str, build: object) -> dict:
    """Read the cosecha and build, or the sentence of why not — never a 500 to the window.

    Args:
        project, databank, identity: What SELECTION holds.
        build: `sheet.build` or `exits.build`.

    Returns:
        A contract result, or `{"error": sentence}`.
    """
    if not (project and databank and identity):
        return {"error": "Elige un proyecto, un databank y una estrategia."}
    data = harvest.read(project, databank, identity)
    return {"error": data} if isinstance(data, str) else build(data)


@ROUTER.get("/api/tearsheet")
def tearsheet(project: str = "", databank: str = "", identity: str = "") -> dict:
    """The Ficha: curve, underwater, episodes, months, years, facts — IS and OOS apart.

    Returns:
        A contract result with tabs «IS» and «OOS» and `harvest_day`, or `{"error"}`.
    """
    return _answer(project, databank, identity, sheet.build)


@ROUTER.get("/api/tearsheet/exits")
def tearsheet_exits(project: str = "", databank: str = "", identity: str = "") -> dict:
    """P&L and expectancy per exit type, and one cumulative line per type — IS and OOS apart.

    Returns:
        A contract result with tabs «IS» and «OOS» and `harvest_day`, or `{"error"}`.
    """
    return _answer(project, databank, identity, exits.build)
