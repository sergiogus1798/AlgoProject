"""One strategy's edge per operation against its own cost, as the contract's data."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.edgeCost import costs

MODULE = "edgeCost"
GLOSSARY = [
    {"term": "P&L bruto", "text": "Lo que dejó el movimiento de precio antes de pagar el "
     "spread y la comisión: `Profit/Loss` + comisión + el spread REALMENTE cobrado, medido "
     "contra la barra (nunca el declarado hoy en assets/)."},
    {"term": "Edge en spreads", "text": "El bruto medio (o mediano) por operación, dividido "
     "entre el coste de ida y vuelta que se modela hoy — cuántas veces ese coste cabe en la "
     "ventaja."},
    {"term": "Coste de breakeven c*", "text": "El coste de ida y vuelta al que la ventaja "
     "neta llega a cero. Es el mismo número que el edge en spreads: el múltiplo de hoy al "
     "que empataría."}]
HOURS_ES = "hora de entrada (UTC)"


def measure(priced: pd.DataFrame) -> dict:
    """The edge, the breakeven cost and the two breakdowns, from one strategy's priced trades.

    Args:
        priced: `costs.per_trade()`'s output, one strategy only.

    Returns:
        Flat numbers plus `by_hour` and `by_dow`, each a Series of mean gross per bucket.
        Median and min are kept beside every mean (feedback §9.5, 2026-09-30): a few large
        winners move the mean gross far more than the median, and a min shows the worst
        single trade the edge is built on rather than only its centre.
    """
    mean_cost, median_cost = priced["cost_today"].mean(), priced["cost_today"].median()
    min_cost = priced["cost_today"].min()
    mean_gross, median_gross = priced["gross"].mean(), priced["gross"].median()
    min_gross = priced["gross"].min()
    edge_mean = mean_gross / mean_cost
    edge_median = median_gross / mean_cost
    commission = priced["commission_cost"]
    by_hour = priced.assign(hour=priced["Open time"].dt.hour).groupby("hour")["gross"].mean()
    by_dow = priced.assign(dow=priced["Open time"].dt.dayofweek).groupby("dow")["gross"].mean()
    return {"n": len(priced), "mean_cost": mean_cost, "median_cost": median_cost,
            "min_cost": min_cost, "mean_gross": mean_gross, "median_gross": median_gross,
            "min_gross": min_gross, "edge_mean": edge_mean, "edge_median": edge_median,
            "breakeven_multiple": edge_mean, "cost_over_edge": mean_cost / mean_gross,
            "mean_commission": commission.mean(), "median_commission": commission.median(),
            "min_commission": commission.min(), "by_hour": by_hour, "by_dow": by_dow}


DOW_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def measure_table(got: dict) -> dict:
    """Gross and today's modelled cost, mean/median/min side by side (feedback §9.5)."""
    return blocks.table(
        "Bruto y coste de hoy: media, mediana y mínimo", pd.DataFrame([
            ["bruto por operación", got["mean_gross"], got["median_gross"], got["min_gross"]],
            ["coste de hoy por operación", got["mean_cost"], got["median_cost"],
             got["min_cost"]]], columns=["", "media", "mediana", "mínimo"]),
        "El mínimo es la peor operación sola, no un percentil: unos pocos ganadores grandes "
        "mueven la media del bruto mucho más que la mediana; el coste de hoy varía poco "
        "porque es el mismo spread/comisión declarado repetido, salvo cambios IS/OOS.")


def commission_table(got: dict) -> dict:
    """The commission alone, mean/median/min, and what the reconciliation residual says
    about swap (feedback §9.5: "tablas con comisiones, swaps...")."""
    return blocks.table(
        "Comisión por operación", pd.DataFrame([[
            got["mean_commission"], got["median_commission"], got["min_commission"]]],
            columns=["media", "mediana", "mínimo"]),
        "Ya está dentro de «coste de hoy» y de la reconciliación de abajo; aquí sola para "
        "verla sin el spread mezclado.")


