"""The routes of «Lanzar en SQX» and «Correr workflow»: tasks, steps, preflights and the jobs that run them."""

import json
import zipfile
from datetime import datetime
from xml.etree.ElementTree import ParseError

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon import jobs, workerguard
from ui.daemon.advance import preflight as advance
from ui.daemon.launch import chain, preflight
from ui.daemon.workflow.steps import STEPS

ROUTER = APIRouter()
LABEL = "launch"
# The launchers share the conductor lane and refuse each other: two jobs starting and
# stopping workers at once is OPEN.md §32 from inside the window. `mt5verify` is MT5 Bridge's.
LAUNCHERS = (LABEL, "advance", "mt5verify")
FAILS = (OSError, KeyError, ValueError, zipfile.BadZipFile, ParseError)


class Launch(BaseModel):
    """What the owner confirmed launching: one task by title, or one workflow step's tasks."""

    project: str
    task: str = ""
    step: str = ""


class Chain(BaseModel):
    """The project whose «Correr workflow» the owner confirmed, and the plan he was shown."""

    project: str
    plan: dict = {}


def orphans() -> list[dict]:
    """What a closed window's launcher left: its markers that no job of this daemon owns."""
    return workerguard.orphans({j["_proc"].pid for j in jobs.JOBS if j["_proc"]})


def queued() -> list[str]:
    """A launcher of any kind queued or running — here, or orphaned by a closed window and
    still alive: the refusal, both ways, or nothing."""
    mine = [j for j in jobs.listing() if j["label"] in LAUNCHERS and j["rc"] is None]
    out = [f"ya hay un lanzamiento en marcha o en cola en {mine[0]['project']}: espera a que "
           "acabe"] if mine else []
    return out + [o["text"] for o in orphans() if o["alive"]]


@ROUTER.get("/api/launch/tasks")
def listing(project: str) -> dict[str, object]:
    """A project's SQX tasks with what their databanks hold now, or why none can be listed."""
    try:
        got = preflight.tasks(project)
    except FAILS as e:      # a file SQX is rewriting, a half-written project.cfx
        return {"refuse": f"no se pudo leer el proyecto: {e}"}
    if "refuse" in got:
        return {"refuse": got["refuse"]}
    return {"install": got["install"], "role": got["role"], "tasks": got["tasks"]}


@ROUTER.get("/api/launch/preflight")
def check(project: str, task: str = "", step: str = "") -> dict[str, object]:
    """Whether a task, or a step's tasks, may be launched now; the confirmation text when so."""
    try:
        pre = preflight.check(project, task, step)
    except FAILS as e:
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"], "text": ""}
    pre["reasons"] += queued()
    pre["ok"] = not pre["reasons"]
    return {"ok": pre["ok"], "reasons": pre["reasons"], "role": pre.get("role"),
            "titles": [t["title"] for t in pre.get("chosen", [])],
            "text": preflight.text(pre, project) if pre["ok"] else ""}


@ROUTER.get("/api/launch/steps")
def steps(project: str) -> dict[str, object]:
    """Every SQX step of the rail: whether its ▶ SQX may launch it now, and why not."""
    try:
        got = preflight.tasks(project)
        busy = [] if "refuse" in got else advance.busy(got["role"], project) + queued()
    except FAILS as e:
        got = {"refuse": f"no se pudo comprobar: {e}"}
    out = {}
    for s in [s for s in STEPS if s["kind"] == "sqx"]:
        pre = ({"ok": False, "reasons": [got["refuse"]]} if "refuse" in got
               else preflight.judge(project, got, busy, step=s["n"]))
        out[s["n"]] = {"ok": pre["ok"], "reasons": pre["reasons"],
                       "titles": [t["title"] for t in pre.get("chosen", [])],
                       "elsewhere": pre.get("elsewhere", False)}
    return {"steps": out, "warnings": [o["text"] for o in orphans()]}


@ROUTER.post("/api/launch/run")
def run(req: Launch) -> dict[str, object]:
    """Queue the one job that stages, starts, watches and stops — after re-checking."""
    got = check(req.project, req.task, req.step)
    if not got["ok"]:
        return got
    what = ["--step", req.step] if req.step else ["--task", req.task]
    job = jobs.start(LABEL, ["-m", "ui.daemon.launch.run", "--project", req.project, *what],
                     {"project": req.project, "role": got["role"],
                      "databank": f"paso {req.step}" if req.step else req.task},
                     lane="conductor")
    return {**got, "job": job["id"], "task": req.task, "step": req.step}


@ROUTER.get("/api/launch/chain")
def chain_check(project: str) -> dict[str, object]:
    """Whether «Correr workflow» may start now, its plan, and the sentence to confirm."""
    try:
        got = chain.check(project)
    except FAILS as e:
        return {"ok": False, "reasons": [f"no se pudo comprobar: {e}"], "text": ""}
    got["reasons"] += queued()
    got["ok"] = not got["reasons"]
    return {"ok": got["ok"], "reasons": got["reasons"], "plan": got["plan"],
            "role": got.get("role"), "text": chain.text(got, project) if got["ok"] else ""}


@ROUTER.post("/api/launch/chain")
def chain_run(req: Chain) -> dict[str, object]:
    """Queue «Correr workflow» as ONE job on the conductor lane — after re-checking.

    Labelled `launch`: «Continuar workflow» refuses while it is queued or running, as it
    refuses «Lanzar en SQX».
    """
    got = chain_check(req.project)
    if not got["ok"]:
        return got
    if got["plan"] != req.plan:
        return {**got, "ok": False, "reasons": ["el plan cambió desde que lo viste: vuelve a "
                                                "pulsar y confirma el nuevo"]}
    # The job runs exactly what was confirmed: its own process cannot see this daemon's jobs.
    confirmed = jobs.LOGS / f"chain-{req.project}-{datetime.now():%Y%m%d-%H%M%S}.json"
    confirmed.parent.mkdir(parents=True, exist_ok=True)
    confirmed.write_text(json.dumps(req.plan, ensure_ascii=False), encoding="utf-8")
    job = jobs.start(LABEL, ["-m", "ui.daemon.launch.chain", "--project", req.project,
                             "--plan", str(confirmed)],
                     {"project": req.project, "role": got["role"], "databank": "workflow entero",
                      "study": "Correr workflow"}, lane="conductor")
    return {**got, "job": job["id"]}
