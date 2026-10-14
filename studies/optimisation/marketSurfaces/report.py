#!/usr/bin/env python3
"""Step 18.5 over one mother's variant batch: does the main market's order of variants travel to the others?"""

from typing import Any
import argparse
import sys
import time
from pathlib import Path

import pandas as pd
from threadpoolctl import threadpool_limits

from core import assetdata
from core.study import blocks, draws, output, result as envelope, verdicts
from core.study.config import fingerprint
from engines.variants import look
from studies.optimisation.marketSurfaces import one
from studies.optimisation.marketSurfaces.contract import tabs, words
from studies.optimisation.marketSurfaces.inputs import batch, config, markets
from studies.optimisation.marketSurfaces.verdict import call

MODULE = "studies.optimisation.marketSurfaces"


def result(name: str, measured: dict, symbol: str, provisional: list[str], cfg: dict,
           started: float) -> dict[str, Any]:
    """The small result the judge and step 20 read: envelope, summary, facts and light tabs.

    Args:
        name: The batch folder's name, the mother's with underscores.
        measured: What `one.measure` returned.
        symbol: The main asset.
        provisional: The markets whose cost card still carries a placeholder.
        cfg: The study's config.
        started: time.time() when the run began.

    Returns:
        The validated result plus `facts` (`one.facts`); `summary.segundos` is the run's time.
    """
    facts, state = one.facts(measured, cfg)
    order, shown = facts["orden"], tabs.verdict(facts, state, symbol, cfg)
    summary = {"call": shown["label"], "state": state, "estado": call.WORD[state],
               "orden": order.get("estado", call.NO_DATA), "rho": order["rho"],
               "p_mas": order["p_mas"], "p_menos": order["p_menos"], "peso": order["mercados"],
               "markets": order["n_mercados"], "declared": len(measured["principal"]["mercados"]),
               "variants": measured["usable"], "prima": facts["prima"]["valor"],
               "prima_bajo_p5": facts["prima"].get("bajo_p5"), "rho_auto": facts["auto"]["rho"],
               "oos2": measured["oos2"] is not None, "segundos": round(time.time() - started, 1)}
    out = envelope.envelope(MODULE, name, None, cfg, started, tabs.tabs(measured, facts, symbol, cfg),
                            shown, tabs.warnings(measured, facts, provisional, cfg), words.GLOSSARY,
                            summary)
    return out | {"facts": blocks.plain(facts)}


def record(name: str, measured: dict, seed: int) -> list[dict]:
    """The nulls behind the joint order's p and the premium's cut, for each reading measured."""
    where = {"strategy": name, "seed": seed}
    return [d for reading in ("principal", "dos_semanas", "oos2") if measured[reading]
            for d in (
                draws.record("marketSurfaces", "p_mas", measured[reading]["orden"]["rho"],
                             measured[reading]["nulo"], **where, reading=reading,
                             p="flip.tails", unit="rho conjunto entre mercados"),
                draws.record("marketSurfaces", "prima_bajo_p5", measured[reading]["prima"]["valor"],
                             measured[reading]["prima_nulo"], **where, reading=reading,
                             unit="prima del top, exceso neto"))]


def main() -> None:
    """Ask the door for the legs read, reprice every market, measure, write the result, log the look."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="la carpeta del lote: metrics.parquet, segments.parquet y "
                         "variant_trades.parquet")
    ap.add_argument("--family", required=True,
                    help="la familia de plantillas del lote, para la fila del ledger")
    ap.add_argument("--out", type=Path, help="dónde escribir; por defecto <work>/estudios")
    ap.add_argument("--oos2", action="store_true",
                    help="añade la lectura de oos2 en los otros mercados (bloque ciego); sin "
                         "ella oos2 no se abre")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()

    started = time.time()
    cfg = config.load(a.overrides)
    symbol, timeframe = look.market(a.work)
    segments = one.INSIDE + one.OOS2 * a.oos2
    look.admit(cfg["step"], segments, symbol)         # before any trade is opened
    envelope.progress(5, f"{symbol} {timeframe}: {', '.join(segments)} permitidos por el ledger")

    table, design, asset = markets.declared(symbol), batch.variants(a.work), assetdata.load(symbol)
    legs = one.legs(list(table["feed"]), a.oos2)
    data = batch.read(a.work, symbol, timeframe, legs, design["ids"], cfg)
    since = dict(zip(table["feed"], table["data_from"])) | {one.MAIN: None}
    years = {m: {leg: batch.years(asset, leg, since[m]) for leg in read} for m, read in legs.items()}
    envelope.progress(60, f"{len(design['ids'])} variantes x {len(legs)} mercados, exceso semanal")

    # One BLAS thread: the autopilot runs the mothers at once, and two of them with OpenBLAS's
    # 64 threads each took 33 s apiece against 4.1 (🔬 2026-10-13). ρ, p and the verdict are the
    # same; the saved null vectors move in the 6th decimal (owner accepted it, 2026-10-13).
    with threadpool_limits(1):
        measured = one.measure(data, design, table, years, cfg, a.oos2)
    provisional = [m for m in [asset["sqx_symbol"], *table["feed"]] if markets.provisional(m)]
    res = result(a.work.name, measured, symbol, provisional, cfg, started)
    out = a.out or a.work / "estudios"
    output.population(out, "marketSurfaces", res, f"Superficies por mercado — {a.work.name}",
                      res["tabs"][0]["note"])
    draws.save(out, record(a.work.name, measured, cfg["null"]["seed"]))
    measured["principal"]["mercados"].to_csv(out / "mercados.csv", index=False)
    command, said = " ".join(sys.argv), res["summary"]
    verdicts.write(out, pd.DataFrame([{"strategy": a.work.name, "identity": None,
                                       "verdict": said["estado"]}]), a.work, command, a.overrides)
    rows = look.log(a.work, a.family, {
        "step": cfg["step"], "launched_by": command, "config_hash": fingerprint(cfg),
        "n_in": len(design["ids"]), "n_out": len(design["ids"]),
        "criterion": f"marketSurfaces: {symbol} contra {said['declared']} mercados declarados, "
                     f"{said['markets']} en la media (peso {said['peso']:g})",
        "thresholds": {"alpha": cfg["null"]["alpha"], "min_weight": cfg["markets"]["min_weight"],
                       "top_share": cfg["premium"]["top_share"]},
        "note": f"{said['estado']} · orden {said['orden']} · {said['variants']} variantes"},
        segments)

    envelope.progress(100, f"{said['call']} — {len(rows)} filas en el ledger del paso {cfg['step']}")
    for warning in res["warnings"]:
        print(f"[{warning['state']}] {warning['text']}")
    print(f"{res['verdict']['meaning']}\n{said['segundos']} s -> {out / 'marketSurfaces.html'}")


if __name__ == "__main__":
    main()
