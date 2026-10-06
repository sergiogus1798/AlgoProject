"""Level 3c of the gate: the strategy against monkeys drawn inside R3's drift window."""

import pandas as pd

from engines.nulls.model import RUNGS

FACTS = ("z_mono", "mono_p", *(f"z_mono_{rung}" for rung in RUNGS), "mono_seed")


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Skeleton (encargo 44, package 0): every fact empty until its package fills it.

    Args:
        data: The harvest as `inputs.load` gives it; from level 1a on also `oos`, the
            per-trade table of oos1 (`operaciones.parquet`).
        alive: Identities still in the cascade.
        cfg: The gate's config.

    Returns:
        One row per identity, one column per fact of `FACTS`. Only `z_mono` is judged; the p and the
        per-rung z annotate.
    """
    return pd.DataFrame(index=alive, columns=list(FACTS), dtype=float)
