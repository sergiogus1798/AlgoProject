"""The routes of «Continuar workflow»: its preflight, and the one job that applies it."""

import zipfile
from typing import TypedDict, cast
from xml.etree.ElementTree import ParseError

from fastapi import APIRouter
from pydantic import BaseModel

from sqx import jobs, proof

from sqx.worker import winddown
from ui.daemon.advance import confirm, preflight

ROUTER = APIRouter()
LABEL = "advance"


class Advance(BaseModel):
    """The databank whose discards the owner confirmed deleting."""

    project: str
    databank: str
    nonce: str = ""  # the proof its preflight returned (`proof.py`)


class Answer(TypedDict):
    """The preflight as the window reads it: ok, reasons, the sentence, and what it will touch."""

    ok: bool
    reasons: list[str]
    text: str
    install: str | None
    role: str | None
    task: str | None
    n: int | None


def answer(project: str, databank: str) -> Answer:
    """The preflight as the window reads it, with a queued «Continuar» counted as a refusal."""
    pre = preflight.check(project, databank)
    # «Lanzar en SQX» shares the lane and the workers: one launcher at a time, either way.
    mine = [
        j
        for j in jobs.listing()
        if j["label"] in winddown.LAUNCHERS and j["rc"] is None
    ]
    if mine:
        pre["ok"] = False
        pre["reasons"].append(
            f"ya hay un lanzamiento en marcha o en cola "
            f"({mine[0]['project']} / {mine[0]['databank']})"
        )
    return {
        "ok": pre["ok"],
        "reasons": pre["reasons"],
        "text": confirm.text(pre, project, pre["databank"]) if pre["ok"] else "",
        "install": pre.get("install"),
        "role": pre.get("role"),
        "task": pre.get("task"),
        "n": pre.get("n"),
    }


def shown(project: str, databank: str, got: dict[str, object]) -> dict[str, str]:
    """What a nonce of this launcher is bound to: what was asked and the sentence shown."""
    return {"project": project, "databank": databank, "text": cast("str", got["text"])}


@ROUTER.get("/api/advance/preflight")
def confirmable(project: str, databank: str) -> dict[str, object]:
    """`check`, plus the one-use nonce `POST /api/advance/run` asks back when it is ok."""
    got = check(project, databank)
    return (
        {**got, "nonce": proof.issue(LABEL, shown(project, databank, got))}
        if got["ok"]
        else got
    )


def check(project: str, databank: str) -> dict[str, object]:
    """Whether «Continuar workflow» may run now; the confirmation text when it may."""
    try:
        return cast("dict[str, object]", answer(project, databank))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, ParseError) as e:
        # a file SQX is rewriting, a half-written project.cfx, a bad name
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"], "text": ""}


@ROUTER.post("/api/advance/run")
def run(req: Advance) -> dict[str, object]:
    """Queue the one job that cuts, stages, starts, watches and stops — after re-checking, and
    only with the nonce of a preflight that showed this very sentence."""
    got = check(req.project, req.databank)
    if not got["ok"]:
        return got
    why = proof.refusal(LABEL, req.nonce, shown(req.project, req.databank, got))
    if why:
        return {**got, "ok": False, "reasons": [why]}
    job = jobs.start(
        LABEL,
        [
            "-m",
            "ui.daemon.advance.run",
            "--project",
            req.project,
            "--databank",
            req.databank,
        ],
        {"project": req.project, "databank": req.databank, "role": got.get("role")},
        lane="conductor",
    )
    return {**got, "job": job["id"]}
