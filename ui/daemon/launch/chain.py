#!/usr/bin/env python3
"""«Correr workflow»: every pending step in WORKFLOW.md's order, SQX and Python, up to the next decision."""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil

from core.paths import ROOT
from sqx.projects import stage
from ui.daemon import jobs
from ui.daemon.advance.run import say
from ui.daemon.launch import chaincheck, preflight
from ui.daemon.launch import run as launcher
from ui.daemon.loader import afterrun, state as loader
from ui.daemon.runner import batch
from ui.daemon.workflow import api as workflow
from ui.daemon.workflow import run as rail

TAIL = 4    # lines of a failed command's output the chain's log keeps
# The python lane's rules (`jobs.FLOOR_GB`, `jobs.SLOTS`): a command starts when its weight fits
# the cores and its RAM estimate fits above the floor, or when nothing else of the chain runs.
# "gb" and "cores" are what the running commands reserved (a child has not eaten its RAM yet
# when the next one measures the free figure).
_RUNNING = {"n": 0, "stop": False, "gb": 0.0, "cores": 0}
GB_PER_WEIGHT = 0.25    # 🔬 2026-09-27: a light study (weight 3) is 0.2-0.7 GB; ponytail: flat per unit
CHILDREN: set[subprocess.Popen] = set()     # the tests and exports running now
_GATE = threading.Lock()


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


def floored(argv: list[str], key: str = "", picked: int | None = None) -> tuple[int, str]:
    """`command`, started only while its weight (`jobs.weight`) fits the core budget and its RAM
    (`GB_PER_WEIGHT` a unit) fits above `jobs.FLOOR_GB`, counting what the running ones
    reserved; or when nothing else of the chain runs, so a heavy one is never starved.

    Args:
        argv: The command.
        key: The test's study key; light (`jobs.LIGHT`) when empty.
        picked: Weight of one command of a test run once per picked survivor (`jobs.PICKED`).
    """
    w = jobs.weight({"study": key, "weight": picked})
    if key in jobs.WIDE and picked is None:
        w = jobs.SLOTS       # it fans out over every core: alone, light ones wait for it
    gb = w * GB_PER_WEIGHT
    while True:
        if _RUNNING["stop"]:
            return 1, "cancelado"
        with _GATE:
            free = psutil.virtual_memory().available / 1e9
            if not _RUNNING["n"] or (free - _RUNNING["gb"] - gb >= jobs.FLOOR_GB
                                     and _RUNNING["cores"] + w <= jobs.SLOTS):
                _RUNNING["n"] += 1
                _RUNNING["gb"] += gb
                _RUNNING["cores"] += w
                break
        time.sleep(1)       # psutil and a lock: cheap, so a freed slot is taken within a second
    try:
        return command(argv)
    finally:
        with _GATE:
            _RUNNING["n"] -= 1
            _RUNNING["gb"] -= gb
            _RUNNING["cores"] -= w


def load(project: str, databank: str) -> list[str]:
    """What the window loads when a databank is chosen, run here and waited for.

    Returns:
        One line per piece that failed. The one-shot exports run as the chain's own children
        (the conductor lane is its until it ends); the MC Retest trades nobody reads are skipped.
    """
    failed, done = [], []
    for piece, (_lane, argv) in loader.commands(project, loader.status(project, databank)).items():
        if piece == "trades" and databank in afterrun.UNREAD_TRADES: continue    # owner, 2026-10-01
        if piece == "trades" and "--exports" in done and (
                loader.status(project, databank)["pieces"]["trades"]["state"] == "fresh"):
            continue            # the harvest's --exports wrote them
        print(f"cargando {piece} de {databank}", flush=True)
        rc, tail = command(argv)
        if piece == "harvest": done = argv
        if rc:
            failed.append(f"cargar {piece} de {databank}: {tail}")
    return failed


def python_step(project: str, action: dict, strict: bool = False,
                tell: Callable[[str], None] | None = None) -> list[str]:
    """Load what the step reads, then run each of its tests.

    Args:
        project: Project name.
        action: One entry of the plan's `do`.
        strict: A refused test is a failure too: the autopilot judges on what tests wrote
            (🔬 2026-10-01, step 14 judged on 0 facts after mcRetest was refused).
        tell: Where to say a batch that lost some strategies but exited 0 («FALLARON n de N: …»):
            the autopilot passes the writer of its `estado.txt`; the window's chain passes none
            and the line goes to the job's own log.

    Returns:
        The failures, one line each: a load or a command that ended non-zero. A test the
        rail refuses now is said and skipped, as «correr todo» lists it under «no se lanzó».
    """
    ctx = workflow.context(project)
    failed = [f for d in feeds(action["n"], ctx) for f in load(project, d)]
    if failed:
        return failed
    ctx = workflow.context(project)

    def one(key: str) -> list[str]:
        """Plan one key of the step; the refusal printed, or its planned commands."""
        why = rail.refusal(action["n"], key, ctx)
        planned = why or rail.plan(rail.BY_N[action["n"]], key, ctx, "", action.get("picked", []))
        if isinstance(planned, str):
            print(f"{key}: no se corre — {planned}", flush=True)
            return [f"{key}: no se corrió — {planned}"] if strict else []
        planned = batch.fold(planned)     # one process for the one-strategy plans of a light study
        weight = jobs.PICKED.get(key) if len(planned) > 1 else None
        with launcher.phase("test", key), ThreadPoolExecutor(jobs.width(key, len(planned))) as pool:
            done = list(pool.map(lambda p: (p["label"], *floored(p["argv"], key,
                                                                 p.get("weight") or weight)), planned))
        for _, _, tail in done:
            lost = re.search(r"FALLARON \d+ de \d+: .*", tail)
            if lost:
                line = f"{key}: {lost.group(0)}"
                tell(line) if tell else print(line, flush=True)
        bad = [f"{label}: {tail}" for label, rc, tail in done if rc]
        print(f"{key}: {len(done) - len(bad)} de {len(done)} bien", flush=True)
        return bad

    # The tests of a step are independent and run together, each command held by `floored`'s
    # weights — except monkeyExcess, which reads the panel monkey writes: after all the others.
    first = [k for k in action["tests"] if k != "monkeyExcess"]
    with ThreadPoolExecutor(max(1, len(first))) as pool:
        results = list(pool.map(one, first))
    if "monkeyExcess" in action["tests"]:
        results.append(one("monkeyExcess"))
    return failed + [f for r in results for f in r]


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
        got = chaincheck.check(project)
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
