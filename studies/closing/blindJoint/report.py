#!/usr/bin/env python3
"""Step 20: the blind joint reading of 17, 18 and 19, with SPA and StepM on oos2, and its ledger row."""

from typing import Any, cast
import argparse
import shlex
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from core.paths import report_dir
from core.study import draws, output, verdicts
from core.study.config import fingerprint
from ledger import record, study as studymod
from studies.closing.blindJoint import inputs, many, one, pieces, readings


# Only DESCARTAR cuts: the autopilot's step-20 rule reads `verdict_csv.drop` (criteria.yaml).
# REVISAR is KEPT, flagged for the owner's eye; any other call keeps: MANTENER.
VERDICT = {"fail": "DESCARTAR", "watch": "REVISAR"}


def ledger_row(
    a: argparse.Namespace, cfg: dict, got: dict, span: tuple
) -> dict[str, Any]:
    """Record step 20's look at oos2 in the study's ledger.

    Args:
        a: The command's arguments.
        cfg: What inputs.config() returned.
        got: What measure.run() returned, with the SPA run.
        span: The oos2 window.

    Returns:
        The row as written. Under a chosen reading `n_out` is how many it does not drop
        (those that pass it); with no
        reading chosen the row is soft (`n_out = n_in`) and every reading's count goes in
        the note, as a soft screen is recorded (`ledger/README.md`). The scores are the
        mothers' per-day Sharpe ratios, never annualised.
    """
    reading = one.chosen(cfg)
    counts = {r: int((got["calls"][r] == "pass").sum()) for r in got["calls"].columns}
    k = len(got["states"])
    return record.log(
        studymod.study_id(a.symbol, a.timeframe, a.family),
        {
            "step": inputs.STEP,
            "launched_by": "studies.closing.blindJoint.report",
            "config_hash": fingerprint(cfg),
            "symbol": a.symbol,
            "timeframe": a.timeframe,
            "segment": inputs.SEGMENT,
            "window_from": str(span[0].date()),
            "window_to": str(span[1].date()),
            "n_in": k,
            "n_out": int((got["calls"][readings.label(reading)] != "fail").sum())
            if reading
            else k,
            "criterion": f"blindJoint/{readings.label(reading) if reading else 'sin_regla'}",
            "thresholds": {
                "fwer": cfg["stepm"]["fwer"],
                "benchmark": "random_trader",
                **cfg["benchmark"],
                **cfg["joint"],
            },
            "seeds": [cfg["bootstrap"]["seed"], cfg["benchmark"]["seed"]],
            "note": f"{'soft: ' if not reading else ''}pasan por lectura {counts}; SPA "
            f"{got['spa']}; benchmark: random trader of the mother's footprint",
        },
        (got["table"]["sharpe"] / np.sqrt(252)).values,
    )


def verdict_table(population: pd.DataFrame, got: dict, cfg: dict) -> pd.DataFrame:
    """One row per mother for /curate: DESCARTAR only under a chosen reading that drops her,
    REVISAR (kept and flagged, never cut: like anything but DESCARTAR) for a `watch`."""
    reading = one.chosen(cfg)
    rows = []
    for mother, row in population.iterrows():
        complete = bool(row["complete"])
        call = cast(
            str | None,
            got["calls"].loc[mother, readings.label(reading)]
            if reading and complete
            else None,
        )
        reason = (
            "incompleta: no leída"
            if not complete
            else f"lectura {readings.label(reading)}: {one.CALL[cast(str, call)]}"
            if reading
            else "sin regla del dueño: anota y no corta"
        )
        rows.append(
            {
                "strategy": mother,
                "identity": row["identity"],
                "verdict": VERDICT.get(call or "", "MANTENER"),
                "reason": reason,
                **{p: row[p]["state"] if complete else None for p in pieces.PIECES},
            }
        )
    return pd.DataFrame(rows)


