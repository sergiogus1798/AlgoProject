"""One strategy repriced at the real spread, as the contract's data: does its edge still pay it?"""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.data.spread import asset

MODULE = asset.MODULE
JUDGE = {"spread": "neto reajustado", "spread_slippage": "neto con slippage real"}
GLOSSARY = asset.GLOSSARY + [
    {"term": "Reajustada", "text": "El P/L de cada operación con el spread plano de SQX devuelto "
     "y el real cobrado: el de Darwinex en el minuto que la paga (entrada si es larga, salida si "
     "es corta) o, sin tick cerca, el del modelo para ese día y esa hora."},
    {"term": "Se rompe", "text": "Ganaba en ese tramo con el spread de SQX y deja de ganar con el "
     "real (y su slippage, con `reprice.judge: spread_slippage`). Lo que ya perdía no se atribuye "
     "al spread."},
    {"term": "Slippage real", "text": "La mitad del spread real en la entrada más la mitad en la "
     "salida, en lugar de los dos slippages planos que cobra SQX: la convención del dueño, que el "
     "slippage es la mitad del spread, siguiendo al spread de cada momento."}]


def _pf(pnl: pd.Series) -> float:
    """Profit factor: gross profit over gross loss."""
    loss = -pnl[pnl < 0].sum()
    return float(pnl[pnl > 0].sum() / loss) if loss > 0 else float("inf")


def _sample(t: pd.DataFrame, charged: float, tick: float) -> dict:
    """One sample's numbers before and after the repricing."""
    real = t["real"] / tick
    return {"operaciones": len(t), "% con tick": float((t["source"] == "tick").mean() * 100),
            "spread SQX (puntos)": charged / tick, "spread real medio (puntos)": float(real.mean()),
            "percentil del spread SQX": float((real <= charged / tick + 1e-9).mean() * 100),
            "neto SQX": float(t["Profit/Loss"].sum()), "neto reajustado": float(t["adjusted"].sum()),
            "neto con slippage real": float(t["slipped"].sum()),
            "PF SQX": _pf(t["Profit/Loss"]), "PF reajustado": _pf(t["adjusted"]),
            "PF con slippage real": _pf(t["slipped"])}


def _curve(t: pd.DataFrame, sample: str) -> dict:
    """One sample's cumulative P/L at SQX's flat spread and at the real one, thinned for drawing."""
    t = t.sort_values("Close time")
    keep = blocks.thin(len(t))
    return {"kind": "lines", "title": f"P/L acumulado {sample}: spread de SQX contra spread real",
            "unit": "USD", "x": [f"{d:%Y-%m-%d}" for d in t["Close time"].iloc[keep]],
            "series": [{"label": "spread de SQX", "values": t["Profit/Loss"].cumsum().iloc[keep].tolist(),
                        "role": "reference"},
                       {"label": "spread real", "values": t["adjusted"].cumsum().iloc[keep].tolist(),
                        "role": "sim"},
                       {"label": "spread y slippage reales", "values": t["slipped"].cumsum().iloc[keep].tolist(),
                        "role": "real"}]}


def run(strategy: str, identity: str, t: pd.DataFrame, charged: dict, tick: float, cfg: dict) -> dict:
    """One strategy's reading.

    Args:
        strategy: Its name in the retest databank.
        identity: SHA-256 of its normalised XML.
        t: Its trades with `real`, `source` (reprice.paid) and `adjusted` (reprice.adjust).
        charged: The flat spread SQX charged per sample, in price.
        tick: `assets/`'s tick size.
        cfg: inputs.config()'s dict.

    Returns:
        The contract dict; `summary` carries the flat row many.py tabulates.
    """
    started = time.time()
    per = {s: _sample(g, charged[s], tick) for s, g in t.groupby("sample", observed=True)}
    judged = JUDGE[cfg["reprice"]["judge"]]
    broken = [s for s, p in per.items() if p["neto SQX"] > 0 >= p[judged]]
    state = "fail" if broken else "pass"
    said = blocks.verdict(
        f"se rompe en {' y '.join(broken)}" if broken else "cubre el spread real", state,
        "; ".join(f"{s}: neto {p['neto SQX']:,.0f} → {p['neto reajustado']:,.0f} con el spread real y "
                  f"{p['neto con slippage real']:,.0f} con su slippage, PF {p['PF SQX']:.2f} → "
                  f"{p['PF reajustado']:.2f} → {p['PF con slippage real']:.2f}, spread SQX {p['spread SQX (puntos)']:g} "
                  f"puntos contra {p['spread real medio (puntos)']:.1f} reales de media "
                  f"({p['% con tick']:.0f} % medido con ticks)" for s, p in per.items()),
        None)
    table = pd.DataFrame(per).T.reset_index(names="tramo")
    shapes = [{**blocks.distribution(f"Spread real en sus operaciones, {s}", "puntos", (g["real"] / tick).to_numpy(),
                                  charged[s] / tick, f"La línea es el spread que cargó SQX: está en el "
                                  f"percentil {per[s]['percentil del spread SQX']:.0f} de lo que sus "
                                  "operaciones pagarían a esas horas.", band=(5, 95)), "mark": "spread de SQX"}
              for s, g in t.groupby("sample", observed=True)]
    tabs = [envelope.tab("headline", "Reajuste", [blocks.table("Por tramo", table)]
                         + [_curve(g, s) for s, g in t.groupby("sample", observed=True)],
                         note="Cada tramo es su propio backtest, con los costes que declaró su "
                              "tarea: las curvas empiezan en cero en cada uno. Las operaciones son "
                              "las mismas; sólo cambian el spread y el slippage que pagan."),
            envelope.tab("hours", "Spread a sus horas", shapes,
                         note="La distribución del spread en los minutos exactos que paga cada "
                              "operación, no la del día: una estrategia que entra en el rollover "
                              "paga el rollover.")]
    summary = {"verdict_state": state, "broken": ",".join(broken),
               **{f"{k} [{s}]": v for s, p in per.items() for k, v in p.items()}}
    return envelope.envelope(MODULE, strategy, identity, cfg, started, tabs, said,
                             glossary=GLOSSARY, summary=summary)
