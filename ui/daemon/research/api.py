"""The routes of «Investigar»: the map, the memory, the board, the proposal and the queue."""

import json
from collections.abc import Callable
from typing import Any, cast

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from studies.research.board import store
from ui.daemon import jobs
from ui.daemon.research import preflight, proposals, queue, views

ROUTER = APIRouter()
# The queue is one more launcher: labelled `launch`, the other three refuse while it is queued
# or running (`launch.api.queued`), and a cancel winds it down with SIGTERM (`winddown`).
LABEL = "launch"
FAILS = (OSError, KeyError, ValueError, StopIteration, IndexError, json.JSONDecodeError,
         pd.errors.ParserError)

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


def safe(read: Callable[..., Any], *args: object) -> dict[str, Any]:
    """A read whose failure is shown in the panel instead of taking the daemon down."""
    try:
        return read(*args)
    except FAILS as e:
        return {"error": f"no se pudo leer: {type(e).__name__}: {e}"}


def running(label: str, study: str = "") -> dict[str, Any] | None:
    """The job of that label (and study) queued or running, if any."""
    return next((j for j in jobs.listing() if j["label"] == label and j["rc"] is None
                 and (not study or j.get("study") == study)), None)


@ROUTER.get("/api/research/map")
def profile_map() -> dict[str, Any]:
    """The profile's map: asset × timeframe, dominant family and intensity."""
    return safe(views.profile_map)


@ROUTER.get("/api/research/cell")
def cell(symbol: str, timeframe: str) -> dict[str, Any]:
    """One cell's measures, each with its explanation."""
    return safe(views.cell, symbol, timeframe)


@ROUTER.get("/api/research/memory")
def memory() -> dict[str, Any]:
    """Coverage, each attempt's funnel, survivors per family, ideas spent."""
    return safe(views.memory)


@ROUTER.get("/api/research/board")
def board() -> dict[str, Any]:
    """The board, ordered now."""
    return safe(views.board)


@ROUTER.get("/api/research/proposal")
def shown(id: str = "") -> dict[str, Any]:
    """One proposal (the newest by default), each idea with whether it may be launched."""
    return safe(proposals.latest, id)


@ROUTER.post("/api/research/veto")
def veto(req: Veto) -> dict[str, Any]:
    """Veto an idea, or lift the veto."""
    return safe(proposals.veto, req.id, req.idea, req.vetoed)


@ROUTER.post("/api/research/answer")
def answer(req: Answer) -> dict[str, Any]:
    """Record the owner's answer to an idea's open question."""
    return safe(proposals.answer, req.id, req.idea, req.question, req.text.strip())


@ROUTER.get("/api/research/launch")
def launch_check(id: str) -> dict[str, Any]:
    """Whether the queue may start now, and the sentence to confirm."""
    try:
        return cast("dict[str, Any]", preflight.check(id))
    except FAILS as e:
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"], "text": "", "ideas": []}


@ROUTER.post("/api/research/launch")
def launch(req: Launch) -> dict[str, Any]:
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
def queued(id: str) -> dict[str, Any]:
    """A proposal's queue: which idea is on the custodian, which wait, which ended and how."""
    f = queue.path(id)
    state = safe(store.read, f) if f.exists() else {}
    return {"queue": state, "job": running(LABEL, "Investigar: cola")}
