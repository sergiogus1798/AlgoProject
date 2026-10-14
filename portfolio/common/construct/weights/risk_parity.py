"""Risk parity as AlphaForge defines it: each member weighted by 1 / its daily volatility."""

import numpy as np
import pandas as pd


def weights(build_daily: pd.DataFrame, cfg: dict) -> dict[str, float]:
    """Inverse volatility, normalised to 1; holds correlations at zero, estimates K volatilities.

    Args:
        build_daily: estimation days x the combination's members, P&L per unit of risk.
        cfg: The construct config (unused: the method has no knob).

    Returns:
        Column label -> weight.

    Raises:
        ValueError: A member does not vary on the estimation days: it has no volatility to
            weigh by, and no other method is substituted.
    """
    sigma = (
        build_daily.to_numpy().std(axis=0, ddof=1)
        if len(build_daily) > 1
        else np.zeros(build_daily.shape[1])
    )
    if build_daily.shape[1] > 1 and not (sigma > 0).all():
        flat = [str(c)[:12] for c, s in zip(build_daily.columns, sigma) if not s > 0]
        raise ValueError(f"sin volatilidad en los días de estimación: {flat}")
    inverse = np.ones(1) if build_daily.shape[1] == 1 else 1.0 / sigma
    return dict(zip(build_daily.columns, (inverse / inverse.sum()).tolist()))
