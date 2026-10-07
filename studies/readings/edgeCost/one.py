"""One strategy's oos1 edge against the cost it paid, as the contract's data."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.edgeCost import costs

MODULE = "edgeCost"
GLOSSARY = [
    {"term": "P&L bruto", "text": "El P/L de la operación repreciada (apertura de barra, spread, "
     "slippage, comisión y swap de la tarea) más el coste que pagó: lo que dejó el movimiento "
     "de precio antes de cobrar."},
    {"term": "Coste pagado", "text": "El spread, el doble slippage, la comisión y el swap por "
     "noche que el repreciado común cobró a cada operación de oos1 — el mismo que lee la puerta."},
    {"term": "Edge en costes", "text": "Bruto medio dividido entre coste medio, sólo oos1: cuántas "
     "veces el coste pagado cabe en la ventaja. 1 es el punto muerto; el mismo número es el "
     "múltiplo del coste al que la ventaja neta llegaría a cero."}]
HOURS_ES = "hora de entrada (reloj del feed)"
DOW_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def measure(priced: pd.DataFrame) -> dict:
    """The edge over the cost paid, and the gross by entry hour and weekday.

    Args:
        priced: `costs.per_trade()`'s output, one strategy only (oos1).

    Returns:
        `mean_gross`, `mean_cost`, `edge_mean` = mean(pnl + cost) / mean(cost) — the gate's
        `edge_mean_oos` on the same trades — and `by_hour`, `by_dow`.
    """
    gross = priced["pnl"] + priced["cost"]
    mean_cost = priced["cost"].mean()
    when = priced["open_time"]
    return {"mean_gross": gross.mean(), "mean_cost": mean_cost, "edge_mean": gross.mean() / mean_cost,
            "by_hour": gross.groupby(when.dt.hour).mean(), "by_dow": gross.groupby(when.dt.dayofweek).mean()}


def tabs(got: dict) -> list[dict]:
    """The headline numbers and the breakdown by session."""
    headline = blocks.table(
        "Edge sobre el coste pagado (oos1)", pd.DataFrame([[
            got["mean_gross"], got["mean_cost"], got["edge_mean"]]],
            columns=["bruto medio", "coste pagado (medio)", "edge medio (× coste)"]),
        "Sólo oos1, cada operación repreciada con los costes de la tarea. El edge es bruto "
        "medio / coste medio: 1 es el punto muerto, y es también el múltiplo del coste al que "
        "la ventaja neta llegaría a 0.")
    by_hour = {"kind": "bars", "title": f"Bruto medio por {HOURS_ES}", "unit": "USD",
               "reference": 0.0,
               "items": [{"label": f"{h:02d}h", "value": float(v), "error": None,
                          "state": "info"} for h, v in got["by_hour"].items()],
               "note": ""}
    by_dow = {"kind": "bars", "title": "Bruto medio por día de la semana", "unit": "USD",
              "reference": 0.0,
              "items": [{"label": DOW_ES[d], "value": float(v), "error": None, "state": "info"}
                        for d, v in got["by_dow"].items()],
              "note": ""}
    return [envelope.tab("headline", "Edge y coste", [headline]),
            envelope.tab("sessions", "Por sesión y hora", [by_hour, by_dow])]


def run(strategy: str, priced: pd.DataFrame, cfg: dict, asset: dict,
        identity: str | None = None) -> dict:
    """One strategy against its own edge-per-cost bar.

    Args:
        strategy: Its name in the export.
        priced: `costs.per_trade()`'s output, already filtered to this strategy.
        cfg: What `inputs.config()` returned.
        asset: `costs.asset_for()`'s dict, for the provisional-cost warnings.
        identity: SHA-256 of its normalised XML, read from the harvest.

    Returns:
        The contract dict: a call against `verdict.min_edge_spreads`, two tabs.
    """
    started = time.time()
    got = measure(priced)
    bar, action = cfg["verdict"]["min_edge_spreads"], cfg["verdict"]["action"]
    passed = got["edge_mean"] >= bar
    said = blocks.verdict(
        "por encima del umbral" if passed else "por debajo del umbral", "pass" if passed else "fail",
        f"Edge medio {got['edge_mean']:.2f} veces el coste pagado en oos1 contra un umbral de "
        f"{bar} ({'no elimina, sólo marca' if action == 'mark' else 'elimina en curate'}).",
        got["edge_mean"])
    return envelope.envelope(MODULE, strategy, identity, cfg, started, tabs(got), said,
                             costs.warnings(asset), GLOSSARY,
                             summary={"edge_mean": got["edge_mean"]})
