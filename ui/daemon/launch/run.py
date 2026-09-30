#!/usr/bin/env python3
"""«Lanzar en SQX»: switch on one task or one step's tasks, start the worker once, wait for SQX, stop."""

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from core import worker
from core.datapaths import template_runs
from core.paths import ROOT
from sqx.projects import crosstfload, stage
from sqx.templates.registry import RUN_COLUMNS, append
from ui.daemon import workerguard
from ui.daemon.advance import preflight as advance, sqxlog
from ui.daemon.advance.run import ready, say, watch
from ui.daemon.launch import configure, preflight

# The project folder before the start (hard rule 1), without log/; deleted once the counts match.
SNAPSHOTS = advance.DISCARDS.parent / "snapshots"


def assets(symbol: str) -> None:
    """Hard rule 5: `python3 -m core.assets <SYMBOL>` before touching a project; stop on non-zero."""
    got = subprocess.run([sys.executable, "-m", "core.assets", symbol], capture_output=True,
                         text=True)
    print(got.stdout.strip(), flush=True)
    if got.returncode:
        sys.exit(f"core.assets {symbol} salió con {got.returncode}: no se lanza nada\n"
                 f"{got.stderr.strip()}")


def counts(folder: Path) -> dict[str, int]:
    """.sqx per databank of one project folder, keyed as SQX names them (the folder's name)."""
    banks = folder / "databanks"
    return {d.name: len(list(d.glob("*.sqx"))) for d in sorted(banks.iterdir()) if d.is_dir()} \
        if banks.is_dir() else {}


def snapshot(folder: Path) -> Path:
    """Copy the project aside, `log/` left out (knowhow/databanks/snapshot-before-restart.md);
    named `.partial` until complete, and a copy cut short (a cancel) is removed."""
    to = SNAPSHOTS / folder.name / f"{datetime.now():%Y%m%d-%H%M%S}"
    partial = to.with_name(to.name + ".partial")
    partial.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(folder, partial, ignore=shutil.ignore_patterns("log"))
    except BaseException:       # SystemExit from a SIGTERM too
        shutil.rmtree(partial, ignore_errors=True)
        raise
    return partial.rename(to)


def compare(before: dict, after: dict, output: str | set[str], kept: Path) -> str:
    """The line on what the run did to the databanks; the snapshot goes only when nothing fell.

    Args:
        before: `counts` before the start.
        after: `counts` after the stop.
        output: The tasks' own output databank(s), which they may clear by configuration.
        kept: The snapshot.

    Returns:
        The line to print. A databank no task of the run writes that lost files keeps the
        snapshot (hard rule 1: a sync deletes what is not in memory).
    """
    outputs = {output} if isinstance(output, str) else output
    fell = {d: (n, after.get(d, 0)) for d, n in before.items()
            if d not in outputs and after.get(d, 0) < n}
    if fell:
        return ("⚠️ bajaron databanks que la tarea no escribe: "
                + ", ".join(f"{d} {a} → {b}" for d, (a, b) in fell.items())
                + f". La copia se queda en {kept}")
    shutil.rmtree(kept)
    return "ningún otro databank bajó; la copia de seguridad se ha borrado"


INTERRUPTED = re.compile(r"Cannot process strategy '([^']+)'")


def restore(project_dir: Path, kept: Path, before: dict, outputs: set[str],
            lines: list[str]) -> list[str]:
    """Put back the strategies SQX's own sync race deleted, from the pre-run snapshot.

    🔬 2026-09-29: the stop's shutdown sync ran while a periodic sync of «Retest Markets -
    Family» held a strategy's lock; SQX logged «Cannot process strategy 'Strategy 9.11.67'»
    (InterruptedException) and the periodic sync then counted it removed and deleted its
    file. Only a strategy named in such a line, missing from a databank no task of the run
    writes, is copied back — the worker is stopped, so nothing rewrites it.

    Args:
        project_dir: The project's folder on the install.
        kept: The snapshot of it taken before the start.
        before: `counts` before the start.
        outputs: The run's own output databanks.
        lines: The install log's lines written since the start.

    Returns:
        «databank/strategy» per file restored.
    """
    named = {m.group(1) for line in lines for m in [INTERRUPTED.search(line)] if m}
    back = []
    for bank in (b for b in before if b not in outputs):
        for f in (kept / "databanks" / bank).glob("*.sqx") if named else []:
            live = project_dir / "databanks" / bank / f.name
            if f.stem in named and not live.exists():
                shutil.copy2(f, live)
                back.append(f"{bank}/{f.stem}")
    return back


