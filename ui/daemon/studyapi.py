"""The routes of the strategies zone: the databanks, one databank's strategies, one strategy's results."""

from fastapi import APIRouter
from pydantic import BaseModel

from core import assetdata
from ui.daemon import gateview, jobs, progress, studies

ROUTER = APIRouter()


class GateRun(BaseModel):
    """One press of the gate's run button: which harvest, the asset for its feed, overrides."""

    project: str
    databank: str
    asset: str
    overrides: list[str] = []


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


@ROUTER.get("/api/gate/harvests")
def gate_harvests() -> dict[str, object]:
    """Every cosecha and whether the gate judged it, plus the screens as configured today.

    Returns:
        `harvests` newest first and `screens` with their thresholds and their why.
    """
    return {"harvests": gateview.harvests(), "screens": gateview.screens()}


@ROUTER.get("/api/gate/report")
def gate_report(project: str, databank: str, day: str) -> dict[str, object]:
    """One gate report in full.

    Args:
        project: Project name.
        databank: The build databank.
        day: The report's day, `report_day` of the harvest listing.

    Returns:
        As `gateview.gate` builds it.
    """
    return gateview.gate(project, databank, day)


@ROUTER.get("/api/gate/strategy")
def gate_strategy(project: str, databank: str, day: str, identity: str) -> dict[str, object]:
    """One strategy's paired metrics and daily curve.

    Args:
        project: Project name.
        databank: The build databank.
        day: The harvest day.
        identity: The harvest's index value.

    Returns:
        As `gateview.strategy` builds it.
    """
    return gateview.strategy(project, databank, day, identity)


@ROUTER.post("/api/gate/run")
def gate_run(req: GateRun) -> dict[str, object]:
    """Run the gate over a databank's newest cosecha.

    Args:
        req: The harvest, the asset whose feed the monkey prices with, and any
            `screen.threshold=value` overrides — recorded in the report's manifest.

    Returns:
        The job record.
    """
    feed = assetdata.load(req.asset)["sqx_symbol"]
    argv = ["-m", "studies.screening.gate.report", "--project", req.project, "--databank", req.databank,
            "--feed", feed]
    for item in req.overrides:
        argv += ["--set", item]
    return jobs.start("gate", argv, {"project": req.project, "databank": req.databank,
                                     "strategy": ""})


@ROUTER.get("/api/progress/installs")
def progress_installs() -> dict[str, object]:
    """Every install by role, with the projects each one holds.

    Returns:
        Role → project names. Read off the folders: no install is asked anything.
    """
    return {role: progress.projects(path) for role, path in progress.installs().items()}


@ROUTER.get("/api/progress")
def progress_state(install: str, project: str) -> dict[str, object]:
    """Where one project of one install is right now.

    Args:
        install: A role from the installs listing.
        project: One of its projects.

    Returns:
        As `progress.state` builds it, from the project file, the databank folders and
        the tail of today's log.
    """
    return progress.state(install, project)
