"""The routes of the strategies zone: the databanks, one databank's strategies, one strategy's results."""

from fastapi import APIRouter
from pydantic import BaseModel

from core import assetdata
from ui.daemon import jobs, studies

ROUTER = APIRouter()


class Run(BaseModel):
    """One press of a run button: which module, on which strategy, with which asset."""

    module: str
    project: str
    databank: str
    strategy: str
    asset: str


@ROUTER.get("/api/databanks")
def databank_list() -> dict[str, object]:
    """Every databank the data root holds a strategy table for.

    Returns:
        `databanks`, as `studies.databanks` builds them, plus the module catalogue so the
        window can draw the columns before any strategy is picked.
    """
    return {"databanks": studies.databanks(), "assets": assetdata.symbols(),
            "modules": [{"module": m, "label": label, "step": step}
                        for m, (label, step) in studies.MODULES.items()]}


@ROUTER.get("/api/databank")
def databank(project: str, databank: str, source: str) -> dict[str, object]:
    """The strategies of one databank.

    Args:
        project: SQX project name.
        databank: Databank name.
        source: `metrics` or `harvest`.

    Returns:
        Columns and rows, as `studies.strategies` builds them.
    """
    return studies.strategies(project, databank, source)


@ROUTER.get("/api/results")
def strategy_results(project: str, databank: str, strategy: str,
                     asset: str) -> dict[str, object]:
    """What every module already said about one strategy, and what can be run on it.

    Args:
        project: SQX project name.
        databank: The databank on screen.
        strategy: The strategy's name as SQX spells it.
        asset: The asset the window has chosen for the project.

    Returns:
        As `studies.results` builds it.
    """
    return studies.results(project, databank, strategy, asset)


@ROUTER.post("/api/run")
def run(req: Run) -> dict[str, object]:
    """Start one module on one strategy.

    Args:
        req: Which module, where, and the asset that gives it its feed.

    Returns:
        The job record. A module `runs.plan` refuses raises here instead of starting a
        command that would fail later for the same reason.
    """
    got = studies.runs.plan(req.module, studies.runs.context(req.project, req.databank,
                                                             req.strategy, req.asset))
    return jobs.start(req.module, got["argv"], {"project": req.project, "databank": req.databank,
                                                 "strategy": req.strategy})


@ROUTER.get("/api/jobs")
def job_list() -> dict[str, object]:
    """Every job this daemon started and how each one stands.

    Returns:
        `jobs`, oldest first, each with its exit code and the end of its log.
    """
    return {"jobs": jobs.listing()}
