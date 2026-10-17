#!/usr/bin/env python3
"""«Lanzar en SQX»: switch on one task or one step's tasks, start the worker once, wait for SQX, stop."""

import argparse
import signal
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from core.datapaths import template_runs
from core.phases import phase
from ledger import steprows
from sqx import log as sqxlog
from sqx.projdisk import INTERRUPTED, compare, counts, restore, snapshot
from sqx.projects import crosstfload, stage
from sqx.templates.registry import RUN_COLUMNS, append
from sqx.worker import guard as workerguard
from sqx.worker import preflight as advance
from sqx.worker import session
from sqx.worker.session import assets, graceful, say
from ui.daemon.launch import configure, preflight


def record(pre: dict[str, Any], project: str, built: int) -> str:
    """A build's row in runs.csv, as the template-run skill writes it by hand."""
    template = Path(pre["row"].get("template") or "").parent.name
    if not template:
        return "sin plantilla en registry.csv: runs.csv no se toca"
    row = {
        "template": template,
        "symbol": pre["row"]["symbol"],
        "timeframe": pre["row"]["timeframe"],
        "project": project,
        "date": date.today().isoformat(),
        "strategies_built": str(built),
    }
    what = append(
        template_runs(), RUN_COLUMNS, row, ("template", "symbol", "timeframe")
    )
    return f"runs.csv: {what} {template} en {row['symbol']} {row['timeframe']}"


def execute(pre: dict[str, Any], project: str) -> dict[str, tuple[int, int]]:
    """The run itself, once a preflight passed: rule 5, copy, stage, start, watch, stop.

    Args:
        pre: What `preflight.check` returned, ok.
        project: Project name.

    Returns:
        The output databanks' counts before and after, by title: {title: (before, after)}.
    """
    role, chosen = pre["role"], pre["chosen"]
    titles = [t["title"] for t in chosen]
    top = advance.WORKERS[role][
        "path"
    ]  # through advance: one table the tests can point
    port = advance.WORKERS[role]["port"]
    workerguard.refuse_if_up(
        role, top, port
    )  # before any copy; again right before start
    say(2, f"comprobando {pre['row']['symbol']} (regla 5)")
    with phase("assets"):
        assets(pre["row"]["symbol"])
    say(5, "copiando el proyecto")
    with phase("snapshot"):
        kept, before = snapshot(pre["cfx"].parent), counts(pre["cfx"].parent)
    for bank in pre.get("fill", []):  # CrossTF_Input (10.5), CrossTF_Mothers (13)
        say(9, f"llenando {bank}")
        with phase("fill", bank):
            print(crosstfload.fill(bank, project, role), flush=True)
        before = counts(
            pre["cfx"].parent
        )  # what the fill wrote is not a loss of the run
    with phase(
        "configure"
    ):  # after the fill: the configurator reads the input population
        off = configure.run(pre, say)  # a silenced MC Retest stays off
    titles = [t for t in titles if t not in off]
    titles += (
        crosstfload.separate_titles(pre["cfx"]) if "CrossTF" in titles else []
    )  # the per-timeframe tasks
    say(10, f"activando solo {', '.join(titles)}")
    stage.just(pre["cfx"], titles)
    say(15, f"arrancando el {preflight.ROLES.get(role, role)}")
    got = session.run(
        role,
        project,
        "sus databanks pueden estar a medio escribir; no se sigue",
        session.Hooks(
            phase=lambda n: phase(n, " + ".join(titles)) if n == "sqx" else phase(n),
            launched=lambda: say(60, f"{', '.join(titles)} lanzada(s)"),
        ),
    )
    run, began, started_at = got["run"], got["began"], got["started_at"]
    outputs = {t["output"] for t in chosen}
    with phase("restore"):
        back = restore(
            pre["cfx"].parent,
            kept,
            before,
            outputs,
            sqxlog.matching(top, started_at, INTERRUPTED),
        )
    if back:
        print(
            f"restauradas desde la copia {len(back)} estrategia(s) que el sync de SQX borró "
            f"al pararse (Cannot process strategy): {', '.join(back)}",
            flush=True,
        )
    with phase("compare"):
        after = counts(pre["cfx"].parent)
        print(compare(before, after, outputs, kept), flush=True)
    for t in chosen:
        if t["type"] == preflight.BUILD:
            print(record(pre, project, after.get(t["output"], 0)), flush=True)
            print(
                steprows.log_build(project, pre["cfx"].parent / "log", began),
                flush=True,
            )
    moved = {
        t["title"]: (before.get(t["output"], 0), after.get(t["output"], 0))
        for t in chosen
    }
    say(
        100,
        " · ".join(
            f"«{t}»: {run['events'].get(t, '?')}; {n0} → {n1}"
            for t, (n0, n1) in moved.items()
        ),
    )
    return moved


def launch(
    project: str, titles: str | Sequence[str] = (), step: str = ""
) -> dict[str, tuple[int, int]]:
    """The whole sequence, re-checking the preflight first: two clicks cannot race it.

    Args:
        project: Project name.
        titles: One task title or several; ignored when `step` is given.
        step: A workflow step: all its tasks, together, in one start of the worker.
    """
    pre = preflight.check(project, titles, step)
    if not pre["ok"]:
        sys.exit("no se lanza:\n  " + "\n  ".join(pre["reasons"]))
    return execute(pre, project)


def main() -> None:
    """Run one task, several, or one step's tasks; the window queues it on the conductor lane."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--task",
        action="append",
        default=[],
        help="el título de la tarea, como lo enseña SQX (se puede repetir)",
    )
    ap.add_argument(
        "--step", default="", help="un paso del workflow: todas sus tareas juntas"
    )
    a = ap.parse_args()
    signal.signal(signal.SIGTERM, graceful)
    if not a.task and not a.step:
        ap.error("--task o --step")
    launch(a.project, a.task, a.step)


if __name__ == "__main__":
    main()
