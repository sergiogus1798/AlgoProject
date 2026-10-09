"""The order of the variants on the main market against another market's: ties, and the weighted mean."""

import numpy as np
import pandas as pd


def tie_share(values: np.ndarray) -> float:
    """The share of variants whose value on a market is exactly another variant's.

    Args:
        values: One value per variant.

    Returns:
        0 when every value is its own; 1 when no variant stands alone. A parameter that
        does nothing on a market leaves distinct variants with one trade list there.
    """
    return float(pd.Series(values).duplicated(keep=False).mean())


def joint(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """The weighted mean over markets of one statistic, or of every draw of it.

    Args:
        values: One per market, or draws x markets.
        weights: One per market.

    Returns:
        One mean, or one per draw. A market whose value is not finite is left out of that
        mean, with its weight; NaN where none is.
    """
    ok = np.isfinite(values)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (np.where(ok, values, 0.0) @ weights) / (ok @ weights)


def weights(group: np.ndarray) -> np.ndarray:
    """The weight of each market that enters a mean.

    Args:
        group: `declared`'s `group` of the markets in the mean, and only of those.

    Returns:
        1 for a market outside every group; a group shares a total of 1 among its members
        present, so three near-identical markets weigh 1/3 each and two left of three, 1/2.
    """
    group = np.asarray(group)
    size = pd.Series(group).map(pd.Series(group).value_counts()).to_numpy()
    return np.where(group < 0, 1.0, 1.0 / size)
