"""The top-20 % premium: what picking by the main market buys on another one, in units of its spread."""

import numpy as np


def top(values: np.ndarray, usable: np.ndarray, share: float) -> np.ndarray:
    """The variants an optimiser would pick on the main market.

    Args:
        values: The main market's net excess, one per variant.
        usable: Which variants count there.
        share: The top share, e.g. 0.2.

    Returns:
        A mask over every variant: the usable ones at or above the usable ones' (1 - share)
        quantile.
    """
    return usable & (values >= np.quantile(values[usable], 1 - share))


def premium(excess: np.ndarray, best: np.ndarray) -> np.ndarray:
    """Median of the main market's top minus the median of all, over the interquartile range.

    Args:
        excess: One market's net excess, one per variant, or draws x variants.
        best: Which of those variants are the main market's top.

    Returns:
        One premium, or one per draw; NaN without a top or with a flat market.
    """
    if not best.any():
        return np.full(excess.shape[:-1], np.nan)
    low, mid, high = np.percentile(excess, [25, 50, 75], axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(
            high > low,
            (np.median(excess[..., best], axis=-1) - mid) / (high - low),
            np.nan,
        )