def record(pre: dict, project: str, built: int) -> str:
    """A build's row in runs.csv, as the template-run skill writes it by hand."""
    template = Path(pre["row"].get("template") or "").parent.name
    if not template:
        return "sin plantilla en registry.csv: runs.csv no se toca"
    row = {"template": template, "symbol": pre["row"]["symbol"],
           "timeframe": pre["row"]["timeframe"], "project": project,
           "date": date.today().isoformat(), "strategies_built": str(built)}
    what = append(template_runs(), RUN_COLUMNS, row, ("template", "symbol", "timeframe"))
    return f"runs.csv: {what} {template} en {row['symbol']} {row['timeframe']}"


def graceful(_signum: int, _frame: object) -> None:
    """SIGTERM from the daemon's cancel: raise, so every `finally` stops the worker it started —
    without the export after the stop, which could outlast the daemon's grace period."""
    os.environ["ALGO_NO_EXPORT"] = "1"
    raise SystemExit("cancelado desde la ventana: se para el worker antes de salir")


def execute(pre: dict, project: str) -> dict:
    """The run itself, once a preflight passed: rule 5, copy, stage, start, watch, stop.

    Args:
        pre: What `preflight.check` returned, ok.
        project: Project name.

    Returns:
        The output databanks' counts before and after, by title: {title: (before, after)}.
    """
    role, chosen = pre["role"], pre["chosen"]
    titles = [t["title"] for t in chosen]
    top = advance.WORKERS[role]["path"]   # through advance: one table the tests can point
    port = advance.WORKERS[role]["port"]
    workerguard.refuse_if_up(role, top, port)      # before any copy; again right before start
    say(2, f"comprobando {pre['row']['symbol']} (regla 5)")
    assets(pre["row"]["symbol"])
    say(5, "copiando el proyecto")
    kept, before = snapshot(pre["cfx"].parent), counts(pre["cfx"].parent)
    off = configure.run(pre, say)               # a silenced MC Retest stays off
    titles = [t for t in titles if t not in off]
    for bank in pre.get("fill", []):             # CrossTF_Input (10.5), CrossTF_Mothers (13)
        say(9, f"llenando {bank}")
        print(crosstfload.fill(bank, project, role), flush=True)
        before = counts(pre["cfx"].parent)      # what the fill wrote is not a loss of the run
    titles += crosstfload.separate_titles(pre["cfx"]) if "CrossTF" in titles else []   # D1/MT4
    say(10, f"activando solo {', '.join(titles)}")
    stage.just(pre["cfx"], titles)
    say(15, f"arrancando el {preflight.ROLES.get(role, role)}")
    workerguard.refuse_if_up(role, top, port)
    try:
        worker.start(role)          # inside: a start that fails half-way is stopped too
        workerguard.mark(role, project)
        ready(project, role)
        offsets = sqxlog.mark(top)
        started_at = dict(offsets)        # `watch` advances `offsets`; the restore reads all
        reply = worker.call(f"-project action=start name={project}", role)
        if "rror" in reply or "Cannot start" in reply:     # «Project has unresolved resources»
            sys.exit(f"SQX rechazó `action=start` de {project}: {reply.strip()}")
        say(60, f"{', '.join(titles)} lanzada(s)")
        run = watch(project, role, offsets)
    finally:
        # The job started it (refused above when it was up already), so it stops it.
        worker.stop(role)
        left = workerguard.stopped(role, top, port)
    if left:
        sys.exit(f"el {role} no se paró ({left}): sus databanks pueden estar a medio escribir; "
                 "no se sigue")
    outputs = {t["output"] for t in chosen}
    back = restore(pre["cfx"].parent, kept, before, outputs,
                   sqxlog.matching(top, started_at, INTERRUPTED))
    if back:
        print(f"restauradas desde la copia {len(back)} estrategia(s) que el sync de SQX borró "
              f"al pararse (Cannot process strategy): {', '.join(back)}", flush=True)
    after = counts(pre["cfx"].parent)
    print(compare(before, after, outputs, kept), flush=True)
    for t in chosen:
        if t["type"] == preflight.BUILD:
            print(record(pre, project, after.get(t["output"], 0)), flush=True)
    moved = {t["title"]: (before.get(t["output"], 0), after.get(t["output"], 0)) for t in chosen}
    say(100, " · ".join(f"«{t}»: {run['events'].get(t, '?')}; {n0} → {n1}"
                        for t, (n0, n1) in moved.items()))
    return moved


def launch(project: str, titles: str | list[str] = (), step: str = "") -> dict:
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
    ap.add_argument("--task", action="append", default=[],
                    help="el título de la tarea, como lo enseña SQX (se puede repetir)")
    ap.add_argument("--step", default="", help="un paso del workflow: todas sus tareas juntas")
    a = ap.parse_args()
    signal.signal(signal.SIGTERM, graceful)
    if not a.task and not a.step:
        ap.error("--task o --step")
    launch(a.project, a.task, a.step)


if __name__ == "__main__":
    main()
