#!/usr/bin/env python3
"""Step 4's spread study: each asset's real Darwinex spread, whether it is constant, and what SQX should carry.

Writes, per asset, into `spread/<tick feed>/` under the data root: `minutes.parquet` (the tick
file decoded, rebuilt only when SQX updates it), `daily.parquet` (the relative spread measured
where Darwinex has ticks and modelled back to Dukascopy's first day — what step 8's repricing
reads), `hours.parquet`, `summary.json` and the report as `spread.json/.html/.md`. Proposes the
costs; never writes `assets/`. `model.fixed` pins the owner's model for an asset over the
best-validated one.
"""

import argparse
import json
from datetime import date

import pandas as pd

from core import assetdata
from core.datapaths import spread_dir
from core.study import output
from core.study.result import progress
from studies.data.spread import asset, inputs, measure, verdict

SEGMENTS = ("build", "oos1", "oos2")


def declared(data: dict) -> str:
    """What `assets/` declares today for the spread and the commission, in words."""
    c, unit = data["costs"], assetdata.schema(data)["commission"]["unit"]
    spreads = [f"{k} {c[k]['use']} puntos" for k in assetdata.fields(data) if k.startswith("spread")]
    return ", ".join(spreads + [f"comisión {c['commission']['use']} ({unit})"])


def one(symbol: str, cfg: dict) -> dict:
    """Measure, test, model, propose and write one asset."""
    feeds, data = cfg["assets"][symbol], inputs.asset(symbol)
    tick = data["instrument"]["tick_size"]
    m = inputs.minutes(feeds["ticks"])
    vol = inputs.volatility(feeds["bars"])
    days = measure.days(m, vol, cfg["day"]["min_minutes"])
    yearly = measure.yearly(m, tick)
    tolerance = cfg["constancy"]["tolerance"]
    rel, pts = verdict.constancy(yearly, "pb media", tolerance), verdict.constancy(yearly, "puntos media", tolerance)
    errors = verdict.validate(days, cfg["model"]["candidates"], cfg["model"]["split"])
    chosen = cfg["model"]["fixed"].get(symbol) or verdict.choose(rel, errors)
    daily = verdict.reconstruct(days, vol, chosen)
    windows = {s: assetdata.window(data, s) for s in SEGMENTS}
    proposal = verdict.propose(daily, windows, tick, cfg["safety"]["factor"])
    hours = measure.hours(m)
    tail_year = int(verdict.full_years(yearly).index[-1])
    tail = (measure.relative(m) * measure.BPS)[m.index.year == tail_year].to_numpy()
    back = errors[(errors["modelo"] == chosen) & (errors["sentido"] == "hacia atrás")]["error"]
    facts = {"symbol": symbol, "ticks": feeds["ticks"], "bars": feeds["bars"], "model": chosen, "tick": tick,
             "relative": rel, "points": pts, "error_backwards": float(back.abs().mean()),
             "declared": declared(data), "tail_year": tail_year,
             "mc_multiples": verdict.mc_multiples(days, chosen, [cfg["band"]["quantiles"][0], cfg["band"]["quantiles"][-1]]),
             "proposal": proposal.to_dict("records"), "scanned_on": date.today().isoformat(),
             "ticks_from": str(m.index[0]), "ticks_to": str(m.index[-1])}
    out = spread_dir(feeds["ticks"])
    daily.to_parquet(out / "daily.parquet")
    hours.rename("multiplier").to_frame().to_parquet(out / "hours.parquet")
    (out / "summary.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    output.population(out, "spread", asset.run(symbol, facts, yearly, daily, errors, proposal,
                                               measure.week_grid(m), hours, tail, cfg),
                      f"Spread real — {symbol}")
    return facts


def main() -> None:
    """Scan every asset of the config, or those named."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", action="append", default=[], help="one asset; all when omitted")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()
    cfg = inputs.config(a.set)
    names = a.symbol or list(cfg["assets"])
    for n, symbol in enumerate(names):
        progress(5 + 90 * n // len(names), symbol)
        got = one(symbol, cfg)
        table = pd.DataFrame(got["proposal"]).set_index("tramo")
        print(f"\n{symbol}: relativo {'constante' if got['relative']['constant'] else 'NO constante'} "
              f"(peor año {got['relative']['worst']:.2f}×) → modelo {got['model']}, error hacia "
              f"atrás {got['error_backwards']:.0%}. Hoy: {got['declared']}. MC Retest de spread: "
              f"{got['mc_multiples']['min']:.2f}x–{got['mc_multiples']['max']:.2f}x el spread de la tarea")
        print(table[["% días medidos", "spread medio (pb)", "comisión % propuesta",
                     "puntos equivalentes"]].round(4).to_string())
    progress(100, "hecho")
    print(f"-> {spread_dir()}")


if __name__ == "__main__":
    main()
