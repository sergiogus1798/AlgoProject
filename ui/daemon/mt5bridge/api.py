"""MT5 Bridge's routes: the form's options, past checks, one result, the preflight and the job."""

from fastapi import APIRouter
from pydantic import BaseModel

from core import sqxfile
from ui.daemon import jobs
from ui.daemon.launch.api import queued
from ui.daemon.mt5bridge import runs

ROUTER = APIRouter()
LABEL = "mt5verify"
FAILS = (OSError, KeyError, ValueError)


class Verify(BaseModel):
    """What the owner confirmed: which strategy, over which window, with which model, where."""

    source: str                 # "archive", "databank" or "folder" (Banquillo)
    identity: str
    version: str = ""
    project: str = ""
    databank: str = ""
    start: str
    end: str
    model: str
    firms: list[str]


@ROUTER.get("/api/mt5bridge/options")
def options() -> dict:
    """The saved accounts, the tester's models, the archived strategies and the Banquillo folder."""
    try:
        return runs.options()
    except FAILS as e:              # the boundary with a person
        return {"error": f"No pude leer las opciones: {type(e).__name__}: {e}"}


class Where(BaseModel):
    """Which strategy the form has chosen, to look up its asset's default dates."""

    source: str
    identity: str
    version: str = ""
    project: str = ""
    databank: str = ""


@ROUTER.post("/api/mt5bridge/dates")
def dates(req: Where) -> dict:
    """Hasta = the last day SQX holds data for this strategy's asset; Desde, a fallback (§3.2)."""
    try:
        path, where = runs.strategy_file(req.source, req.identity, req.version, req.project,
                                         req.databank)
        if path is None:
            return {"error": where}
        asset, _ = sqxfile.symbol(path)
        hasta = runs.hasta_default(asset)
        return {"hasta": hasta, "desde": runs.desde_default(hasta)}
    except FAILS as e:
        return {"error": f"no se pudieron calcular las fechas: {e}"}


@ROUTER.get("/api/mt5bridge/runs")
def listing() -> dict:
    """Every check, newest first."""
    return {"runs": runs.listing()}


@ROUTER.get("/api/mt5bridge/result")
def result(run: str) -> dict:
    """One check's result in the study contract, and how it ended."""
    try:
        return runs.result(run)
    except FAILS as e:
        return {"error": f"No pude leer «{run}»: {type(e).__name__}: {e}"}


def _check(req: Verify) -> dict:
    """The preflight for one request, plus a launcher of the window already queued."""
    path, where = runs.strategy_file(req.source, req.identity, req.version, req.project,
                                     req.databank)
    got = runs.check(path, req.start, req.end, req.model, req.firms)
    got["reasons"] = ([] if path else [where]) + got["reasons"] + queued()
    got["ok"] = not got["reasons"]
    return {**got, "file": str(path) if path else None, "where": where}


@ROUTER.post("/api/mt5bridge/preflight")
def preflight(req: Verify) -> dict:
    """Whether this check may start now, and the text the owner confirms."""
    try:
        return _check(req)
    except FAILS as e:
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"], "text": ""}


@ROUTER.post("/api/mt5bridge/verify")
def verify(req: Verify) -> dict:
    """Queue the check on the conductor lane — after the same preflight, re-run now.

    Returns:
        The job's record (`jobbutton.JobButton` follows its `id`), or `{"error"}` with the
        reasons it was refused.
    """
    got = preflight(req)
    if not got["ok"]:
        return {"error": "no se lanza: " + "; ".join(got["reasons"])}
    start = "mt5" if req.start.strip().upper() == runs.DEEPEST else req.start
    argv = ["-m", "mt5.verify.run", "--strategy", got["file"], "--from", start,
            "--to", req.end, "--model", req.model, "--firms", ",".join(req.firms)]
    job = jobs.start(LABEL, argv, {"project": "", "databank": req.databank,
                                   "strategy": req.identity, "role": "conductor",
                                   "study": LABEL}, lane="conductor")
    return job
