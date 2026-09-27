"""One asset's spread report as the contract's data: the proposal, by year, by hour, the model, the tail."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope

MODULE = "spread"
BPS = 1e4
GLOSSARY = [
    {"term": "Spread de apertura", "text": "El del primer tick de Darwinex de cada minuto: lo que "
     "paga una orden a mercado en la apertura de esa vela con precisión DATATICK."},
    {"term": "pb", "text": "Puntos básicos del precio: 1 pb = 0,01 %. El spread relativo al precio."},
    {"term": "Puntos", "text": "El spread dividido por el tick de assets/ — la unidad del "
     "spread de SQX (oro 0,01; USDJPY 0,01)."},
    {"term": "Constante", "text": "Cada año completo con su media a ± la tolerancia del dueño de "
     "la mediana de los años (ledger spread.constancy.tolerance)."},
    {"term": "Error del modelo", "text": "Media predicha del año ÷ media medida − 1, ajustando en "
     "un lado del año de corte y prediciendo el otro. «Hacia atrás» es la dirección que necesitan "
     "los años de Dukascopy."},
    {"term": "Comisión % propuesta", "text": "Spread medio del tramo × el factor del dueño, en % "
     "del nocional. SQX la cobra una vez por operación sobre el precio de apertura (OPEN.md #26), "
     "y una operación paga un spread entero ida y vuelta."},
]


def _monthly(daily: pd.DataFrame, tick: float | None = None) -> dict:
    """The reconstructed spread month by month, measured and modelled as two series.

    Args:
        daily: `verdict.reconstruct()`.
        tick: None for basis points of price; the tick size for points, SQX's unit.
    """
    month = daily.index.to_period("M")
    value = daily["rel"] * (BPS if tick is None else daily["price"] / tick)
    got = value.groupby([month, daily["source"]]).mean().unstack()
    x = [str(m) for m in got.index]
    unit, what = ("pb", "relativo") if tick is None else ("puntos", "en puntos")
    return {"kind": "lines", "title": f"Spread {what} medio por mes", "unit": unit, "x": x,
            "series": [{"label": s, "values": got[s].where(got[s].notna(), None).tolist(),
                        "role": "real" if s == "medido" else "sim"} for s in got.columns]}


def _model_tab(errors: pd.DataFrame, chosen: str) -> dict:
    """The validation: mean and worst error per model and direction, and year by year."""
    e = errors.assign(abs_error=errors["error"].abs())
    summary = e.groupby(["modelo", "sentido"]).agg(
        **{"error medio |%|": ("abs_error", "mean"), "peor año %": ("error", lambda s: s.iloc[np.argmax(np.abs(s))])})
    summary = (summary * 100).reset_index()
    wide = (errors.pivot_table(index=["modelo", "sentido"], columns="año", values="error") * 100).reset_index()
    wide.columns = [str(c) for c in wide.columns]
    return envelope.tab("model", "Modelo", [
        blocks.table("Validación cruzada", summary, f"Elegido: {chosen}. El error es predicho ÷ "
                     "medido − 1 de la media del año; negativo = el modelo se queda corto."),
        blocks.table("Error por año (%)", wide, "Cada celda es un año que el modelo no vio.")],
        note="Ningún modelo ve los años de Dukascopy anteriores a 2017: su error sobre ellos "
             "no se puede medir. El de «hacia atrás» es la mejor pista que hay.")


def run(symbol: str, facts: dict, yearly: pd.DataFrame, daily: pd.DataFrame, errors: pd.DataFrame,
        proposal: pd.DataFrame, grid: pd.DataFrame, hours: pd.Series, tail: np.ndarray,
        cfg: dict) -> dict:
    """One asset's report.

    Args:
        symbol: The asset, e.g. "XAUUSD".
        facts: scan.facts()'s dict.
        yearly: measure.yearly().
        daily: verdict.reconstruct().
        errors: verdict.validate().
        proposal: verdict.propose().
        grid: measure.week_grid().
        hours: measure.hours().
        tail: The last full year's minute relative spreads, in pb.
        cfg: inputs.config()'s dict.

    Returns:
        The contract dict. It describes an asset: the verdict block says whether a flat
        relative spread would do and what each segment should carry.
    """
    started = time.time()
    rel, pts = facts["relative"], facts["points"]
    state = "pass" if rel["constant"] else "watch"
    said = blocks.verdict(
        "relativo constante" if rel["constant"] else f"relativo NO constante → modelo {facts['model']}",
        state,
        f"Peor año del spread relativo a {rel['worst']:.2f} × la mediana de los años (tolerancia "
        f"±{cfg['constancy']['tolerance']:.0%}); en puntos {pts['worst']:.2f} ×. "
        f"Propuesta con factor {cfg['safety']['factor']}: comisión "
        + ", ".join(f"{r['tramo']} {r['comisión % propuesta']:.4f} %" for _, r in proposal.iterrows())
        + f". Hoy assets/ declara {facts['declared']}. MC Retest de spread: "
        f"{facts['mc_multiples']['min']:.2f}×–{facts['mc_multiples']['max']:.2f}× el spread de la tarea "
        "(cuantiles 2,5–97,5 % del día medido ÷ la media del modelo).",
        facts["error_backwards"])
    per_year = yearly.reset_index(names="año")
    per_year["año"] = per_year["año"].astype(str)
    hour_bars = {"kind": "bars", "title": "Spread de cada hora ÷ spread medio del día", "unit": "×",
                 "reference": 1.0,
                 "items": [{"label": f"{h:02d}", "value": float(v), "error": None,
                            "state": "watch" if v > 1.5 else "info"} for h, v in hours.items()]}
    heat = {"kind": "grid", "title": "Spread relativo medio (pb) por día y hora del feed",
            "rows": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"][:len(grid)],
            "cols": [f"{c:02d}" for c in grid.columns],
            "values": grid.where(grid.notna(), None).to_numpy().tolist(),
            "scale": "sequential", "levels": None, "labels": None}
    tabs = [envelope.tab("proposal", "Propuesta para SQX", [blocks.table(
                "Por tramo", proposal, "Los días sin Darwinex (antes de octubre de 2017) llevan "
                "el spread del modelo; «% días medidos» dice cuánto del tramo es medición.")],
                note="Propone, no escribe: assets/ es del dueño (core.assetwrite)."),
            envelope.tab("years", "Por año", [blocks.table("Spread por año", per_year,
                         "Primer y último año, parciales. Puntos = spread ÷ el tick de assets/."),
                         _monthly(daily), _monthly(daily, facts["tick"])],
                         note="En puntos es la curva que usa el reajuste de cada operación (con la "
                              "forma de su hora encima); el slippage real es la mitad."),
            envelope.tab("hours", "Por hora", [hour_bars, heat],
                         note="Hora del reloj del feed. El reajuste de cada operación multiplica "
                              "el spread del día modelado por el de su hora."),
            _model_tab(errors, facts["model"]),
            envelope.tab("tail", "Cola", [{**blocks.distribution(
                f"Spread de apertura de cada minuto, {facts['tail_year']}", "pb", tail,
                float(np.mean(tail)), "La línea es la media; la cola larga es el rollover y "
                "las noticias, y es la razón de usar la media y no la mediana."), "mark": "media"}])]
    return envelope.envelope(MODULE, None, None, cfg, started, tabs, said, glossary=GLOSSARY,
                             summary={"symbol": symbol, "model": facts["model"],
                                      "constant": rel["constant"], "worst": rel["worst"]})
