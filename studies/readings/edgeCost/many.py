"""Every strategy of one harvest against its own edge-per-cost bar, as one result and one panel."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.edgeCost import costs, one

MODULE = one.MODULE


def _row(identity: str, group: pd.DataFrame) -> dict:
    """One strategy's line: its edge measures and its own reconciliation."""
    got = one.measure(group)
    target = group["Profit/Loss"] + group["commission_cost"]
    corr = float(np.corrcoef(group["price_pnl"], target)[0, 1]) if len(group) > 1 else float("nan")
    return {"identity": identity, "n": got["n"], "mean_gross": got["mean_gross"],
            "median_gross": got["median_gross"], "mean_cost": got["mean_cost"],
            "edge_mean": got["edge_mean"], "edge_median": got["edge_median"],
            "breakeven_multiple": got["breakeven_multiple"], "reconcile": corr}


def run(priced: pd.DataFrame, names: pd.Series, cfg: dict, asset: dict) -> dict:
    """Every strategy in one priced harvest, judged against the same bar.

    Args:
        priced: `costs.per_trade()`'s output for the whole harvest (every strategy).
        names: Identity -> strategy name (`inputs.names`).
        cfg: What `inputs.config()` returned.
        asset: `costs.asset_for()`'s dict, for the provisional-cost warnings.

    Returns:
        {"population": the export's result, "panel": one row per strategy, indexed by
        strategy name, with `verdict` ("MANTENER"/"DESCARTAR") added — what verdict.csv
        and the window's population table read}.
    """
    started = time.time()
    rows = {i: _row(i, g) for i, g in priced.groupby("identity", observed=True)}
    panel = pd.DataFrame(rows).T
    panel.index.name = "identity"
    panel["strategy"] = names.reindex(panel.index)
    panel = panel.set_index("strategy")
    bar, action = cfg["verdict"]["min_edge_spreads"], cfg["verdict"]["action"]
    below = panel["edge_mean"] < bar
    panel["verdict"] = np.where(below & (action == "drop"), "DESCARTAR", "MANTENER")

    bars = {"kind": "bars", "title": f"Edge medio por estrategia — umbral {bar} spreads",
           "unit": "spreads", "reference": bar,
           "items": [{"label": s, "value": float(v), "error": None,
                      "state": "fail" if v < bar else "pass"}
                     for s, v in panel["edge_mean"].items()]}
    table = blocks.table("Todas", panel.reset_index(), "edge en spreads = bruto medio / "
                         "coste de ida y vuelta modelado hoy; c* es el mismo número.")
    population = envelope.envelope(
        MODULE, None, None, cfg, started,
        [envelope.tab("panel", "Cada estrategia contra su coste", [bars, table],
                      note=f"{int(below.sum())} de {len(panel)} por debajo de {bar} spreads "
                           f"({'sólo marcadas' if action == 'mark' else 'DESCARTAR en curate'})."
                      )], warnings=costs.warnings(asset), glossary=one.GLOSSARY)
    return {"population": population, "panel": panel}
