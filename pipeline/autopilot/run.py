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


def sqx_step(project: str, action: dict, first: bool, filled: set[str]) -> str:
    """One SQX step, as the window's chain runs it: preflight, then one start and one stop.

    Returns:
        «task: before → after» per task.
    """
    pre = preflight.check(project, step=action["n"], own_log=not first, filled=filled)
    if not pre["ok"]:
        sys.exit(f"paso {action['n']}: no se lanza:\n  " + "\n  ".join(pre["reasons"]))
    moved = launcher.execute(pre, project)
    filled |= {t["output"] for t in pre["chosen"]}
    return " · ".join(f"{t}: {a} → {b}" for t, (a, b) in moved.items())


def autopilot(project: str, out: Path) -> None:
    """Plan from the rail, then run every action in order; the first failure ends it."""
    where = advance.where(project)
    if "refuse" in where:
        sys.exit(where["refuse"])
    busy = advance.busy(where["role"], project)
    if busy:
        sys.exit("el worker no está libre:\n  " + "\n  ".join(busy))
    cfg = judge.settings()
    todo = plan.plan(workflow.workflow(project))
    (out / "plan.json").write_text(json.dumps(todo, indent=1, ensure_ascii=False),
                                   encoding="utf-8")
    done, filled, ran_sqx = [], set(), False
    try:
        for i, action in enumerate(todo["do"]):
            status(out, f"[{i + 1}/{len(todo['do'])}] paso {action['n']} · {action['kind']}")
            began = time.monotonic()
            if action["kind"] == "sqx":
                what = sqx_step(project, action, not ran_sqx, filled)
                ran_sqx = True
            elif action["kind"] == "python":
                failed = chain.python_step(project, action)
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
        n = todo["do"][len(done)]["n"]
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
    a = ap.parse_args()
    if a.plan:
        print(json.dumps(plan.plan(workflow.workflow(a.project)), indent=1, ensure_ascii=False))
        return
    out = RUNS / a.project / f"{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    print(f"carpeta del run: {out}", flush=True)
    signal.signal(signal.SIGTERM, chain.cancelled)
    autopilot(a.project, out)


if __name__ == "__main__":
    main()
