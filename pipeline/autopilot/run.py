#!/usr/bin/env python3
"""Autopilot: one project's workflow, SQX and Python, judging and cutting at each judging step without stopping."""

import argparse
import csv
import json
import os
import signal
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from core import phases
from core.assetdata import AUTONOMOUS, pin_oos2
from core.paths import DATA
from pipeline.autopilot import (
    blind,
    call,
    entry,
    judge,
    plan,
    tail,
    tailrun,
    timing,
    variants,
)
from pipeline.autopilot.survivors import Done, about, mothers
from sqx import log as sqxlog
from sqx.projects import live
from sqx.worker import preflight as advance
from sqx.workflow import launchcheck as preflight
from sqx.workflow import launchsteps
from ui.daemon.launch import (
    chain,
    liverun,
)
from ui.daemon.launch import (
    run as launcher,
)
from ui.daemon.workflow import api as workflow

RUNS = DATA / "autopilot"
TAIL = 25  # lines of the traceback fallo.md keeps


def status(out: Path, line: str) -> None:
    """Overwrite estado.txt with one line, and print it: the only thing a watcher reads mid-run."""
    (out / "estado.txt").write_text(
        f"{datetime.now():%H:%M:%S} {line}\n", encoding="utf-8"
    )
    print(line, flush=True)