def need_stepm(refused: str | None, cfg: dict) -> None:
    """Raise when the StepM could not be read and the chosen reading needs it."""
    reading = one.chosen(cfg)
    if refused and reading:
        raise PermissionError(
            f"{refused}. Una lectura elegida necesita el StepM sobre oos2"
        )


def main() -> None:
    """Open the three pieces through the ledger's door, test oos2 if the policy allows, write."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--wfm-databank", required=True, help="the WFM databank step 19 read"
    )
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. USDJPY_M1")
    ap.add_argument("--symbol", required=True, help="asset file name, e.g. USDJPY")
    ap.add_argument(
        "--timeframe", required=True, help="the build's timeframe, for the ledger"
    )
    ap.add_argument(
        "--family", required=True, help="the template family, for the ledger"
    )
    ap.add_argument(
        "--set", action="extend", nargs="+", default=[], help="section.key=value"
    )
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    study = studymod.study_id(a.symbol, a.timeframe, a.family)
    inputs.blind_door(study)
    population = pieces.population(a.project, a.wfm_databank)
    refused = inputs.segment_door(a.symbol)
    if not refused and not bool(population["complete"].any()):
        # 🔬 2026-09-29: with no mother holding all three pieces the panel came out empty, with
        # an integer index, and the oos2 prices raised TypeError. There is nothing to read:
        # the pieces are reported, oos2 stays closed and no ledger row is written.
        refused = (
            "ninguna madre llega con las tres piezas (WFC, CSCV y WFM): "
            "no hay nada que leer en oos2"
        )
    batches = population.loc[population["complete"], "batch"].to_dict()
    refused = refused or inputs.trades_door(batches)
    need_stepm(refused, cfg)
    span = inputs.window(a.symbol)
    wfm = Path(population["wfm_source"].iloc[0])
    data = {
        "population": population,
        "refused": refused,
        "source": f"Estudio {study} · WFM {wfm} · lotes de variantes de {a.project} · "
        f"oos2 {span[0].date()} → {span[1].date()}",
    }
    if not refused:
        panel = inputs.panel(batches, span, a.feed)
        random, mc = inputs.random_traders(batches, span, a.feed, cfg)
        data |= {"panel": panel, "benchmark": random.reindex(panel.index), "mc": mc}
    got = many.run(data, cfg)
    measured = got["measured"]

    out = report_dir(a.project, a.wfm_databank, date.today().isoformat()) / "blindJoint"
    output.population(
        out,
        "blindJoint",
        got["population"],
        f"Paso 20, lectura conjunta ciega — {a.project}",
    )
    for m in got["members"]:
        output.member(out, m, f"Paso 20 — {m['strategy']}")
    measured["calls"].rename_axis("strategy").reset_index().to_csv(
        out / "readings.csv", index=False
    )
    verdicts.write(
        out,
        verdict_table(population, measured, cfg),
        wfm,
        " ".join(shlex.quote(x) for x in sys.argv),
        a.set,
    )

    print(
        f"\n{got['population']['verdict']['label']} — {got['population']['verdict']['meaning']}"
    )
    print(measured["states"].to_string())
    print(measured["calls"].to_string())
    if refused:
        print(
            f"\nSPA/StepM sin leer: {refused}\nsin fila en el ledger: no se abrió oos2"
        )
    else:
        spa = measured["spa"]
        kept = measured["spa_drawn"]  # the bootstrap each SPA p was counted on
        draws.save(
            out,
            [
                draws.record("blindJoint", f"spa_{k}", kept["observed"], kept[k])
                for k in spa
            ],
        )
        print(
            f"\nSPA  lower {spa['lower']:.3f}  consistent {spa['consistent']:.3f}  "
            f"upper {spa['upper']:.3f} · contra el operador al azar de su misma huella"
        )
        written = ledger_row(a, cfg, measured, span)
        print(f"ledger: {written['study']} paso 20")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
