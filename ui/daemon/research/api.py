"""The routes of «Investigar»: the map, the memory, the board, the director and the queue."""

import json

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from studies.research.board import proposal, store
from ui.daemon import jobs
from ui.daemon.research import preflight, proposals, queue, views

ROUTER = APIRouter()
DIRECTOR = "researchDirector"
# The queue is one more launcher: labelled `launch`, the other three refuse while it is queued
# or running (`launch.api.queued`), and a cancel winds it down with SIGTERM (`winddown`).
LABEL = "launch"
FAILS = (OSError, KeyError, ValueError, StopIteration, IndexError, json.JSONDecodeError,
         pd.errors.ParserError)
COST = ("El director lee el tablero, elige UNA celda y pide tres ideas al ideaExpert. Cuesta "
        "unos 10-30 $ en tokens y tarda entre 20 y 60 minutos. No toca SQX ni lanza nada: "
        "deja una propuesta que tú vetas aquí.")


class Confirm(BaseModel):
    """The owner confirmed spending the director's tokens."""

    confirmed: bool = False


class Veto(BaseModel):
    """One idea of a proposal, vetoed or not."""

    id: str
    idea: str
    vetoed: bool


class Answer(BaseModel):
    """The owner's answer to one open question of an idea."""

    id: str
    idea: str
    question: int
    text: str


class Launch(BaseModel):
    """What the owner confirmed launching: the proposal and the ideas he was shown."""

    id: str
    ideas: list[str]


def safe(read: object, *args: object) -> dict:
    """A read whose failure is shown in the panel instead of taking the daemon down."""
    try:
        return read(*args)
    except FAILS as e:
        return {"error": f"no se pudo leer: {type(e).__name__}: {e}"}


def running(label: str, study: str = "") -> dict | None:
    """The job of that label (and study) queued or running, if any."""
    return next((j for j in jobs.listing() if j["label"] == label and j["rc"] is None
                 and (not study or j.get("study") == study)), None)


@ROUTER.get("/api/research/map")
def profile_map() -> dict:
    """The profile's map: asset × timeframe, dominant family and intensity."""
    return safe(views.profile_map)


@ROUTER.get("/api/research/cell")
def cell(symbol: str, timeframe: str) -> dict:
    """One cell's measures, each with its explanation."""
    return safe(views.cell, symbol, timeframe)


@ROUTER.get("/api/research/memory")
def memory() -> dict:
    """Coverage, each attempt's funnel, survivors per family, ideas spent."""
    return safe(views.memory)


@ROUTER.get("/api/research/board")
def board() -> dict:
    """The board, ordered now."""
    return safe(views.board)


@ROUTER.get("/api/research/direct")
def direct_state() -> dict:
    """Whether the director runs, the step it recorded, and what a press costs."""
    job = running(DIRECTOR)
    last = next((j for j in reversed(jobs.listing()) if j["label"] == DIRECTOR), None)
    return {"running": bool(job), "job": job or last, "cost": COST,
            "step": safe(proposals.state) if job else {}, "steps": list(proposal.STEPS)}


@ROUTER.post("/api/research/direct")
def direct(req: Confirm) -> dict:
    """Queue the director — only on the owner's confirmation, and never two at once."""
    if not req.confirmed:
        return {"ok": False, "reasons": ["falta confirmar el coste"], "cost": COST}
    if running(DIRECTOR):
        return {"ok": False, "reasons": ["el director ya está trabajando"]}
    job = jobs.start(DIRECTOR, ["-m", "ui.daemon.research.direct"],
                     {"project": "", "databank": "", "study": DIRECTOR})
    return {"ok": True, "job": job["id"]}


@ROUTER.get("/api/research/proposal")
def shown(id: str = "") -> dict:
    """One proposal (the newest by default), each idea with whether it may be launched."""
    return safe(proposals.latest, id)


@ROUTER.post("/api/research/veto")
def veto(req: Veto) -> dict:
    """Veto an idea, or lift the veto."""
    return safe(proposals.veto, req.id, req.idea, req.vetoed)


@ROUTER.post("/api/research/answer")
def answer(req: Answer) -> dict:
    """Record the owner's answer to an idea's open question."""
    return safe(proposals.answer, req.id, req.idea, req.question, req.text.strip())


@ROUTER.get("/api/research/launch")
def launch_check(id: str) -> dict:
    """Whether the queue may start now, and the sentence to confirm."""
    try:
        return preflight.check(id)
    except FAILS as e:
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"], "text": "", "ideas": []}


@ROUTER.post("/api/research/launch")
def launch(req: Launch) -> dict:
    """Queue the proposal's ideas as ONE job on the conductor lane — after re-checking."""
    got = launch_check(req.id)
    if not got["ok"]:
        return got
    if got["ideas"] != req.ideas:
        return {**got, "ok": False, "reasons": ["las ideas que irían cambiaron desde que lo "
                                                "viste: vuelve a pulsar y confirma"]}
    job = jobs.start(LABEL, ["-m", "ui.daemon.research.queue", "--proposal", req.id],
                     {"project": got["projects"][0], "role": got["role"],
                      "databank": f"{len(req.ideas)} ideas", "study": "Investigar: cola"},
                     lane="conductor")
    return {**got, "job": job["id"]}


@ROUTER.get("/api/research/queue")
def queued(id: str) -> dict:
    """A proposal's queue: which idea is on the custodian, which wait, which ended and how."""
    f = queue.path(id)
    state = safe(store.read, f) if f.exists() else {}
    return {"queue": state, "job": running(LABEL, "Investigar: cola")}
