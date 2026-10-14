#!/usr/bin/env python3
"""Step 17 over one mother's variant batch: the three compositions, the state, the ledger's looks."""

from typing import Any
import argparse
import json
import time
from pathlib import Path

import pandas as pd

from core.study import blocks, draws, output, result as envelope
from core.study.config import fingerprint
from engines.variants import look, panel
from studies.optimisation.wfc import one
from studies.optimisation.wfc.contract import wfc, words
from studies.optimisation.wfc.inputs import batch, config

MODULE = "studies.optimisation.wfc"
SUMMARY = ("estado", "orden", "fuerte", "n", "rho", "p_mas", "p_menos", "nivel_top", "p_nivel", "r_sel")


def result(name: str, measured: dict[str, one.Composition], cfg: dict, started: float) -> dict[str, Any]:
    """The contract's result of one batch, with the facts the autopilot judges.

    Args:
        name: The batch folder's name, the mother's with underscores.
        measured: What `one.run` returned.
        cfg: The study's config.
        started: time.time() when the run began.

    Returns:
        The validated result plus `facts`: `c1`, `c2`, `c3` -> each composition's numbers
        and words, `estado` only in the deciding one.
    """
    deciding = next(k for k, c in panel.KEYS.items() if panel.label(c) == cfg["deciding"])
    facts = {key: got["facts"] for key, got in measured.items()}
    out = envelope.envelope(
        MODULE, name, None, cfg, started,
        [wfc.tab(measured, deciding, cfg["annotate"]["block_weeks"])],
        wfc.verdict(facts[deciding], cfg["panel"]["min_variants"], cfg["level"]["alpha"]),
        glossary=words.GLOSSARY,
        summary={"composicion": deciding} | {k: facts[deciding].get(k) for k in SUMMARY})
    return out | {"facts": blocks.plain(facts)}


def main() -> None:
    """Ask the door and the seal, measure the three compositions, write the result, log the looks."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="la carpeta del lote: metrics.parquet y variant_trades.parquet")
    ap.add_argument("--family", required=True,
                    help="la familia de plantillas del lote: la tercera parte del estudio del "
                         "ledger, donde se apuntan las tres composiciones")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()
    started = time.time()
    cfg = config.load(a.overrides)
    symbol, timeframe = look.market(a.work)
    look.admit(one.STEP, panel.SEGMENTS, symbol)      # before anything of oos2 is opened
    envelope.progress(10, f"{symbol} {timeframe}: el ledger y el sello permiten leer oos2")
    metrics = pd.read_parquet(a.work / "metrics.parquet")
    got = batch.read(a.work, symbol, timeframe)
    envelope.progress(60, f"exceso de {len(metrics)} variantes en los tres tramos")
    measured = one.run(metrics, got, symbol, cfg, a.work.name)
    found = result(a.work.name, measured, cfg, started)
    said = found["summary"]
    out = a.work / "estudios"
    draws.save(out, [d for got_one in measured.values() for d in got_one.pop("draws", [])])
    output.population(out, "wfc", found, f"WFC — {a.work.name.replace('_', ' ')}",
                      "¿Elegir por el pasado sirve fuera?")
    # The scalars the old pipeline's verdict read.
    comp = panel.columns(panel.KEYS[said["composicion"]])
    (a.work / "wfc.json").write_text(json.dumps(
        {"n": said["n"], "rho": said["rho"], "call": said["estado"], "p_mas": said["p_mas"],
         "p_menos": said["p_menos"], "composition": said["composicion"],
         "in_sample": comp["is_label"], "out_of_sample": comp["oos_label"]}, indent=2),
        encoding="utf-8")
    rho = "sin dato" if said["rho"] is None else f"rho {said['rho']:.3f}"
    rows = look.log_all(a.work, a.family, {
        "step": one.STEP, "launched_by": "wfc", "config_hash": fingerprint(cfg),
        "n_in": len(metrics), "n_out": len(metrics),
        "thresholds": {"alpha": cfg["null"]["alpha"], "top_share": cfg["level"]["top_share"]},
        "note": f"{said['estado']} · {said['orden']} · {rho} sobre {said['n']} variantes"})
    envelope.progress(100, f"{words.LABEL[said['estado']]} ({said['orden']}, {rho}, "
                           f"{said['n']} variantes); {len(rows)} filas en el ledger del paso "
                           f"{one.STEP}")
    print(f"-> {out / 'wfc.html'}")


if __name__ == "__main__":
    main()
