#!/usr/bin/env python3
"""«Continuar workflow»: copy the discards aside, cut the databank, start the next task and wait."""

import argparse
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from core import worker
from ledger import record
from sqx.curate import apply_verdict
from sqx.projects import stage
from ui.daemon import progress
from ui.daemon.advance import preflight, sqxlog
from ui.daemon.filters import discards, ledgerrow

POLL = 10           # seconds between two `action=status`
READY_TRIES = 60    # × POLL: the CLI answers «not ready» for ~20 s after the port opens
START_WITHIN = 120  # s after `action=start` for «Starting project '<P>'» to reach the log
# No run of this workflow is known to last this long (the longest logged step, a 1,000-variant
# WFC, took hours, not days). A job past it is stuck, and it holds the conductor lane: it stops.
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


def ready(project: str, role: str) -> None:
    """Wait until the CLI answers, asking only `action=status`."""
    for _ in range(READY_TRIES):
        if "not ready" not in worker.call(f"-project action=status name={project}", role):
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
        The last `run` read. Each poll calls `progress.state`, which sends `-project
        action=status` and nothing else — the one verb a worker may get between start and
        collect (owner, 2026-09-25). The log itself is read across midnight (`sqxlog`).
        SystemExit when the start never reaches the log within START_WITHIN, when the worker
        dies, or past MAX_HOURS.
    """
    top, kept, began = preflight.WORKERS[role]["path"], [], time.monotonic()
    while True:
        time.sleep(POLL)
        if not worker.holding(top):
            sys.exit(f"el {role} se paró antes de «Project finished»")
        live = progress.state(role, project).get("status")
        run = progress.run_state(sqxlog.grow(top, offsets, kept))
        waited = time.monotonic() - began
        if run["project"] != project:
            if waited > START_WITHIN:
                sys.exit(f"SQX no escribió «Starting project '{project}'» en {START_WITHIN} s "
                         "tras `action=start`: no arrancó; se para el worker")
            continue
        if run["finished"]:
            return run
        if waited > MAX_HOURS * 3600:
            sys.exit(f"{project} sigue sin «Project finished» tras {MAX_HOURS} h: se para el "
                     "worker para liberar el carril")
        say(60 + (run["percent"] or 0) * 35 // 100, f"{run['current'] or 'esperando'} "
            f"{run['percent'] or 0} %" + (f" · {live['generated']} probadas" if live else ""))


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
    say(25, f"activando solo {pre['task']}")
    stage.apply(pre["cfx"], [pre["stage"]], pre["skip"])
    say(30, f"arrancando el {role}")
    try:
        worker.start(role)          # inside: a start that fails half-way is stopped too
        ready(project, role)
        offsets = sqxlog.mark(preflight.WORKERS[role]["path"])
        reply = worker.call(f"-project action=start name={project}", role)
        if "rror" in reply:
            sys.exit(f"SQX rechazó `action=start` de {project}: {reply.strip()}")
        say(60, f"{pre['task']} lanzada")
        run = watch(project, role, offsets)
    finally:
        # The daemon started it (the preflight refused a worker already up), so it stops it:
        # a worker left up auto-syncs, and a sync deletes what it does not hold (hard rule 1).
        worker.stop(role)
    say(100, f"{pre['task']}: {run['events'].get(pre['task'], '?')}; {databank} "
             f"{cut['before']} → {cut['after']}")


def main() -> None:
    """Run «Continuar workflow» for one databank; the window queues it on the conductor lane."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    a = ap.parse_args()
    advance(a.project, a.databank)


if __name__ == "__main__":
    main()
