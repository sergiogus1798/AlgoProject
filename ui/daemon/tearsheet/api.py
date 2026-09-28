"""The Ficha's routes: one strategy's tear sheet, and its P&L by exit reason, from the newest cosecha or the archive."""

from fastapi import APIRouter

from ui.daemon.strategy import archived
from ui.daemon.tearsheet import exits, harvest, oos2, sheet

ROUTER = APIRouter()
TAB = {"IS": "IS", "OOS": "OOS", "OOS1": "OOS"}      # the window says OOS1, the cosecha OOS


def _answer(project: str, databank: str, identity: str, build: object, sample: str,
            source: str, version: str) -> dict:
    """Read the cosecha (or the archive) and build, or the sentence of why not — never a 500.

    Args:
        project, databank, identity: What SELECTION holds.
        build: `sheet.build` or `exits.build`.
        sample: "" for IS and OOS side by side; IS, OOS1 (or OOS) alone; OOS2 behind its door.
        source: "live" reads the newest cosecha; "archive" the archived version, nothing else.
        version: The archived version, "" for the newest.

    Returns:
        A contract result; `{"blocked": sentence, "why"?}` for an OOS2 that may not or cannot
        be read; or `{"error": sentence}`.
    """
    if not (project and databank and identity):
        return {"error": "Elige un proyecto, un databank y una estrategia."}
    if sample not in ("", "OOS2", *TAB):
        return {"error": f"Muestra «{sample}» no válida: IS, OOS1 u OOS2."}
    refused = archived.bad_source(source)
    if refused:
        return refused
    if sample == "OOS2":
        locked = oos2.blocked(project)
        if locked:
            return locked
        data = (oos2.read(project, identity) if source == "live" else
                "el archivo no guarda OOS2: se archiva lo que la cosecha IS/OOS tenía")
        return {"blocked": data} if isinstance(data, str) else build(data)
    data = (harvest.read(project, databank, identity) if source == "live"
            else archived.tearsheet(identity, version))
    if isinstance(data, str):
        return {"error": data}
    got = build(data)
    if sample:
        got["tabs"] = [t for t in got["tabs"] if t["name"] == TAB[sample]]
    return got


@ROUTER.get("/api/tearsheet")
def tearsheet(project: str = "", databank: str = "", identity: str = "", sample: str = "",
              source: str = "live", version: str = "") -> dict:
    """The Ficha: curve, underwater, episodes, months, years, facts — each sample apart.

    Returns:
        A contract result with tabs «IS» and «OOS» (or the one `sample` names) and
        `harvest_day`; `{"blocked"}` for OOS2 while sealed or without export; or `{"error"}`.
    """
    return _answer(project, databank, identity, sheet.build, sample, source, version)


@ROUTER.get("/api/tearsheet/exits")
def tearsheet_exits(project: str = "", databank: str = "", identity: str = "", sample: str = "",
                    source: str = "live", version: str = "") -> dict:
    """P&L and expectancy per exit type, and one cumulative line per type — each sample apart.

    Returns:
        As `/api/tearsheet`.
    """
    return _answer(project, databank, identity, exits.build, sample, source, version)
