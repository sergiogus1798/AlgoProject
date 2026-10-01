#!/usr/bin/env python3
"""«Correr workflow»: every pending step in WORKFLOW.md's order, SQX and Python, up to the next decision."""

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil

from core.paths import ROOT
from sqx.projects import stage
from ui.daemon import jobs
from ui.daemon.advance import preflight as advance
from ui.daemon.advance.run import say
from ui.daemon.launch import chainplan, preflight
from ui.daemon.launch import run as launcher
from ui.daemon.loader import state as loader
from ui.daemon.workflow import api as workflow
from ui.daemon.workflow import run as rail

TAIL = 4    # lines of a failed command's output the chain's log keeps
# The python lane's RAM rule (`jobs.FLOOR_GB`): a test starts below the floor only alone.
_RUNNING = {"n": 0, "stop": False}
CHILDREN: set[subprocess.Popen] = set()     # the tests and exports running now
_GATE = threading.Lock()


def check(project: str) -> dict:
    """Whether the chain may start now, what it would run and where it would stop.

    Args:
        project: Project name.

    Returns:
        `ok`, `reasons`, `plan` (`chainplan.plan`), `install`, `role`. Refused on the master,
        on a worker someone uses (`advance.busy`, the same preflight as every launcher),
        with nothing to run, and when the first SQX step cannot start as it stands; a later
        SQX step is only checked for its tasks now, and fully just before it starts.
    """
    plan = chainplan.plan(workflow.workflow(project))
    where = advance.where(project)
    if "refuse" in where:
        return {"ok": False, "reasons": [where["refuse"]], "plan": plan}
    reasons = advance.busy(where["role"], project)
    if not plan["do"]:
        reasons.append(f"nada que correr: se para ya en el paso {plan['stop']['n']} — "
                       f"{plan['stop']['why']}" if plan["stop"]["n"] else plan["stop"]["why"])
    filled: set[str] = set()      # outputs of the SQX steps planned before this one
    for action in [a for a in plan["do"] if a["kind"] == "sqx"]:
        pre = preflight.check(project, step=action["n"], filled=filled)
        action["titles"] = [t["title"] for t in pre.get("chosen", [])]
        filled |= {t["output"] for t in pre.get("chosen", [])}
        reasons += [f"paso {action['n']}: {r}" for r in pre["reasons"] if r not in reasons]
    return {"ok": not reasons, "reasons": reasons, "plan": plan, **where}


def text(got: dict, project: str) -> str:
    """The sentence the owner confirms: every step that runs, where, and where it stops."""
    who = preflight.ROLES.get(got["role"], got["role"])
    lines = [f"«Correr workflow» en {project} ({got['install']}), en este orden:"]
    for a in got["plan"]["do"]:
        lines.append(f"· paso {a['n']} · {a['title']} — " + (
            f"SQX en el {who}: {', '.join(a['titles'])}; el worker arranca, corre hasta "
            "«Project finished» y se para" if a["kind"] == "sqx" else
            f"Python: {', '.join(a['tests'])}"))
    stop = got["plan"]["stop"]
    lines.append(f"Se para antes del paso {stop['n']} · {stop['title']}: {stop['why']}."
                 if stop["n"] else f"Y termina: {stop['why']}.")
    return "\n".join(lines + ["", chainplan.RULE])


def feeds(n: str, ctx: dict) -> list[str]:
    """The databanks a Python step's tests read: its `feeds` stages' outputs, as SQX spells them."""
    spec = rail.BY_N[n]
    if spec["feeds"] == "batch" or not ctx["sqx"]:
        return []
    names = [t for s in spec["feeds"] for t in stage.titles(s)]
    return list(dict.fromkeys(t["output"] for t in ctx["sqx"]["tasks"] if t["title"] in names))


def command(argv: list[str]) -> tuple[int, str]:
    """Run one `python3 -m …` to its end; its return code and the tail of what it printed.
    Held in `CHILDREN` while it runs, so a cancel can end it at once (`cancelled`)."""
    proc = subprocess.Popen([sys.executable, *argv], cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            env={**os.environ, "PYTHONUTF8": "1"})
    CHILDREN.add(proc)
    try:
        out, _ = proc.communicate()
    finally:
        CHILDREN.discard(proc)
    return proc.returncode, " / ".join(out.strip().splitlines()[-TAIL:])


def cancelled(signum: int, frame: object) -> None:
    """SIGTERM: end the tests and exports running now, then leave as `run.graceful` does —
    during an SQX step its `finally` stops the worker; during a Python step none is up."""
    _RUNNING["stop"] = True       # the tests still queued in the pool never start
    for proc in list(CHILDREN):
        proc.kill()
    launcher.graceful(signum, frame)


def floored(argv: list[str]) -> tuple[int, str]:
    """`command`, started only while `jobs.FLOOR_GB` of RAM is free or nothing else of the
    chain runs — the python lane's own rule, which the chain's tests do not pass through."""
    while True:
        if _RUNNING["stop"]:
            return 1, "cancelado"
        with _GATE:
            free = psutil.virtual_memory().available / 1e9
            if free >= jobs.FLOOR_GB or not _RUNNING["n"]:
                _RUNNING["n"] += 1
                break
        time.sleep(5)
    try:
        return command(argv)
    finally:
        with _GATE:
            _RUNNING["n"] -= 1