def tabs(got: dict, recon: dict) -> list[dict]:
    """The four readings: the headline numbers, the breakdowns, and the reconciliation."""
    headline = blocks.table(
        "Edge por operación y coste de breakeven", pd.DataFrame([[
            got["n"], got["mean_gross"], got["median_gross"], got["mean_cost"],
            got["edge_mean"], got["edge_median"], got["breakeven_multiple"],
            got["cost_over_edge"]]], columns=[
            "operaciones", "bruto medio", "bruto mediano", "coste de hoy (medio)",
            "edge medio (spreads)", "edge mediano (spreads)", "c* (múltiplo de hoy)",
            "coste / edge"]),
        "Media y mediana del bruto, siempre las dos: unos pocos ganadores grandes dominan "
        "la media. c* es el mismo número que el edge medio: a cuántas veces el coste de hoy "
        "la ventaja empataría.")
    rec = blocks.table(
        "Reconciliación contra SQX", pd.DataFrame([[
            recon["n"], recon["corr"], recon["resid_mean"], recon["resid_std"]]],
            columns=["operaciones", "correlación", "residual medio (swap)", "residual std"]),
        "price_pnl reconstruido de Open/Close price contra Profit/Loss + comisión — el "
        "residual es swap y redondeo de centavos, nunca spread: el spread ya está en el "
        "precio de relleno. El residual medio es la mejor estimación de swap que este "
        "estudio tiene: la exportación de SQX no trae una columna de swap propia.")
    by_hour = {"kind": "bars", "title": f"Bruto medio por {HOURS_ES}", "unit": "USD",
              "reference": 0.0,
              "items": [{"label": f"{h:02d}h", "value": float(v), "error": None,
                         "state": "info"} for h, v in got["by_hour"].items()],
              "note": "El spread real varía con la sesión y el rollover; esto es la huella "
                      "en el bruto, no una medición del spread por hora."}
    by_dow = {"kind": "bars", "title": "Bruto medio por día de la semana", "unit": "USD",
             "reference": 0.0,
             "items": [{"label": DOW_ES[d], "value": float(v), "error": None, "state": "info"}
                       for d, v in got["by_dow"].items()],
             "note": ""}
    # Reconciliation FIRST (review FIX, 2026-09-26): a reader must see whether the bruto is
    # trustworthy before the headline table that uses it — never the other way round.
    return [envelope.tab("reconcile", "Reconciliación", [rec, commission_table(got)]),
            envelope.tab("headline", "Edge y breakeven", [headline, measure_table(got)]),
            envelope.tab("sessions", "Por sesión y hora", [by_hour, by_dow])]


def run(strategy: str, priced: pd.DataFrame, recon: dict, cfg: dict, asset: dict,
       identity: str | None = None) -> dict:
    """One strategy against its own edge-per-cost bar.

    Args:
        strategy: Its name in the export.
        priced: `costs.per_trade()`'s output, already filtered to this strategy.
        recon: `costs.reconcile()`'s output for the same rows.
        cfg: What `inputs.config()` returned.
        asset: `costs.asset_for()`'s dict, for the provisional-cost warnings.
        identity: SHA-256 of its normalised XML, read from the harvest.

    Returns:
        The contract dict: a call against `verdict.min_edge_spreads`, three tabs.
    """
    started = time.time()
    got = measure(priced)
    bar, action = cfg["verdict"]["min_edge_spreads"], cfg["verdict"]["action"]
    passed = got["edge_mean"] >= bar
    label = "por encima del umbral" if passed else "por debajo del umbral"
    said = blocks.verdict(
        label, "pass" if passed else "fail",
        f"Reconciliación {recon['corr']:.6f} sobre {recon['n']} operaciones — "
        f"{'el bruto se puede leer' if recon['corr'] >= 0.99 else 'el bruto NO se debe leer'}. "
        f"Edge medio {got['edge_mean']:.2f} spreads contra un umbral de {bar} "
        f"({'no elimina, sólo marca' if action == 'mark' else 'elimina en curate'}).",
        got["edge_mean"])
    warn = list(costs.warnings(asset))
    provisional = bool(warn)
    if recon["corr"] < 0.99:
        warn.append({"code": "reconciliation", "state": "watch",
                    "text": f"la reconciliación cayó a {recon['corr']:.4f}, por debajo del "
                            "suelo 0.99: el bruto de este resultado es decoración hasta "
                            "revisarla."})
    return envelope.envelope(
        MODULE, strategy, identity, cfg, started, tabs(got, recon), said, warn, GLOSSARY,
        summary={"n": got["n"], "edge_mean": got["edge_mean"], "edge_median": got["edge_median"],
                 "breakeven_multiple": got["breakeven_multiple"], "reconcile": recon["corr"],
                 "costs_provisional": provisional})
