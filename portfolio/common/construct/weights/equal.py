"""Equal weight: 1/K to every member -- the baseline every later method must beat."""

import pandas as pd


def weights(build_daily: pd.DataFrame, cfg: dict) -> dict:
    """1/K per member; holds everything fixed, estimates nothing.

    Args:
        build_daily: build days x the combination's members; only its columns are read.
        cfg: The construct config (unused: the method has no knob).

    Returns:
        Column label -> 1/K.
    """
    return {member: 1.0 / build_daily.shape[1] for member in build_daily.columns}
