"""Every strategy of one harvest against its own edge-per-cost bar, as one result and one panel."""

import time
from typing import Any, TypedDict

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.edgeCost import costs, one

MODULE = one.MODULE


class Population(TypedDict):
    """The population run: the export's contract result and the per-strategy panel."""

    population: dict[str, Any]
    panel: pd.DataFrame


def run(priced: pd.DataFrame, names: pd.Series, cfg: dict, asset: dict) -> Population:
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
    by = priced.assign(gross=priced["pnl"] + priced["cost"]).groupby(
        "identity", observed=True
    )
    panel = pd.DataFrame(
        {"mean_gross": by["gross"].mean(), "mean_cost": by["cost"].mean()}
    )
    panel["edge_mean"] = panel["mean_gross"] / panel["mean_cost"]
    panel["strategy"] = names.reindex(panel.index)
    panel = panel.reset_index().set_index("strategy")
    bar, action = cfg["verdict"]["min_edge_spreads"], cfg["verdict"]["action"]
    below = panel["edge_mean"] < bar
    panel["verdict"] = np.where(below & (action == "drop"), "DESCARTAR", "MANTENER")
    shown = panel.reset_index()
    table = blocks.table(
        "Cada estrategia contra su coste",
        shown,
        f"Verde: edge medio por encima de {bar}. Rojo: por debajo "
        f"({'sólo marcadas' if action == 'mark' else 'DESCARTAR en curate'}). "
        "edge = bruto medio / coste pagado medio, sólo oos1.",
    )
    table["states"] = [
        ["pass" if not b else "fail"] * len(shown.columns) for b in below
    ]
    population = envelope.envelope(
        MODULE,
        None,
        None,
        cfg,
        started,
        [
            envelope.tab(
                "panel",
                "Cada estrategia contra su coste",
                [table],
                note=f"{int(below.sum())} de {len(panel)} por debajo de {bar} "
                f"({'sólo marcadas' if action == 'mark' else 'DESCARTAR en curate'}).",
            )
        ],
        warnings=costs.warnings(asset),
        glossary=one.GLOSSARY,
    )
    return {"population": population, "panel": panel}
