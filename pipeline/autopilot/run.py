#!/usr/bin/env python3
"""Autopilot: one project's workflow, SQX and Python, judging and cutting at each judging step without stopping."""

import argparse
import json
import signal
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from core.paths import DATA
from pipeline.autopilot import judge, plan
from ui.daemon.advance import preflight as advance
from ui.daemon.launch import chain, preflight
from ui.daemon.launch import steps as launchsteps
from ui.daemon.launch import run as launcher
from ui.daemon.workflow import api as workflow

RUNS = DATA / "autopilot"
TAIL = 25   # lines of the traceback fallo.md keeps


def status(out: Path, line: str) -> None:
    """Overwrite estado.txt with one line, and print it: the only thing a watcher reads mid-run."""
    (out / "estado.txt").write_text(f"{datetime.now():%H:%M:%S} {line}\n", encoding="utf-8")
    print(line, flush=True)


def summary(out: Path, project: str, done: list[dict], stop: dict, error: str = "") -> None:
    """Write resumen.md: one row per action, how long it took and what it did; and the stop.

    Short on purpose (≈ one line per step): an agent reads this file, never SQX's log.
    """
    rows = [f"| {d['n']} | {d['kind']} | {d['s']:.0f} | {d['what']} |" for d in done]
    total = sum(d["s"] for d in done)
    end = (f"**Falló** en el paso {error}. Detalle en `fallo.md`." if error else
           f"Se para antes del paso {stop['n']}: {stop['why']}." if stop["n"] else stop["why"])
    (out / "resumen.md").write_text("\n".join(
        [f"# Autopiloto · {project} · {out.name}", "",
         "| paso | tipo | s | qué hizo |", "|---|---|---|---|", *rows, "",
         f"Total {total / 60:.1f} min. {end}", ""]), encoding="utf-8")


def sqx_step(project: str, actions: list[dict], first: bool, filled: set[str]) -> str:
    """Consecutive SQX steps with nothing between them, in ONE start and one stop: SQX chains
    the tasks itself (build → OOS 0.19 s apart, knowhow/sqx-drive/live-chain-without-restart.md),
    where a stop and a start between them cost ~95 s.

    Returns:
        «task: before → after» per task.
    """
    if len(actions) == 1:
        pre = preflight.check(project, step=actions[0]["n"], own_log=not first, filled=filled)
    else:
        cfx = preflight.tasks(project)["cfx"]
        titles = [t for a in actions for t in launchsteps.of_step(a["n"], cfx)["titles"]]
        pre = preflight.check(project, titles=titles, own_log=not first, filled=filled)
    if not pre["ok"]:
        sys.exit(f"paso {'+'.join(a['n'] for a in actions)}: no se lanza:\n  "
                 + "\n  ".join(pre["reasons"]))
    moved = launcher.execute(pre, project)
    filled |= {t["output"] for t in pre["chosen"]}
    return " · ".join(f"{t}: {a} → {b}" for t, (a, b) in moved.items())


def merged(todo: list[dict]) -> list[dict]:
    """The plan with every run of consecutive SQX steps folded into one action («6+7»)."""
    out = []
    for a in todo:
        if a["kind"] == "sqx" and out and out[-1]["kind"] == "sqx":
            out[-1]["steps"].append(a)
            out[-1]["n"] += f"+{a['n']}"
        else:
            out.append({**a, "steps": [a]} if a["kind"] == "sqx" else a)
    return out


# Per-strategy readings outside the sequence that run on the survivors of step 8's cut, not on
# the whole build (owner, 2026-10-01: 200 of step 8's 297 s were these two on all 571).
AFTER_CUT = {"8": ["profitShape", "entryQuality"]}


def after_cut(actions: list[dict]) -> list[dict]:
    """Move AFTER_CUT's tests out of their step's Python action to a Python action right after
    that step's judge, marked `cut` so the loop hands it the surviving strategies."""
    out, late = [], {}
    for a in actions:
        moved = [k for k in AFTER_CUT.get(a["n"], [])
                 if a["kind"] == "python" and k in a["tests"]]
        if moved:
            late[a["n"]] = {"n": a["n"], "title": a["title"], "kind": "python", "tests": moved,
                            "cut": True}
            a = {**a, "tests": [k for k in a["tests"] if k not in moved]}
            if not a["tests"]:
                continue
        out.append(a)
        if a["kind"] == "judge" and a["n"] in late:
            out.append(late.pop(a["n"]))
    return out


