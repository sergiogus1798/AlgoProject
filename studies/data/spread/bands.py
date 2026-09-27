#!/usr/bin/env python3
"""The spread band of each asset: its daily mean spread as a curve of price, with a 2.5–97.5 % band for the MC Retest.

One report per asset, into `spread/<tick feed>/band.{json,html,md}` and `band.json`'s numbers in
`band_summary.json`: every day of Darwinex's ticks as a point (price, mean spread in points), the
power-law curves of the mean and of each quantile, the range they give at the asset's prices —
the Min and Max to declare in the MC Retest's RandomizeSpread — and how many days of each year
fall outside the band. Reads only ticks; proposes and never writes `assets/`.
"""

import argparse
import json
import time

import numpy as np
import pandas as pd

from core.datapaths import spread_dir
from core.study import blocks, output, result as envelope
from core.study.result import progress
from studies.data.spread import band, inputs

MODULE = "spread"
GLOSSARY = [
    {"term": "Spread diario", "text": "La media del spread del primer tick de cada minuto cotizado "
     "ese día, en puntos (spread ÷ el tick de assets/)."},
    {"term": "Curva", "text": "spread = a · precio^b, una recta en escala log-log. b = 1 es un spread "
     "proporcional al precio; b = 0, un spread fijo en puntos."},
    {"term": "Banda", "text": "Las curvas de los cuantiles 2,5 % y 97,5 %: a cada precio, el 95 % "
     "central de los spreads diarios observados a precios parecidos."},
    {"term": "MC Retest", "text": "SQX sortea UN spread por simulación, uniforme entre Min y Max en "
     "pasos de 0,1 puntos, y lo aplica a todo el backtest (RandomizeSpread.java)."},
]


def at_prices(d: pd.DataFrame, curves: dict) -> pd.DataFrame:
    """The curves at the price of every year and at the last price: the ranges to pick from."""
    year = d.groupby(d.index.year)["price"].median()
    prices = np.append(year.to_numpy(), d["price"].iloc[-1])
    table = band.predict(curves, prices).reset_index()
    table.insert(0, "a precio de", [str(y) for y in year.index] + ["último día"])
    return table


def report(symbol: str, d: pd.DataFrame, curves: dict, cfg: dict) -> dict:
    """One asset's band as the contract's data."""
    started = time.time()
    qs = [str(q) for q in cfg["band"]["quantiles"]]
    low, high = qs[0], qs[-1]
    grid = np.linspace(d["price"].min(), d["price"].max(), 60)
    lines = band.predict(curves, grid)
    keep = blocks.thin(len(d), 1500)
    cloud = {"kind": "scatter", "title": "Spread medio de cada día contra el precio", "x_label": "precio",
             "y_label": "spread (puntos)", "quadrants": False, "fit": None,
             "points": [{"x": float(p), "y": float(s), "label": f"{t:%Y-%m-%d}", "group": str(t.year)}
                        for t, p, s in zip(d.index[keep], d["price"].iloc[keep], d["spread"].iloc[keep])]}
    curve = {"kind": "lines", "title": "Curvas ajustadas: media y banda", "unit": "puntos",
             "x": [f"{p:.0f}" for p in grid],
             "series": [{"label": "media" if k == "media" else f"cuantil {float(k):.1%}",
                         "values": lines[k].tolist(), "role": "real" if k == "media" else "reference"}
                        for k in lines.columns]}
    now = band.predict(curves, [d["price"].iloc[-1]]).iloc[0]
    cover = band.coverage(d, curves, low, high)
    worst = float(cover[["% por debajo", "% por encima"]].max().max())
    said = blocks.verdict(
        f"MC Retest de spread hoy: {now[low]:.1f} – {now[high]:.1f} puntos", "info",
        f"Al último precio ({d['price'].iloc[-1]:,.1f}) la curva media da {now['media']:.1f} puntos "
        f"y la banda {low}–{high}, {now[low]:.1f} a {now[high]:.1f}. Exponente de la media "
        f"b = {curves['media']['b']:.2f} (1 = proporcional al precio, 0 = fijo en puntos). "
        f"Peor año fuera de la banda por un lado: {worst:.0f} % de sus días (lo esperado, 2,5 %).",
        None)
    coef = pd.DataFrame([{"curva": k, "a": c["a"], "b": c["b"]} for k, c in curves.items()])
    tabs = [envelope.tab("curve", "Curva", [cloud, curve, blocks.table(
                "Coeficientes", coef, "spread = a · precio^b; la media lleva además el factor de "
                "smearing que devuelve la media desde el log.")]),
            envelope.tab("ranges", "Rangos para el MC Retest", [blocks.table(
                "Las curvas a cada precio", at_prices(d, curves),
                f"Min = cuantil {low}, Max = cuantil {high}, en puntos: lo que se escribe en la "
                "tarea RandomizeSpread para un tramo cuyo precio típico es ese.")]),
            envelope.tab("calibration", "Calibración", [blocks.table(
                "Días fuera de la banda por año", cover.reset_index(names="año"),
                "Una banda bien ajustada deja fuera ~2,5 % por cada lado cada año; un año muy "
                "por encima es un régimen que el precio no explica.")])]
    return envelope.envelope(MODULE, None, None, cfg, started, tabs, said, glossary=GLOSSARY,
                             summary={"symbol": symbol, "last_price": float(d["price"].iloc[-1]),
                                      **{f"hoy {k}": float(v) for k, v in now.items()}})


def main() -> None:
    """Fit and write the band of every configured asset, or those named, each on its own."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", action="append", default=[], help="one asset; all of band.assets when omitted")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()
    cfg = inputs.config(a.set)
    names = a.symbol or list(cfg["band"]["assets"])
    for n, symbol in enumerate(names):
        progress(100 * n // len(names), symbol)
        feed = cfg["band"]["assets"][symbol]
        tick = inputs.asset(symbol)["instrument"]["tick_size"]
        d = band.days(inputs.minutes(feed), tick, cfg["band"]["min_minutes"])
        curves = band.fit(d, cfg["band"]["quantiles"])
        got = report(symbol, d, curves, cfg)
        out = spread_dir(feed)
        d.to_parquet(out / "band_days.parquet")
        (out / "band_summary.json").write_text(json.dumps({"symbol": symbol, "curves": curves,
                                                           **got["summary"]}, indent=1))
        output.population(out, "band", got, f"Banda del spread — {symbol}")
        print(f"{symbol:10} b={curves['media']['b']:+.2f}  hoy (precio {d['price'].iloc[-1]:,.1f}): "
              + "  ".join(f"{k} {v:.1f}" for k, v in got["summary"].items() if k.startswith("hoy"))
              + f"  -> {out / 'band.html'}")
    progress(100, "hecho")


if __name__ == "__main__":
    main()
