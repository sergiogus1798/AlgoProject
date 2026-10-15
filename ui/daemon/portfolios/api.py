"""The routes of the PORTFOLIOS zone: what exists, each module's tabs, and the «Calcular» launchers."""

import inspect
import re
import secrets
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from portfolio.common.construct.inputs import pool as pool_mod
from portfolio.funded.decide import tables
from ui.daemon import jobs, proof
from ui.daemon.portfolios import (
    analyse,
    bank,
    commands,
    construct,
    correlation,
    funded,
    owner,
    shelf,
    weights,
)

ROUTER = APIRouter()
READERS = {
    "Analizar": analyse.read,
    "Correlación": correlation.read,
    "Constructor": construct.read,
    "Fondeo": funded.read,
    "Banco": bank.read,
    "Pesos": weights.read,
    "Incubación": weights.incubation,
}
FAILS = (OSError, KeyError, ValueError, IndexError)
NAME = re.compile(r"^(Test|Trade|Research)_[A-Za-z0-9_]+$")


class Run(BaseModel):
    """One «Calcular» the owner pressed: the action, its settings, and the proof of its preflight."""

    action: str
    params: dict[str, str] = {}
    nonce: str = ""


class OwnerInput(BaseModel):
    """One owner input typed in the window: a row's id and the text of its box ("" = back to the file's value)."""

    field: str
    value: str


class Pool(BaseModel):
    """A pool to declare from the ticked strategies."""

    name: str
    members: list[dict[str, str]]  # identity, version


@ROUTER.get("/api/portfolios/state")
def state() -> dict[str, object]:
    """What the zone's selectors and its databank list: pools, runs, plans, bank tables, the root."""
    plans = funded.plans()
    return {
        "test_root": shelf.test_root(),
        "pools": shelf.pools(),
        "runs": shelf.runs(),
        "plans": plans,
        "firms": sorted({p.split(":")[0] for p in plans}),
        "banks": [t["folder"].name for t in tables.runs()],
        "modules": list(READERS),
    }


@ROUTER.get("/api/portfolios/module")
def module(
    name: str,
    pool: str = "",
    run: str = "",
    plan: str = "",
    firm: str = "",
    freq: str = "monthly",
    measure: str = "",
    bank: str = "",
    strategy: str = "",
) -> dict[str, object]:
    """One rail module's tabs for the selection, or its empty state — read from disk, nothing computed."""
    reader = READERS.get(name)
    if reader is None:
        return {"tabs": [], "empty": f"No existe el módulo «{name}».", "relaxed": ""}
    given = {
        "pool": pool,
        "run": run,
        "plan": plan,
        "firm": firm,
        "freq": freq,
        "measure": measure,
        "bank": bank,
        "strategy": strategy,
    }
    takes = inspect.signature(reader).parameters
    try:
        return reader(**{k: v for k, v in given.items() if k in takes})
    except FAILS as e:  # a folder being written, a run of an older shape
        return {
            "tabs": [],
            "empty": f"No se pudo leer: {type(e).__name__}: {e}",
            "relaxed": "",
        }


@ROUTER.get("/api/portfolios/pair")
def pair(
    pool: str, i: str, j: str, firm: str = "", freq: str = "monthly"
) -> dict[str, object]:
    """One pair of the matrix: both P&L series in build and every measure against its threshold."""
    try:
        return correlation.pair(pool, i, j, firm, freq)
    except FAILS as e:
        return {
            "title": "No se pudo leer la pareja",
            "relaxed": "",
            "blocks": [
                {"kind": "callout", "state": "fail", "text": f"{type(e).__name__}: {e}"}
            ],
        }


def shown(action: str, params: dict[str, str], got: dict[str, Any]) -> dict[str, Any]:
    """What a nonce is bound to: what was asked, the command and the sentence shown."""
    return {
        "action": action,
        "params": params,
        "argv": got["argv"],
        "text": got["text"],
    }


@ROUTER.get("/api/portfolios/preflight")
def preflight(
    action: str,
    pool: str = "",
    run: str = "",
    plan: str = "",
    firm: str = "",
    horizon: str = "",
    edge_from: str = "",
    n_paths: str = "",
    sets: str = "",
    seed: str = "",
) -> dict[str, object]:
    """Whether a «Calcular» may start, what it lacks, the sentence to confirm, and its one-use nonce.

    A fresh seed is drawn when none is given (owner, 2026-10-14, D25: each launch is an independent
    draw); it travels back in `params`, so the launch's recheck rebuilds the same bound argv.
    """
    params = {
        "pool": pool,
        "run": run,
        "plan": plan,
        "firm": firm,
        "horizon": horizon,
        "edge_from": edge_from,
        "n_paths": n_paths,
        "sets": sets,
        "seed": seed or str(secrets.randbits(31)),
    }
    try:
        got = commands.plan(action, params)
    except (*FAILS, SystemExit) as e:  # a knob the config refuses, a run folder gone
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"]}
    return (
        {
            **got,
            "params": params,
            "nonce": proof.issue(commands.LABEL, shown(action, params, got)),
        }
        if got["ok"]
        else got
    )


@ROUTER.post("/api/portfolios/run")
def run_action(req: Run) -> dict[str, object]:
    """Queue the command as one Python job — after re-checking, and only against a spent nonce."""
    got: dict[str, Any] = preflight(
        req.action,
        **{
            k: v
            for k, v in req.params.items()
            if k in inspect.signature(preflight).parameters
        },
    )
    if not got["ok"]:
        return got
    proof.ISSUED.pop(got["nonce"], None)  # the recheck's own nonce is not the owner's
    refused = proof.refusal(
        commands.LABEL, req.nonce, shown(req.action, got["params"], got)
    )
    if refused:
        return {"ok": False, "reasons": [refused]}
    job = jobs.start(commands.LABEL, got["argv"], got["about"])
    return {"ok": True, "job": job["id"], "reasons": []}


@ROUTER.post("/api/portfolios/pool")
def declare(req: Pool) -> dict[str, object]:
    """Freeze the ticked strategies as a named pool; a name already declared is refused."""
    if not NAME.match(req.name):
        return {
            "ok": False,
            "reasons": [
                "el nombre empieza por Test_, Trade_ o Research_ y solo lleva letras, "
                "cifras y guiones bajos"
            ],
        }
    if len(req.members) < 2:
        return {"ok": False, "reasons": ["un pool lleva al menos dos estrategias"]}
    try:
        path = pool_mod.declare(
            req.name,
            [{"identity": m["identity"], "version": m["version"]} for m in req.members],
            "ventana",
        )
    except (FileExistsError, *FAILS) as e:
        return {"ok": False, "reasons": [str(e)]}
    return {"ok": True, "reasons": [], "path": str(path)}


@ROUTER.get("/api/portfolios/owner")
def owner_inputs() -> dict[str, object]:
    """The owner's inputs of the funding modules, each with the value in force and what it blocks."""
    return {"fields": owner.read()}


@ROUTER.post("/api/portfolios/owner")
def owner_write(req: OwnerInput) -> dict[str, object]:
    """Write one typed input to the owner's local layer; nothing else is ever written."""
    try:
        return {"ok": True, "reasons": [], **owner.set_field(req.field, req.value)}
    except (*FAILS, OSError) as e:
        return {"ok": False, "reasons": [str(e)]}