def load(project: str, databank: str) -> list[str]:
    """What the window loads when a databank is chosen, run here and waited for.

    Returns:
        One line per piece that failed. The loader's one-shot exports go to the project's
        worker, stopped by then; run as the chain's own children because the conductor
        lane, where the window queues them, is the chain's until it ends.
    """
    failed = []
    for piece, (_lane, argv) in loader.commands(project, loader.status(project, databank)).items():
        print(f"cargando {piece} de {databank}", flush=True)
        rc, tail = command(argv)
        if rc:
            failed.append(f"cargar {piece} de {databank}: {tail}")
    return failed


def python_step(project: str, action: dict, strict: bool = False) -> list[str]:
    """Load what the step reads, then run each of its tests.

    Args:
        project: Project name.
        action: One entry of the plan's `do`.
        strict: A refused test is a failure too: the autopilot judges on what tests wrote
            (🔬 2026-10-01, step 14 judged on 0 facts after mcRetest was refused).

    Returns:
        The failures, one line each: a load or a command that ended non-zero. A test the
        rail refuses now is said and skipped, as «correr todo» lists it under «no se lanzó».
    """
    ctx = workflow.context(project)
    failed = [f for d in feeds(action["n"], ctx) for f in load(project, d)]
    if failed:
        return failed
    ctx = workflow.context(project)
    # monkeyExcess reads the panel monkey writes: last, or it is refused in the same press.
    for key in sorted(action["tests"], key=lambda k: k == "monkeyExcess"):
        why = rail.refusal(action["n"], key, ctx)
        planned = why or rail.plan(rail.BY_N[action["n"]], key, ctx, "", action.get("picked", []))
        if isinstance(planned, str):
            print(f"{key}: no se corre — {planned}", flush=True)
            if strict:
                failed.append(f"{key}: no se corrió — {planned}")
            continue
        width = 1 if key in jobs.WIDE else max(1, jobs.SLOTS // jobs.LIGHT)
        with ThreadPoolExecutor(width) as pool:
            done = list(pool.map(lambda p: (p["label"], *floored(p["argv"])), planned))
        bad = [f"{label}: {tail}" for label, rc, tail in done if rc]
        print(f"{key}: {len(done) - len(bad)} de {len(done)} bien", flush=True)
        failed += bad
    return failed


def diverged(project: str, action: dict, stale: bool) -> str:
    """Why the confirmed plan no longer holds for this step, '' when it does.

    Args:
        project: Project name.
        action: One entry of the confirmed plan's `do`, with the `state` it had then.
        stale: The chain already ran an SQX step: later steps' states move by design.
    """
    now = next(s for s in workflow.workflow(project)["steps"] if s["n"] == action["n"])
    if now["state"] == "running":
        return f"el paso {action['n']} está ahora en marcha"
    if not stale and now["state"] != action["state"]:
        return (f"el paso {action['n']} estaba «{action['state']}» al confirmar y ahora está "
                f"«{now['state']}»")
    return ""


def chain(project: str, plan: dict | None = None) -> None:
    """The whole press: the confirmed plan exactly, each SQX step re-checked for safety just
    before it starts; a step whose state moved, a refusal or a failure stops it.

    Args:
        project: Project name.
        plan: What the owner confirmed (`check`'s `plan`, with each SQX step's titles). None
            from the terminal: the plan is made here and run without a confirmation.
    """
    if plan is None:
        got = check(project)
        if not got["ok"]:
            sys.exit("no se corre:\n  " + "\n  ".join(got["reasons"]))
        plan = got["plan"]
    todo, stale, filled = plan["do"], False, set()
    for i, action in enumerate(todo):
        say(100 * i // len(todo), f"paso {action['n']} · {action['title']}")
        why = diverged(project, action, stale)
        if why:
            sys.exit(f"se para: {why}. Vuelve a mirar el raíl y pulsa otra vez.")
        if action["kind"] == "sqx":
            # own_log: anything this job ran before (a step, the loader's exports) wrote the log.
            pre = preflight.check(project, step=action["n"], own_log=i > 0, filled=filled)
            if not pre["ok"]:
                sys.exit(f"paso {action['n']}: no se lanza:\n  " + "\n  ".join(pre["reasons"]))
            if [t["title"] for t in pre["chosen"]] != action["titles"]:
                sys.exit(f"paso {action['n']}: sus tareas ya no son las confirmadas "
                         f"({', '.join(action['titles'])})")
            launcher.execute(pre, project)
            filled |= {t["output"] for t in pre["chosen"]}
            stale = True
            continue
        failed = python_step(project, action)
        if failed:
            sys.exit(f"paso {action['n']}: se para, fallaron:\n  " + "\n  ".join(failed))
    stop = plan["stop"]
    say(100, f"se para antes del paso {stop['n']}: {stop['why']}" if stop["n"] else stop["why"])


def main() -> None:
    """Run «Correr workflow» on one project; the window queues it with the plan it confirmed."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--plan", type=Path, help="el plan confirmado en la ventana (JSON)")
    a = ap.parse_args()
    signal.signal(signal.SIGTERM, cancelled)
    chain(a.project, json.loads(a.plan.read_text(encoding="utf-8")) if a.plan else None)


if __name__ == "__main__":
    main()
