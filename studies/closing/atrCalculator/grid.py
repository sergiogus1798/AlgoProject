"""The X values SQX retests around each percentile's X, written for `sqx.variants.stopgrid`."""

import pandas as pd

FILE = "stopgrid.csv"


def rows(strategy: str, xs: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """The stability grid of one strategy.

    Args:
        strategy: The mother's name, which is also its `.sqx` stem.
        xs: What `threshold.x_values` returned.
        cfg: The study's config.

    Returns:
        One row per (percentile, step): `x * (1 + band * step / steps)` for step in
        -steps..steps, so step 0 is the X itself. Rounded to 4 decimals, which is finer than
        any ATR a stop reads and what the variant file will hold.
    """
    band, steps = cfg["grid"]["band"], cfg["grid"]["steps"]
    return pd.DataFrame([{"strategy": strategy, "percentile": r.percentile, "step": k,
                          "x": round(r.x * (1 + band * k / steps), 4)}
                         for r in xs.itertuples() for k in range(-steps, steps + 1)])
