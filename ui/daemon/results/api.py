"""The results routes: catalogue, one stored result, its history, the config drawer, the matrix."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.paths import DATA
from ui.daemon import runs as launch
from ui.daemon.results import catalogue, knobs, matrix, runs

ROUTER = APIRouter()


class Overrides(BaseModel):
    """The drawer's pending edits: which study, and its "section.key=value" overrides."""

    study: str
    overrides: list[str] = []


def _unknown(study: str) -> dict | None:
    """The refusal for a study key the catalogue does not hold.

    Args:
        study: What the window sent.

    Returns:
        `{"error": ...}` in Spanish, or None for a known key.
    """
    return None if study in catalogue.STUDIES else {"error": f"No hay ningún estudio «{study}»."}


@ROUTER.get("/api/catalogue")
def catalogue_list() -> dict[str, object]:
    """Every study, in family order, with whether it eliminates or only describes.

    Returns:
        `studies`, one `catalogue.entry` each. Only a study whose role is a knob of its
        config has that config read.
    """
    return {"studies": [catalogue.entry(k, knobs.config(k, []) if callable(catalogue.ROLE[k])
                                        else None) for k in catalogue.ordered()]}


@ROUTER.get("/api/result")
def result(project: str, databank: str, study: str, strategy: str = "", identity: str = "",
           day: str = "") -> dict[str, object]:
    """One stored result and whether today's config would still sign it.

    Args:
        project: SQX project name.
        databank: Databank name, spaces or underscores.
        study: Study key.
        strategy: Strategy name; empty for the population result.
        identity: The strategy's identity; when given, a result of another strategy that
            shares the name is refused instead of shown.
        day: Report day; empty for the newest.

    Returns:
        As `runs.result`.
    """
    return _unknown(study) or runs.result(project, databank, study, strategy, identity, day)


@ROUTER.get("/api/history")
def history(project: str, databank: str, study: str, strategy: str = "",
            identity: str = "") -> dict[str, object]:
    """Every run of a study on a databank or one of its strategies, newest first.

    Args:
        project: SQX project name.
        databank: Databank name.
        study: Study key.
        strategy: Strategy name; empty for the population.
        identity: The strategy's identity, as for `/api/result`.

    Returns:
        As `runs.history`.
    """
    return _unknown(study) or runs.history(project, databank, study, strategy, identity)


@ROUTER.get("/api/config")
def config(study: str) -> dict[str, object]:
    """A study's knobs with their tooltips, and the hash they sign.

    Args:
        study: Study key.

    Returns:
        As `knobs.sections`.
    """
    return _unknown(study) or knobs.sections(study)


@ROUTER.post("/api/config/hash")
def config_hash(req: Overrides) -> dict[str, object]:
    """The hash the next run would sign under the drawer's overrides.

    Args:
        req: Study key and overrides.

    Returns:
        `{"hash"}`, or `{"error"}` when an override names no knob or changes its type —
        typed by the owner, so shown rather than raised.
    """
    refused = _unknown(req.study)
    if refused:
        return refused
    try:
        return {"hash": knobs.signed(req.study, req.overrides)}
    except (KeyError, ValueError, TypeError) as e:
        return {"error": f"Ajuste no válido: {e}"}


@ROUTER.get("/api/matrix")
def population(project: str, databank: str) -> dict[str, object]:
    """Every strategy of one databank against every study.

    Args:
        project: SQX project name.
        databank: Databank name.

    Returns:
        As `matrix.matrix`.
    """
    return matrix.matrix(project, databank)


@ROUTER.get("/api/projects")
def projects() -> dict[str, object]:
    """Every project with reports, its databanks and its asset.

    Returns:
        `projects` by name: databanks as their report folders spell them (underscores for
        spaces; every route here takes either), and the asset read off the project name,
        or None. Folders starting with "_" are fixtures or cross-databank comparisons,
        not a project or a databank.
    """
    root = DATA / "reports"
    return {"projects": [
        {"project": p.name, "asset": launch.guess_asset(p.name),
         "databanks": sorted(d.name for d in p.iterdir()
                             if d.is_dir() and not d.name.startswith("_"))}
        for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith("_")]}
