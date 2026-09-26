#!/usr/bin/env python3
"""The snooping screen over the gate's harvest: SPA and StepM against buy and hold, and the ledger row."""

import argparse
import shlex
import sys
from datetime import date

import numpy as np
import pandas as pd

from core.paths import report_dir
from core.study import output, verdicts
from core.study.config import fingerprint
from ledger import record, study as studymod
from studies.screening.snoopingScreen import inputs, many


def ledger_row(a: argparse.Namespace, cfg: dict, got: dict, span: tuple) -> dict:
    """Record this look at the window in the study's ledger.

    Args:
        a: The command's arguments.
        cfg: What inputs.config() returned.
        got: What measure.run() returned.
        span: The window the panel was cut to.

    Returns:
        The row as written. It is a soft screen, so `n_out` equals `n_in` and the count it
        would keep goes in the note (`ledger/README.md`, "A soft screen removes nobody").
        The scores are per-day Sharpe ratios, never annualised, as the ledger demands.
    """
    table = got["table"]
    days = table["sharpe"] / np.sqrt(252)
    return record.log(studymod.study_id(a.symbol, a.timeframe, a.family), {
        "step": 8, "launched_by": "studies.screening.snoopingScreen.report",
        "config_hash": fingerprint(cfg), "symbol": a.symbol, "timeframe": a.timeframe,
        "segment": cfg["study"]["segment"], "window_from": str(span[0].date()),
        "window_to": str(span[1].date()), "n_in": got["K"], "n_out": got["K"],
        "criterion": "snoopingScreen/stepm",
        "thresholds": {"fwer": cfg["stepm"]["fwer"], "benchmark": cfg["benchmark"]["sizing"]},
        "seeds": [cfg["bootstrap"]["seed"]],
        "note": f"soft: StepM names {len(got['named'])} of {got['K']}; SPA "
                f"{got['spa']}; buy & hold Sharpe {got['sharpe_bh']:.3f}"}, days.values)


def main() -> None:
    """Read the harvest the gate judged, test it against buy and hold, write and record it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the build databank the gate ran on")
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--symbol", required=True, help="asset file name, e.g. XAUUSD")
    ap.add_argument("--timeframe", required=True, help="the build's timeframe, for the ledger")
    ap.add_argument("--family", required=True, help="the template family, for the ledger")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    folder = inputs.harvest(a.project, a.databank)
    span = inputs.window(a.symbol, cfg["study"]["segment"])
    panel = inputs.panel(folder, span)
    data = {"panel": panel, "moves": inputs.moves(a.feed, panel.index),
            "point_value": inputs.point_value(a.symbol),
            "scores": inputs.scorecard(a.project, a.databank, folder),
            "source": {"harvest": str(folder),
                       "window": (str(span[0].date()), str(span[1].date()))}}
    got = many.run(data, cfg)
    measured = got["measured"]
    written = ledger_row(a, cfg, measured, span)

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "snoopingScreen"
    title = f"SPA y StepM contra el buy & hold — {a.project} / {a.databank}"
    output.population(out, "snoopingScreen", got["population"], title)
    for m in got["members"]:
        output.member(out, m, f"SPA y StepM — {m['strategy']}")
    table = measured["table"].reset_index()
    table.to_parquet(out / "table.parquet", compression="zstd")
    # Annotates, never cuts (owner, 2026-09-25): every row is MANTENER, so /curate applied
    # to this file removes nothing, and what the StepM said travels in its own column.
    verdicts.write(out, pd.DataFrame({
        "strategy": table["strategy"], "identity": table["identity"], "verdict": "MANTENER",
        "superior": table["superior"], "reason": np.where(
            table["superior"], "nombrada por el StepM", "")}), folder,
        " ".join(shlex.quote(x) for x in sys.argv), a.set)
    spa = measured["spa"]
    print(f"\nSPA  lower {spa['lower']:.3f}  consistent {spa['consistent']:.3f}  "
          f"upper {spa['upper']:.3f}   (bloque medio {measured['block']} días)")
    print(f"StepM a FWER {cfg['stepm']['fwer']}: {len(measured['named'])} de {measured['K']}"
          f" · Sharpe del buy & hold {measured['sharpe_bh']:.3f}")
    print(f"ledger: {written['study']} paso 8 -> {out}")


if __name__ == "__main__":
    main()
