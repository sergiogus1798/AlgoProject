#!/usr/bin/env python3
"""«Continuar workflow»: copy the discards aside, cut the databank, start the next task and wait."""

import argparse
import os
import shutil
import signal
import sys
import time
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from core import worker
from ledger import record
from sqx.curate import apply_verdict
from sqx.projects import crosstfload, stage
from ui.daemon import progress, workerguard
from ui.daemon.advance import buildcap, preflight, sqxlog
from ui.daemon.filters import discards, ledgerrow
from ui.daemon.launch import configure

POLL, READY_TRIES = 10, 60   # s between two `action=status`; × POLL, the CLI's «not ready» ~20 s
START_WITHIN = 120  # s after `action=start` for «Starting project '<P>'» to reach the log
# No run lasts this long (a 1,000-variant WFC took hours): past it the job is stuck, and stops.
MAX_HOURS = 48


def say(pct: int, line: str) -> None:
    """One PROGRESS line, the only thing the job list reads from here."""
    print(f"PROGRESS {pct} {line}", flush=True)


def verdict(pre: dict, folder: Path) -> tuple[Path, int]:
    """Copy each discarded .sqx into `folder` and write the verdict that drops them.

    Args:
        pre: What `preflight.check` returned, ok.
        folder: `AlgoData/projects/discards/<P>/<D>/<stamp>/` (owner, Q7), created here.

    Returns:
        The verdict.csv (strategy, verdict DESCARTAR, identity, reason = the filter's
        expression) and how many files it names. Raises SystemExit, nothing copied, when a
        discarded identity is no longer in the databank: the filter judged another population.
    """
    by_id = preflight.by_identity(pre["source"])
    why = {r["identity"]: r["expression"] for r in pre["discards"]}
    gone = sorted(set(why) - set(by_id))
    if gone:
        sys.exit(f"{len(gone)} de {len(why)} descartes ya no están en {pre['source'].name}: el "
                 "databank cambió desde el filtro. Vuelve a filtrar; no se ha tocado nada.")
    folder.mkdir(parents=True)
    rows = []
    for identity, reason in why.items():
        for f in by_id[identity]:
            shutil.copy2(f, folder / f.name)
            rows.append({"strategy": f.stem, "verdict": apply_verdict.DROP,
                         "identity": identity, "reason": reason})
    out = folder / "verdict.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out, len(rows)


def ledger_row(project: str, databank: str, pre: dict, cut: dict, backup: Path) -> str:
    """Write the curate's one ledger row, signed and placed as F6 signs its filters (Q9).

    Returns:
        The line to print: the study written, or why nothing was (no template, no step).
    """
    signed, placed = ledgerrow.signed(project), ledgerrow.placed(project, databank)
    if isinstance(signed, str):
        return "sin plantilla en registry.csv: el Ledger no se apunta (Q9); el corte sigue"
    if isinstance(placed, str):
        return f"el Ledger no se apunta: {placed}"
    (sid, row), (step, _) = signed, placed
    exprs = sorted({r["expression"] for r in pre["discards"]})
    record.log(sid, {"step": step, "launched_by": "ventana", "symbol": row["symbol"],
                     "timeframe": row["timeframe"], "segment": pre["segment"],
                     "n_in": cut["before"], "n_out": cut["after"],
                     "criterion": "curate «Continuar workflow»: " + " · ".join(exprs),
                     "note": f"copia de lo borrado en {backup}; registro en {cut['out']}"})
    return f"Ledger: una fila en {sid}"


def consume(project: str, databank: str, removed: int, task: str) -> None:
    """Mark the discards consumed: one `cut` line in F6's log, append-only.

    It carries `clear` too, because that is the line `discards.since_clear` cuts at: the view
    and the next filter start from what the databank now holds, and the lines before stay.
    """
    discards.append(project, databank, [{"clear": True, "cut": True, "ts": discards.stamp(),
                                         "removed": removed, "task": task}])


SYNCING, SYNCED = b"Syncing databank(s) from files", b"Synchronization finished"


