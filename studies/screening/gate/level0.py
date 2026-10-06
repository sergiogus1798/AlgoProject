"""Level 0 of the gate: in the retest, readable and not a clone, net of oos1, trades per year of the build."""

import pandas as pd

FACTS = ("presencia_passed", "sanidad_passed", "sanidad_value", "estaticas_value",
         "is_trades_per_year")


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Skeleton (encargo 44, package 0): every fact empty until its package fills it.

    Args:
        data: The harvest as `inputs.load` gives it; from level 1a on also `oos`, the
            per-trade table of oos1 (`operaciones.parquet`).
        alive: Identities still in the cascade.
        cfg: The gate's config.

    Returns:
        One row per identity, one column per fact of `FACTS`. `sanidad_value` is filled for every paired
        strategy, not only the ones alive.
    """
    return pd.DataFrame(index=alive, columns=list(FACTS), dtype=float)
