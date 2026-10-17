#!/usr/bin/env python3
"""«Continuar workflow»: copy the discards aside, cut the databank, start the next task and wait."""

import argparse
import shutil
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core import worker
from ledger import record
from sqx import log as sqxlog
from sqx.curate import apply_verdict
from sqx.databank import discards
from sqx.projects import crosstfload, stage
from sqx.worker import guard as workerguard
from sqx.worker import preflight
from sqx.worker.session import graceful, ready, say, watch
from ui.daemon.filters import ledgerrow
from ui.daemon.launch import configure


def verdict(pre: dict[str, Any], folder: Path) -> tuple[Path, int]:
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
        sys.exit(
            f"{len(gone)} de {len(why)} descartes ya no están en {pre['source'].name}: el "
            "databank cambió desde el filtro. Vuelve a filtrar; no se ha tocado nada."
        )
    folder.mkdir(parents=True)
    rows = []
    for identity, reason in why.items():
        for f in by_id[identity]:
            shutil.copy2(f, folder / f.name)
            rows.append(
                {
                    "strategy": f.stem,
                    "verdict": apply_verdict.DROP,
                    "identity": identity,
                    "reason": reason,
                }
            )
    out = folder / "verdict.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out, len(rows)


def ledger_row(
    project: str,
    databank: str,
    pre: dict[str, Any],
    cut: apply_verdict.Applied,
    backup: Path,
) -> str:
    """Write the curate's one ledger row, signed and placed as F6 signs its filters (Q9).

    Returns:
        The line to print: the study written, or why nothing was (no template, no step).
    """
    signed, placed = ledgerrow.signed(project), ledgerrow.placed(project, databank)
    if isinstance(signed, str):
        return (
            "sin plantilla en registry.csv: el Ledger no se apunta (Q9); el corte sigue"
        )
    if isinstance(placed, str):
        return f"el Ledger no se apunta: {placed}"
    (sid, row), (step, _) = signed, placed
    exprs = sorted({r["expression"] for r in pre["discards"]})
    record.log(
        sid,
        {
            "step": step,
            "launched_by": "ventana",
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "segment": pre["segment"],
            "n_in": cut["before"],
            "n_out": cut["after"],
            "criterion": "curate «Continuar workflow»: " + " · ".join(exprs),
            "note": f"copia de lo borrado en {backup}; registro en {cut['out']}",
        },
    )
    return f"Ledger: una fila en {sid}"


def consume(project: str, databank: str, removed: int, task: str) -> None:
    """Mark the discards consumed: one `cut` line in F6's log, append-only.

    It carries `clear` too, because that is the line `discards.since_clear` cuts at: the view
    and the next filter start from what the databank now holds, and the lines before stay.
    """
    discards.append(
        project,
        databank,
        [
            {
                "clear": True,
                "cut": True,
                "ts": discards.stamp(),
                "removed": removed,
                "task": task,
            }
        ],
    )


def advance(project: str, databank: str) -> None:
    """The whole sequence, re-checking the preflight first: two clicks cannot race it."""
    pre = preflight.check(project, databank)
    if not pre["ok"]:
        sys.exit("no se continúa:\n  " + "\n  ".join(pre["reasons"]))
    role, databank = pre["role"], pre["databank"]
    say(5, f"copiando {pre['n']} descartes")
    backup = (
        preflight.DISCARDS
        / project
        / databank.replace(" ", "_")
        / f"{datetime.now():%Y%m%d-%H%M%S}"
    )
    csv, n = verdict(pre, backup)
    say(15, f"borrando {n} de {databank} ({pre['install']})")
    cut = apply_verdict.apply(project, databank, csv, role)
    print(ledger_row(project, databank, pre, cut, backup), flush=True)
    consume(project, databank, cut["removed"], pre["task"])
    if pre.get("fill"):  # CrossTF_Input (10.5) or CrossTF_Mothers, worker stopped
        say(20, f"llenando {pre['fill']}")
        print(crosstfload.fill(pre["fill"], project, role), flush=True)
    pre["skip"] += configure.run(pre, say)  # its configurator first; silenced MCRs off
    say(
        25,
        "activando "
        + ", ".join(t for t in stage.titles(pre["stage"]) if t not in pre["skip"]),
    )
    on = stage.apply(pre["cfx"], [pre["stage"]], pre["skip"])
    if pre["stage"] == "crosstf":  # its per-timeframe tasks, created by the fill
        stage.just(
            pre["cfx"],
            [t for t, a in on if a] + crosstfload.separate_titles(pre["cfx"]),
        )
    say(30, f"arrancando el {role}")
    top, port = preflight.WORKERS[role]["path"], preflight.WORKERS[role]["port"]
    workerguard.refuse_if_up(role, top, port)  # `start` answers 0 on «already running»
    try:
        worker.start(role)  # inside: a start that fails half-way is stopped too
        workerguard.mark(role, project)
        ready(project, role)
        offsets = sqxlog.mark(preflight.WORKERS[role]["path"])
        worker.started(
            worker.call(f"-project action=start name={project}", role), project
        )
        say(60, f"{pre['task']} lanzada")
        run = watch(project, role, offsets)
    finally:
        # The daemon started it (the preflight refused a worker already up), so it stops it:
        # a worker left up auto-syncs, and a sync deletes what it does not hold (hard rule 1).
        worker.stop(role)
        left = workerguard.stopped(
            role, top, port
        )  # `stop` answers 0 on «STILL RUNNING»
    if left:
        sys.exit(f"el {role} no se paró ({left}): páralo antes de leer sus databanks")
    say(
        100,
        f"{pre['task']}: {run['events'].get(pre['task'], '?')}; {databank} "
        f"{cut['before']} → {cut['after']}",
    )


def main() -> None:
    """Run «Continuar workflow» for one databank; the window queues it on the conductor lane."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    a = ap.parse_args()
    signal.signal(signal.SIGTERM, graceful)
    advance(a.project, a.databank)


if __name__ == "__main__":
    main()
