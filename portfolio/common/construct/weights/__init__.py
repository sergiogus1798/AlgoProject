"""The weight methods (PLAN §5.4): chosen on build, fixed for good (never rebalanced)."""

import numpy as np
import pandas as pd

from . import equal, hrp, min_variance, risk_parity

# equal is the one the search and the verdict use (`weights.method`); the rest are M8's
# candidates, estimated once and held, that `construct.wf` compares against it
REGISTRY = {"equal": equal.weights, "risk_parity": risk_parity.weights,
            "min_variance": min_variance.weights, "hrp": hrp.weights}


def matrix(build_daily: pd.DataFrame, members: np.ndarray, cfg: dict) -> np.ndarray:
    """Every combination's weights by `weights.method`, as one array the search multiplies by.

    Args:
        build_daily: build days x the pool's N members -- what a weight multiplies, here each
            member's P&L per unit of risk.
        members: bool [P, N], at least one member per row.
        cfg: The construct config (`weights.method`).

    Returns:
        float [P, N]: each row non-negative, summing to 1, 0 outside the combination.
    """
    method = REGISTRY[cfg["weights"]["method"]]
    out = np.zeros(members.shape)
    for row, mask in enumerate(members):
        # ponytail: one frame slice per combination (~0.1 ms); a method that reads only the
        # columns could take the mask instead if a GA's 30,000 calls ever show in perf
        got = method(build_daily.loc[:, mask], cfg)
        out[row, mask] = [got[member] for member in build_daily.columns[mask]]
    return out