def survivors(project: str, n: str, role: str, cfg: dict) -> list[str]:
    """The strategies left in the databank step `n` cut (`criteria.yaml`), by name."""
    return sorted(judge.population(project, cfg["steps"][n]["cut"], role)["strategy"])


def autopilot(project: str, out: Path, own_log: bool = False) -> None:
    """Plan from the rail, then run every action in order; the first failure ends it.

    `own_log`: this caller wrote the install's log of the last minutes itself, so it is no
    sign of anyone else (`advance.busy`); the lock, the port and a live process still refuse.
    """
    where = advance.where(project)
    if "refuse" in where:
        sys.exit(where["refuse"])
    busy = advance.busy(where["role"], project, own_log)
    if busy:
        sys.exit("el worker no está libre:\n  " + "\n  ".join(busy))
    cfg = judge.settings()
    todo = plan.plan(workflow.workflow(project))
    (out / "plan.json").write_text(json.dumps(todo, indent=1, ensure_ascii=False),
                                   encoding="utf-8")
    done, filled, ran_sqx = [], set(), own_log
    actions = after_cut(merged(todo["do"]))
    try:
        for i, action in enumerate(actions):
            status(out, f"[{i + 1}/{len(actions)}] paso {action['n']} · {action['kind']}")
            began = time.monotonic()
            if action["kind"] == "sqx":
                what = sqx_step(project, action["steps"], not ran_sqx, filled)
                ran_sqx = True
                # A build stopped on its time cap does not go on to the OOS (`buildcap`): the
                # rail still shows those steps to do, so they run now, in a start of their own.
                ns = {s["n"] for s in action["steps"]}
                left = [a for a in plan.plan(workflow.workflow(project))["do"]
                        if a["kind"] == "sqx" and a["n"] in ns]
                if left:
                    what += " · " + sqx_step(project, left, False, filled)
            elif action["kind"] == "python":
                if action.get("cut"):
                    action["picked"] = survivors(project, action["n"], where["role"], cfg)
                failed = chain.python_step(project, action, strict=True)
                if failed:
                    sys.exit(f"paso {action['n']}: fallaron:\n  " + "\n  ".join(failed))
                what = ", ".join(action["tests"])
            else:
                got = judge.judge(project, action["n"], where["role"],
                                  out / f"paso-{action['n']}", cfg)
                what = f"{got['hechos']} hechos; {got['corte']}"
            done.append({"n": action["n"], "kind": action["kind"],
                         "s": time.monotonic() - began, "what": what})
            summary(out, project, done, todo["stop"])
    except BaseException as failed:
        n = actions[len(done)]["n"]
        (out / "fallo.md").write_text(
            f"# Fallo en el paso {n}\n\n{failed}\n\n```\n"
            + "".join(traceback.format_exc().splitlines(keepends=True)[-TAIL:]) + "```\n",
            encoding="utf-8")
        summary(out, project, done, todo["stop"], error=n)
        status(out, f"FALLO en el paso {n}: {str(failed).splitlines()[0] if str(failed) else ''}")
        raise
    status(out, f"FIN · {len(done)} acciones · resumen en {out / 'resumen.md'}")


def main() -> None:
    """Run the autopilot on one project; its folder is AlgoData/autopilot/<P>/<stamp>/."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--plan", action="store_true", help="solo escribe el plan, no corre nada")
    ap.add_argument("--own-log", action="store_true",
                    help="el log reciente del worker lo escribiste tú: no esperes sus 15 min")
    a = ap.parse_args()
    if a.plan:
        print(json.dumps(plan.plan(workflow.workflow(a.project)), indent=1, ensure_ascii=False))
        return
    out = RUNS / a.project / f"{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    print(f"carpeta del run: {out}", flush=True)
    signal.signal(signal.SIGTERM, chain.cancelled)
    autopilot(a.project, out, a.own_log)


if __name__ == "__main__":
    main()
