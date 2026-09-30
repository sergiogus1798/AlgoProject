"""The results routes: catalogue, one stored result, its history, the config drawer, the matrix."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.paths import DATA
from ui.daemon import runs as launch
from ui.daemon.loader import find
from ui.daemon.results import catalogue, forproject, knobs, matrix, runs
from ui.daemon.runner.table import SAMPLED
from ui.daemon.strategy import archived

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
           day: str = "", source: str = "live", version: str = "") -> dict[str, object]:
    """One stored result and whether today's config would still sign it.

    Args:
        project: SQX project name.
        databank: Databank name, spaces or underscores.
        study: Study key.
        strategy: Strategy name; empty for the population result.
        identity: The strategy's identity; when given, a result of another strategy that
            shares the name is refused instead of shown.
        day: Report day; empty for the newest.
        source: "live" reads `reports/`; "archive" answers from the archived version of
            `identity`, computing nothing (its `stale` is the day of archiving's).
        version: The archived version, "" for the newest.

    Returns:
        As `runs.result`.
    """
    refused = _unknown(study) or archived.bad_source(source)
    if refused:
        return refused
    if source == "archive":
        return archived.result(identity, databank, study, strategy, version)
    got = runs.result(project, databank, study, strategy, identity, day)
    # Any study, not only the sampled readings: the IS/OOS gate's decay and isOos file their
    # run under the retest too (📓 2026-09-30, «Decaimiento» empty opened from Results).
    other = (find.oos_partner(project, databank)
             if got["result"] is None and identity else None)
    # A reading of OOS1 run from a build databank lives on its retest (`runner.table`): shown
    # here only under the same identity, which `runs.result` checks.
    return runs.result(project, other, study, strategy, identity, day) if other else got


@ROUTER.get("/api/history")
def history(project: str, databank: str, study: str, strategy: str = "",
            identity: str = "", source: str = "live", version: str = "") -> dict[str, object]:
    """Every run of a study on a databank or one of its strategies, newest first.

    Args:
        project: SQX project name.
        databank: Databank name.
        study: Study key.
        strategy: Strategy name; empty for the population.
        identity: The strategy's identity, as for `/api/result`.
        source, version: As for `/api/result`; the archive holds one run per study.

    Returns:
        As `runs.history`.
    """
    refused = _unknown(study) or archived.bad_source(source)
    if refused:
        return refused
    if source == "archive":
        return archived.history(identity, databank, study, strategy, version)
    return runs.history(project, databank, study, strategy, identity)


@ROUTER.get("/api/config")
def config(study: str, project: str = "") -> dict[str, object]:
    """A study's knobs with their tooltips, and the hash they sign.

    Args:
        study: Study key.
        project: When given, the knobs the runner fills from the project (its feed, symbol,
            timeframe) show the project's value, with a `note`; a knob it leaves at the
            file's value although the project differs carries a `warn` (`forproject`).

    Returns:
        As `knobs.sections`; the hash is the file's, not the project's.
    """
    refused = _unknown(study)
    if refused:
        return refused
    got = knobs.sections(study)
    return got | {"sections": forproject.apply(study, got["sections"], project)} if project \
        else got


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
def population(project: str, databank: str, identity: str = "", source: str = "live",
               version: str = "") -> dict[str, object]:
    """Every strategy of one databank against every study.

    Args:
        project: SQX project name.
        databank: Databank name.
        identity: With `source=archive`, the archived strategy whose row is served.
        source, version: As for `/api/result`; the archive holds that one row only.

    Returns:
        As `matrix.matrix`.
    """
    refused = archived.bad_source(source)
    if refused:
        return refused
    if source == "archive":
        return archived.matrix(identity, databank, version)
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
