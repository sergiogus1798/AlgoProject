#!/usr/bin/env python3
"""Step 20: the blind joint reading of 17, 18, 18.5 and 19, with SPA and StepM on oos2, and its ledger row."""

import argparse
import shlex
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from core.paths import report_dir
from core.study import output, verdicts
from core.study.config import fingerprint
from ledger import record, study as studymod
from studies.closing.blindJoint import inputs, many, one, pieces, readings


def ledger_row(a: argparse.Namespace, cfg: dict, got: dict, span: tuple) -> dict:
    """Record step 20's look at oos2 in the study's ledger.

    Args:
        a: The command's arguments.
        cfg: What inputs.config() returned.
        got: What measure.run() returned, with the SPA run.
        span: The oos2 window.

    Returns:
        The row as written. Under a chosen reading `n_out` is how many pass it; with no
        reading chosen the row is soft (`n_out = n_in`) and every reading's count goes in
        the note, as a soft screen is recorded (`ledger/README.md`). The scores are the
        mothers' per-day Sharpe ratios, never annualised.
    """
    reading = one.chosen(cfg)
    counts = {r: int((got["calls"][r] == "pass").sum()) for r in got["calls"].columns}
    k = len(got["states"])
    return record.log(studymod.study_id(a.symbol, a.timeframe, a.family), {
        "step": inputs.STEP, "launched_by": "studies.closing.blindJoint.report",
        "config_hash": fingerprint(cfg), "symbol": a.symbol, "timeframe": a.timeframe,
        "segment": inputs.SEGMENT, "window_from": str(span[0].date()),
        "window_to": str(span[1].date()), "n_in": k,
        "n_out": counts[readings.label(reading)] if reading else k,
        "criterion": f"blindJoint/{readings.label(reading) if reading else 'sin_regla'}",
        "thresholds": {"fwer": cfg["stepm"]["fwer"], "benchmark": cfg["benchmark"]["sizing"],
                       **cfg["joint"]},
        "seeds": [cfg["bootstrap"]["seed"]],
        "note": f"{'soft: ' if not reading else ''}pasan por lectura {counts}; SPA "
                f"{got['spa']}; buy & hold Sharpe {got['sharpe_bh']:.3f}"},
        (got["table"]["sharpe"] / np.sqrt(252)).values)


def verdict_table(population: pd.DataFrame, got: dict, cfg: dict) -> pd.DataFrame:
    """One row per mother for /curate: DESCARTAR only under a chosen reading that drops her."""
    reading = one.chosen(cfg)
    rows = []
    for mother, row in population.iterrows():
        call = got["calls"].loc[mother, readings.label(reading)] \
            if reading and row["complete"] else None
        reason = ("incompleta: no leída" if not row["complete"] else
                  f"lectura {readings.label(reading)}: {one.CALL[call]}" if reading else
                  "sin regla del dueño: anota y no corta")
        rows.append({"strategy": mother, "identity": row["identity"],
                     "verdict": "DESCARTAR" if call == "fail" else "MANTENER",
                     "reason": reason,
                     **{p: row[p]["state"] if row["complete"] else None for p in pieces.PIECES}})
    return pd.DataFrame(rows)


def main() -> None:
    """Open the four pieces through the ledger's door, test oos2 if the policy allows, write."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--wfm-databank", required=True, help="the WFM databank step 19 read")
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. USDJPY_DukasM1_the5ers")
    ap.add_argument("--symbol", required=True, help="asset file name, e.g. USDJPY")
    ap.add_argument("--timeframe", required=True, help="the build's timeframe, for the ledger")
    ap.add_argument("--family", required=True, help="the template family, for the ledger")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    study = studymod.study_id(a.symbol, a.timeframe, a.family)
    inputs.blind_door(study)
    population = pieces.population(a.project, a.wfm_databank)
    refused = inputs.segment_door(a.symbol)
    if not refused and not population["complete"].any():
        # 🔬 2026-09-29: with no mother holding all four pieces the panel came out empty, with
        # an integer index, and the oos2 prices raised TypeError. There is nothing to read:
        # the pieces are reported, oos2 stays closed and no ledger row is written.
        refused = ("ninguna madre llega con las cuatro piezas (WFC, CSCV, superficies y WFM): "
                   "no hay nada que leer en oos2")
    if refused and one.chosen(cfg):
        raise PermissionError(f"{refused}. Una lectura elegida necesita el StepM sobre oos2")
    span = inputs.window(a.symbol)
    wfm = Path(population["wfm_source"].iloc[0])
    data = {"population": population, "refused": refused,
            "source": f"Estudio {study} · WFM {wfm} · lotes de variantes de {a.project} · "
                      f"oos2 {span[0].date()} → {span[1].date()}"}
    if not refused:
        batches = population.loc[population["complete"], "batch"].to_dict()
        panel = inputs.panel(batches, span)
        data |= {"panel": panel, "moves": inputs.moves(a.feed, panel.index),
                 "point_value": inputs.point_value(a.symbol)}
    got = many.run(data, cfg)
    measured = got["measured"]

    out = report_dir(a.project, a.wfm_databank, date.today().isoformat()) / "blindJoint"
    output.population(out, "blindJoint", got["population"],
                      f"Paso 20, lectura conjunta ciega — {a.project}")
    for m in got["members"]:
        output.member(out, m, f"Paso 20 — {m['strategy']}")
    measured["calls"].rename_axis("strategy").reset_index().to_csv(out / "readings.csv",
                                                                   index=False)
    verdicts.write(out, verdict_table(population, measured, cfg), wfm,
                   " ".join(shlex.quote(x) for x in sys.argv), a.set)

    print(f"\n{got['population']['verdict']['label']} — {got['population']['verdict']['meaning']}")
    print(measured["states"].to_string())
    print(measured["calls"].to_string())
    if refused:
        print(f"\nSPA/StepM sin leer: {refused}\nsin fila en el ledger: no se abrió oos2")
    else:
        spa = measured["spa"]
        print(f"\nSPA  lower {spa['lower']:.3f}  consistent {spa['consistent']:.3f}  "
              f"upper {spa['upper']:.3f} · Sharpe del buy & hold {measured['sharpe_bh']:.3f}")
        written = ledger_row(a, cfg, measured, span)
        print(f"ledger: {written['study']} paso 20")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
