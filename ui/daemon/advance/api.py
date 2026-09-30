"""The routes of «Continuar workflow»: its preflight, and the one job that applies it."""

import zipfile
from xml.etree.ElementTree import ParseError

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon import jobs
from ui.daemon.advance import confirm, preflight

ROUTER = APIRouter()
LABEL = "advance"


class Advance(BaseModel):
    """The databank whose discards the owner confirmed deleting."""

    project: str
    databank: str


def answer(project: str, databank: str) -> dict:
    """The preflight as the window reads it, with a queued «Continuar» counted as a refusal."""
    pre = preflight.check(project, databank)
    # «Lanzar en SQX» shares the lane and the workers: one launcher at a time, either way.
    mine = [j for j in jobs.listing() if j["label"] in (LABEL, "launch") and j["rc"] is None]
    if mine:
        pre["ok"] = False
        pre["reasons"].append(f"ya hay un lanzamiento en marcha o en cola "
                              f"({mine[0]['project']} / {mine[0]['databank']})")
    return {"ok": pre["ok"], "reasons": pre["reasons"],
            "text": confirm.text(pre, project, pre["databank"]) if pre["ok"] else "",
            "install": pre.get("install"), "role": pre.get("role"), "task": pre.get("task"),
            "n": pre.get("n")}


@ROUTER.get("/api/advance/preflight")
def check(project: str, databank: str) -> dict[str, object]:
    """Whether «Continuar workflow» may run now; the confirmation text when it may."""
    try:
        return answer(project, databank)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, ParseError) as e:
        # a file SQX is rewriting, a half-written project.cfx, a bad name
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"], "text": ""}


@ROUTER.post("/api/advance/run")
def run(req: Advance) -> dict[str, object]:
    """Queue the one job that cuts, stages, starts, watches and stops — after re-checking."""
    got = check(req.project, req.databank)
    if not got["ok"]:
        return got
    job = jobs.start(LABEL, ["-m", "ui.daemon.advance.run", "--project", req.project,
                             "--databank", req.databank],
                     {"project": req.project, "databank": req.databank,
                      "role": got.get("role")}, lane="conductor")
    return {**got, "job": job["id"]}