def mark(out: Path, n: str, state: str) -> None:
    """Append `step, state, time` to pasos.csv: `empezó`, `hecho` or `falló`; the window reads it."""
    with open(out / "pasos.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([n, state, f"{datetime.now():%H:%M:%S}"])


def summary(
    out: Path, project: str, done: list[dict], stop: tail.Stop, error: str = ""
) -> None:
    """Write resumen.md: one row per action, how long it took and what it did; and the stop.

    Short on purpose (≈ one line per step): an agent reads this file, never SQX's log.
    """
    rows = [f"| {d['n']} | {d['kind']} | {d['s']:.0f} | {d['what']} |" for d in done]
    total = sum(d["s"] for d in done)
    end = (
        f"**Falló** en el paso {error}. Detalle en `fallo.md`."
        if error
        else f"Se para antes del paso {stop['n']}: {stop['why']}."
        if stop["n"]
        else stop["why"]
    )
    (out / "resumen.md").write_text(
        "\n".join(
            [
                f"# Autopiloto · {project} · {out.name}",
                "",
                "| paso | tipo | s | qué hizo |",
                "|---|---|---|---|",
                *rows,
                "",
                f"Total {total / 60:.1f} min. {end}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if (out / "fases.csv").exists():  # absent when the first action failed
        (out / "tiempos.md").write_text(
            timing.table(out / "fases.csv"), encoding="utf-8"
        )
        with open(out / "fases.csv", newline="", encoding="utf-8") as f:
            slow = [r[3] for r in csv.reader(f) if r[2] == "fallback"]
        if slow:
            with open(out / "resumen.md", "a", encoding="utf-8") as f:
                f.write(
                    f"\nCaídas a la ruta lenta ({len(slow)}):\n"
                    + "".join(f"- {d}\n" for d in slow)
                )


def sqx_step(project: str, actions: list[dict], first: bool, filled: set[str]) -> str:
    """Consecutive SQX steps with nothing between them, in ONE start and one stop: SQX chains
    the tasks itself (build → OOS 0.19 s apart, knowhow/sqx-drive/live-chain-without-restart.md),
    where a stop and a start between them cost ~95 s.

    Returns:
        «task: before → after» per task.
    """
    if len(actions) == 1:
        pre = preflight.check(
            project, step=actions[0]["n"], own_log=not first, filled=filled
        )
    else:
        listing = preflight.tasks(project)
        assert "refuse" not in listing, f"{project}: {listing.get('refuse')}"
        titles = []
        for a in actions:
            got = launchsteps.of_step(a["n"], listing["cfx"])
            assert "refuse" not in got, f"{project} step {a['n']}: {got.get('refuse')}"
            titles += got["titles"]
        pre = preflight.check(project, titles=titles, own_log=not first, filled=filled)
    if not pre["ok"]:
        sys.exit(
            f"paso {'+'.join(a['n'] for a in actions)}: no se lanza:\n  "
            + "\n  ".join(pre["reasons"])
        )
    route = liverun if live.mine(pre["role"]) else launcher
    moved = call.again(
        lambda: route.execute(pre, project), call.keeper(pre, route is launcher)
    )
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


# Per-strategy readings that run on the survivors of step 8's cut, not on the whole build (owner,
# 2026-10-01). monkeyExcess leaves too, not run: knowhow/pipeline/monkeyexcess-after-the-cut.md
AFTER_CUT = {"8": ["monkey", "monkeyExcess", "entryQuality"]}


def after_cut(actions: list[dict], cfg: dict) -> list[dict]:
    """Move AFTER_CUT's tests out of their step's Python action to a Python action right after
    that step's judge, marked `cut` so the loop hands it the surviving strategies — except a
    test a rule of that step in `criteria.yaml` names (`<test>.…`): it is judged, so it runs
    before the judge, on everyone."""
    out, late = [], {}
    for a in actions:
        judged = {
            fact.split(".")[0]
            for fact in judge.criteria.reads(
                cfg["steps"].get(a["n"], {}).get("rules") or []
            )
        }
        moved = [
            k
            for k in AFTER_CUT.get(a["n"], [])
            if a["kind"] == "python" and k in a["tests"] and k not in judged
        ]
        if moved:
            late[a["n"]] = {
                "n": a["n"],
                "title": a["title"],
                "kind": "python",
                "tests": [k for k in moved if k != "monkeyExcess"],
                "cut": True,
            }
            a = {**a, "tests": [k for k in a["tests"] if k not in moved]}
            if not a["tests"]:
                continue
        out.append(a)
        if a["kind"] == "judge" and a["n"] in late and late[a["n"]]["tests"]:
            out.append(late.pop(a["n"]))
    return out


def autopilot(
    project: str,
    out: Path,
    own_log: bool = False,
    on_live: bool = False,
    given: tail.Given = tail.NOTHING,
) -> None:
    """Plan from the rail, then run every action in order; the first failure ends it.

    `own_log`: this caller wrote the install's log of the last minutes itself, so it is no
    sign of anyone else (`advance.busy`); the lock, the port and a live process still refuse.
    `on_live`: one GUI session (`sqx.projects.live`) for every SQX step, started here and
    stopped at the end, its start and stop timed as rows of their own.
    `given`: the tail's inputs (`tail.inputs`); from step 17 on the actions are `tailrun`'s.
    """
    where = advance.where(project)
    if "refuse" in where:
        sys.exit(where["refuse"])
    busy = advance.busy(where["role"], project, own_log)
    if busy:
        sys.exit("el worker no está libre:\n  " + "\n  ".join(busy))
    cfg = judge.settings()
    data = plan.reopen(workflow.workflow(project), out)
    todo = plan.plan(data, given)
    plan.scanned(data["asset"], todo["do"])
    for skip in todo.get("skipped", []):
        print(f"paso {skip['n']} saltado: {skip['why']}", flush=True)
    (out / "plan.json").write_text(
        json.dumps(todo, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    done, filled, ran_sqx, bad, failed_at, t0, logs = (
        [],
        set(),
        own_log,
        None,
        "",
        time.time(),
        sqxlog.mark(advance.WORKERS[where["role"]]["path"]),
    )
    actions = after_cut(merged(todo["do"]), cfg)
    if on_live:
        began = time.monotonic()
        try:
            live.start(where["role"], project)
        except BaseException as failed:  # no stop, exitapp or kill here: exitapp syncs (rule 1) and how to close it is the owner's (2026-10-13)
            status(out, entry.unstarted(where["role"], failed))
            raise
        done.append(
            {
                "n": "-",
                "kind": "arranque",
                "s": time.monotonic() - began,
                "what": "sesión GUI del custodio",
            }
        )
        phases.row("accion", "- arranque", done[-1]["s"])
    try:
        for i, action in enumerate(actions):
            status(
                out, f"[{i + 1}/{len(actions)}] paso {action['n']} · {action['kind']}"
            )
            began, empty, t0 = (
                time.monotonic(),
                False,
                time.time(),
            )  # t0: this action's start, what `close` sets a log aside by
            mark(out, action["n"], "empezó")
            if action["kind"] == "sqx":
                if action["n"] == "19":  # the WFM reads oos2: the ledger's door first
                    blind.admit(project, "19")
                what = sqx_step(project, action["steps"], not ran_sqx, filled)
                # A build stopped on its time cap (`buildcap`) skips the OOS: it runs now, alone.
                ns = {s["n"] for s in action["steps"]}
                left = [
                    a
                    for a in plan.plan(workflow.workflow(project), given)["do"]
                    if a["kind"] == "sqx" and a["n"] in ns
                ]
                if left:
                    what += " · " + sqx_step(project, left, False, filled)
            elif action["kind"] == "variants":
                left = mothers(
                    project, where["role"], cfg, action["n"]
                )  # nobody left: a clean end
                what = variants.run(project, where["role"], set(left["strategy"]))
            elif action["kind"] in tailrun.KINDS:
                what = tailrun.run(action, project, where["role"], out, cfg)
            elif action["kind"] == "python":
                if action.get(
                    "cut"
                ):  # the strategies left in the databank this step cut, by name
                    action["picked"] = sorted(
                        judge.population(
                            project, cfg["steps"][action["n"]]["cut"], where["role"]
                        )["strategy"]
                    )
                failed = chain.python_step(
                    project, action, strict=True, tell=lambda line: status(out, line)
                )
                if failed:
                    sys.exit(f"paso {action['n']}: fallaron:\n  " + "\n  ".join(failed))
                what = ", ".join(action["tests"])
            else:
                got = judge.judge(
                    project,
                    action["n"],
                    where["role"],
                    out / f"paso-{action['n']}",
                    cfg,
                    action.get("segment"),
                )
                what = f"{got['hechos']} hechos; {got['corte']}"
                empty = (
                    got.get("after") == 0
                )  # the cut left nobody: a clean end, after the row
            ran_sqx = ran_sqx or action["kind"] in (
                "sqx",
                "neighbours",
                "variants",
            )  # T1 and the factory wrote the log too
            done.append(
                {
                    "n": action["n"],
                    "kind": action["kind"],
                    "s": time.monotonic() - began,
                    "what": what,
                }
            )
            phases.row("accion", f"{action['n']} {action['kind']}", done[-1]["s"])
            mark(out, action["n"], "hecho")
            summary(out, project, done, todo["stop"])
            if empty:
                raise Done(
                    f"el paso {action['n']} no dejó ninguna superviviente: no queda nada que seguir"
                )
    except Done as end:  # a clean stop decided while running: nothing failed
        todo["stop"] = {"n": None, "why": str(end)}
        summary(out, project, done, todo["stop"])
    except BaseException as failed:
        at = sum(d["n"] != "-" for d in done)
        n = (
            actions[at]["n"] if at < len(actions) else "final"
        )  # failed after the last action
        bad = (
            dict(actions[at], since=t0)
            if at < len(actions) and actions[at]["kind"] == "sqx"
            else None
        )
        (out / "fallo.md").write_text(
            f"# Fallo en el paso {n}\n\n{failed}\n\n```\n"
            + "".join(traceback.format_exc().splitlines(keepends=True)[-TAIL:])
            + "```\n"
            + sqxlog.causes(advance.WORKERS[where["role"]]["path"], logs),
            encoding="utf-8",
        )
        summary(out, project, done, todo["stop"], error=(failed_at := n))
        mark(out, n, "falló")
        status(
            out,
            f"FALLO en el paso {n}: {str(failed).splitlines()[0] if str(failed) else ''}",
        )
        raise
    finally:
        if on_live and live.mine(where["role"]):
            began = time.monotonic()
            with entry.told(lambda line: status(out, line)):
                liverun.close(where["role"], project, bad)
            done.append(
                {
                    "n": "-",
                    "kind": "parada",
                    "s": time.monotonic() - began,
                    "what": "parada y export final",
                }
            )
            phases.row("accion", "- parada", done[-1]["s"])
            summary(
                out, project, done, todo["stop"], error=failed_at
            )  # the stop's row must not erase «Falló»
    status(out, f"FIN · {len(done)} acciones · resumen en {out / 'resumen.md'}")


def main() -> None:
    """Run the autopilot on one project; its folder is AlgoData/autopilot/<P>/<stamp>/."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--plan", action="store_true", help="solo escribe el plan, no corre nada"
    )
    ap.add_argument(
        "--own-log",
        action="store_true",
        help="el log reciente del worker lo escribiste tú: no esperes sus 15 min",
    )
    ap.add_argument(
        "--restart",
        action="store_true",
        help="marcha atrás: SQX arranca y para en cada paso (lo normal es una sola sesión)",
    )
    ap.add_argument("--smoke", action="store_true", help="prueba funcional de un Test_")
    tail.flags(ap)
    a = ap.parse_args()
    judge.smoke(a.project, a.smoke)
    os.environ[AUTONOMOUS] = (
        "1"  # D4 (owner, 2026-10-04): oos2's door binds this run and its subprocesses
    )
    given = tail.inputs(a, judge.settings())
    if a.plan:
        print(
            json.dumps(
                plan.plan(workflow.workflow(a.project), given),
                indent=1,
                ensure_ascii=False,
            )
        )
        return
    pin_oos2(about(a.project)["symbol"])  # T-2: the roll cannot move it mid-run
    entry.alone(w["role"]) if "role" in (w := advance.where(a.project)) else sys.exit(
        w["refuse"]
    )  # before the run's folder: a refused run leaves none
    out = RUNS / a.project / f"{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    (
        out / judge.SMOKE_MARK
    ).touch() if a.smoke else None  # the store stamps its verdicts as smoke
    os.environ[phases.ENV] = str(out / "fases.csv")
    print(f"carpeta del run: {out}", flush=True)
    signal.signal(signal.SIGTERM, chain.cancelled)
    autopilot(a.project, out, a.own_log, not a.restart, given)


if __name__ == "__main__":
    main()
