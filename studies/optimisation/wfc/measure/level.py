"""Does what an optimiser would pick win out of sample: the in-sample top and its out-of-sample median."""

import numpy as np


def top(inside: np.ndarray, share: float) -> np.ndarray:
    """The variants an optimiser would pick: in-sample value at or above the 1 - share quantile.

    Args:
        inside: One in-sample value per variant.
        share: 0.20 for the best fifth.

    Returns:
        A boolean mask; with ties it holds somewhat more than `share` of the variants.
    """
    return inside >= np.quantile(inside, 1.0 - share)


def p_value(tops: np.ndarray, observed: float) -> float:
    """The share of null draws whose top median is at or above the observed one.

    Args:
        tops: One per draw, the median over `top()`'s variants of the out-of-sample excess
            per year under the sign-flip null.
        observed: The out-of-sample median of the in-sample top.

    Returns:
        (1 + draws at or above) / (1 + draws): the observed counted among them, as `order.tails`.
    """
    return float((1 + (tops >= observed).sum()) / (1 + len(tops)))


def premium(values: np.ndarray, best: np.ndarray) -> np.ndarray:
    """Median of the top minus the median of every variant, along the last axis."""
    return np.median(values[..., best], axis=-1) - np.median(values, axis=-1)


def retention(inside: np.ndarray, outside: np.ndarray, best: np.ndarray,
              min_gap: float) -> np.ndarray | None:
    """How much of the top's in-sample premium over the whole family survives out of sample.

    Args:
        inside: One in-sample value per variant.
        outside: The same variants out of sample, or draws x variants.
        best: What top() returned.
        min_gap: The in-sample premium must exceed this share of the in-sample
            interquartile range.

    Returns:
        premium(outside) / premium(inside): 1 keeps it whole, 0 means choosing buys nothing,
        negative is perverse selection. None when the in-sample premium is too small to
        divide by: the quotient would be a large number that measures nothing.
    """
    gap = float(premium(inside, best))
    q75, q25 = np.percentile(inside, [75, 25])
    if not gap > min_gap * (q75 - q25):
        return None
    return premium(outside, best) / gap
