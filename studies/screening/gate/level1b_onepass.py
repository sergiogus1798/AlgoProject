"""Level 1b of the gate, one pass over the trades: edge against cost, concentration and MAE."""

import pandas as pd

from studies.screening.analysis import onepass, tradelevel

FACTS = (
    "edge_mean_oos",
    "t_exceso_k",
    "t_sin_mejor_trimestre",
    "t_sin_3_mejores",
    "mae_p95_r",
)


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """R5c, R8 and R9b for the strategies alive, all on oos1.

    Args:
        data: The harvest as `inputs.load` gives it, plus `oos` (level 1a's per-trade table,
            never recomputed here) and `market["risk"]`, 1R; MAE comes from
            `trades["MAE ($)"]` of the OOS sample.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `drift.se_skew_kurt`, `cost_stress.k`,
            `concentration.drop_trades` / `drop_period` and `mae.percentile`.

    Returns:
        One row per identity, one column per fact of `FACTS`. `mae_p95_r` is positive.
    """
    if not data:  # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=pd.Index(FACTS), dtype=float)
    oos = data["oos"]
    t = tradelevel.t_skew_kurt if cfg["drift"]["se_skew_kurt"] else tradelevel.t
    conc, trades = cfg["concentration"], data["trades"]
    mae = onepass.mae_pct(
        trades[trades["sample"] == "OOS"],
        data["market"]["risk"],
        cfg["mae"]["percentile"],
    )
    return pd.DataFrame(
        {
            "edge_mean_oos": onepass.edge_mean(oos),
            "t_exceso_k": onepass.t_cost(oos, cfg["cost_stress"]["k"], t),
            **onepass.t_without(oos, t, conc["drop_trades"], conc["drop_period"]),
            "mae_p95_r": mae,
        }
    ).reindex(index=alive, columns=pd.Index(FACTS))