def syncing(top: Path) -> bool:
    """Whether SQX is still loading the databanks from their files: the last «Syncing
    databank(s) from files» of today's log has no «Synchronization finished» after it."""
    f = sqxlog.path(top, date.today())
    if not f.exists():
        return False
    with f.open("rb") as fh:
        fh.seek(max(0, f.stat().st_size - 4_000_000))
        tail = fh.read()
    return tail.rfind(SYNCING) > tail.rfind(SYNCED)


def ready(project: str, role: str) -> None:
    """Wait until the CLI answers, asking only `action=status`, and has its databanks loaded.

    The first `-project` command after a start makes SQX load every databank from its files.
    When another caller's status poll (the window's pulse) was that first command, this one
    is answered at once while the load goes on, and a task started then reads an empty input:
    🔬 2026-09-29, «WFM : No strategies to retest» at 11:52:35, «Loaded 21 strategies to
    databank SPP OOS» at 11:52:47.
    """
    top = preflight.WORKERS[role]["path"]
    for _ in range(READY_TRIES):
        answer = worker.call(f"-project action=status name={project}", role)
        if "not ready" not in answer and not syncing(top):
            return
        time.sleep(POLL)
    sys.exit(f"el {role} no respondió tras {READY_TRIES * POLL} s")


def watch(project: str, role: str, offsets: dict[Path, int]) -> dict:
    """Follow the run until SQX logs «Project finished», bounded at both ends.

    Args:
        project: The project started.
        role: Its worker.
        offsets: `sqxlog.mark` taken just before `action=start`: only what the log gained
            since counts, so an earlier run's finish — today's or yesterday's — is never this one's.

    Returns:
        The last `run` read. Each poll sends `-project action=status` (`progress.state`), and
        `stop` once a build passes its minutes (`buildcap`); the log is read across midnight.
        SystemExit when the start never reaches the log within START_WITHIN, when the worker
        dies, or past MAX_HOURS.
    """
    top, kept, began = preflight.WORKERS[role]["path"], [], time.monotonic()
    seen = stopped = False   # once the start was read, losing it is never «did not start»
    while True:
        time.sleep(POLL)
        if not worker.holding(top):
            sys.exit(f"el {role} se paró antes de «Project finished»")
        try:
            got = progress.state(role, project)
            live = got.get("status")
            now = next((t for t in got["tasks"] if t["status"] == "running"), None)
        except (OSError, ValueError, AttributeError, KeyError) as failed:
            # The status is only what the progress line shows. A log SQX is still writing must
            # never end the run: this loop's `finally` stops the worker (2026-09-28, a build).
            print(f"estado no legible ahora ({failed}); se sigue esperando", flush=True)
            live = now = None
        run = progress.run_state(sqxlog.grow(top, offsets, kept))
        waited = time.monotonic() - began
        seen = seen or run["project"] == project
        if run["project"] != project:
            if not seen and waited > START_WITHIN:
                sys.exit(f"SQX no escribió «Starting project '{project}'» en {START_WITHIN} s "
                         "tras `action=start`: no arrancó; se para el worker")
            continue
        if run["finished"]:
            if run["events"].get("error"):
                sys.exit(f"SQX abortó {project} («Error while running project» en su log): "
                         "la tarea no terminó; se para el worker")
            return run
        stopped = stopped or buildcap.enforce(project, role, now, top)
        if waited > MAX_HOURS * 3600:
            sys.exit(f"{project} sigue sin «Project finished» tras {MAX_HOURS} h: se para el "
                     "worker para liberar el carril")
        # A retest's log carries no compute-thread figure: its share is done over its input
        # (📓 2026-09-29, «MCR 1 Bar 0 % · 122 probadas» with 122 of 200 done).
        percent = run["percent"]
        if percent is None and now and now["done"] is not None and now["total"]:
            percent = min(100, 100 * now["done"] // now["total"])
        of = f" de {now['total']}" if now and now["total"] else ""
        say(60 + (percent or 0) * 35 // 100, f"{run['current'] or 'esperando'}"   # a build: no %
            + (f" {percent} %" if percent is not None else "") + (f" · {live['generated']}{of} "
            f"probadas · {live.get('in_databank', '?')} en el databank" if live else ""))


def advance(project: str, databank: str) -> None:
    """The whole sequence, re-checking the preflight first: two clicks cannot race it."""
    pre = preflight.check(project, databank)
    if not pre["ok"]:
        sys.exit("no se continúa:\n  " + "\n  ".join(pre["reasons"]))
    role, databank = pre["role"], pre["databank"]
    say(5, f"copiando {pre['n']} descartes")
    backup = (preflight.DISCARDS / project / databank.replace(" ", "_")
              / f"{datetime.now():%Y%m%d-%H%M%S}")
    csv, n = verdict(pre, backup)
    say(15, f"borrando {n} de {databank} ({pre['install']})")
    cut = apply_verdict.apply(project, databank, csv, role)
    print(ledger_row(project, databank, pre, cut, backup), flush=True)
    consume(project, databank, cut["removed"], pre["task"])
    if pre.get("fill"):         # CrossTF_Input (10.5) or CrossTF_Mothers, worker stopped
        say(20, f"llenando {pre['fill']}")
        print(crosstfload.fill(pre["fill"], project, role), flush=True)
    pre["skip"] += configure.run(pre, say)      # its configurator first; silenced MCRs off
    say(25, "activando " + ", ".join(t for t in stage.titles(pre["stage"]) if t not in pre["skip"]))
    on = stage.apply(pre["cfx"], [pre["stage"]], pre["skip"])
    if pre["stage"] == "crosstf":               # D1 on MT4: its own task, created by the fill
        stage.just(pre["cfx"], [t for t, a in on if a]
                   + crosstfload.separate_titles(pre["cfx"]))
    say(30, f"arrancando el {role}")
    top, port = preflight.WORKERS[role]["path"], preflight.WORKERS[role]["port"]
    workerguard.refuse_if_up(role, top, port)      # `start` answers 0 on «already running»
    try:
        worker.start(role)          # inside: a start that fails half-way is stopped too
        workerguard.mark(role, project)
        ready(project, role)
        offsets = sqxlog.mark(preflight.WORKERS[role]["path"])
        reply = worker.call(f"-project action=start name={project}", role)
        if "rror" in reply or "Cannot start" in reply:     # unresolved resources
            sys.exit(f"SQX rechazó `action=start` de {project}: {reply.strip()}")
        say(60, f"{pre['task']} lanzada")
        run = watch(project, role, offsets)
    finally:
        # The daemon started it (the preflight refused a worker already up), so it stops it:
        # a worker left up auto-syncs, and a sync deletes what it does not hold (hard rule 1).
        worker.stop(role)
        left = workerguard.stopped(role, top, port)    # `stop` answers 0 on «STILL RUNNING»
    if left:
        sys.exit(f"el {role} no se paró ({left}): páralo antes de leer sus databanks")
    say(100, f"{pre['task']}: {run['events'].get(pre['task'], '?')}; {databank} "
             f"{cut['before']} → {cut['after']}")


def main() -> None:
    """Run «Continuar workflow» for one databank; the window queues it on the conductor lane."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    a = ap.parse_args()
    # The daemon's cancel sends SIGTERM and waits: raising lets `advance`'s `finally` stop the
    # worker it started (ui/daemon/jobs.py `_wind_down`). Local, not `launch.run.graceful`:
    # launch.run imports this module, and importing it back would be a cycle.
    # The export after the stop is skipped on a cancel: it could outlast the grace period.
    signal.signal(signal.SIGTERM, lambda _s, _f: (os.environ.update(ALGO_NO_EXPORT="1"), sys.exit(
        "cancelado desde la ventana: se para el worker antes de salir")))
    advance(a.project, a.databank)


if __name__ == "__main__":
    main()
