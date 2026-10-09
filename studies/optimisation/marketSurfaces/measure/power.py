"""The planted transmission: a no-edge draw of a market with the main market's order mixed in."""

import numpy as np
from scipy.stats import norm, rankdata

from engines.weekly import flip


def scores(values: np.ndarray) -> np.ndarray:
    """Normal scores of the ranks along the last axis: mean 0, the same spread in every row."""
    rank = rankdata(values, axis=-1)
    return norm.ppf((rank - 0.5) / values.shape[-1])


def planted(main: np.ndarray, flipped: np.ndarray, rho: float) -> np.ndarray:
    """Spearman of the main market with each no-edge draw once a true rho is planted in it.

    The draw's normal scores z and the main market's x are mixed as r x + sqrt(1 - r^2) z,
    with r = 2 sin(pi rho / 6): for a Gaussian pair of Pearson r, Spearman's rho is exactly
    `rho`. The draw keeps its own chance correlation with the main market, so the planted
    family is as noisy as the real one.

    Args:
        main: The main market's excess, one per variant.
        flipped: draws x variants: the other market's excess under the sign-flip null.
        rho: The true Spearman planted.

    Returns:
        One rho per draw.
    """
    r = 2 * np.sin(np.pi * rho / 6)
    return flip.spearman(main, r * scores(main) + np.sqrt(1 - r * r) * scores(flipped))


def detected(statistic: np.ndarray, null: np.ndarray, alpha: float) -> float:
    """The share of planted draws the step reads as a positive order.

    Args:
        statistic: The joint rho of each planted draw.
        null: The joint rho of each draw of the null the real family is read against.
        alpha: The cut on p+.

    Returns:
        The share whose p+ = (1 + #{null >= it}) / (1 + B) is at or under alpha.
    """
    above = len(null) - np.searchsorted(np.sort(null), statistic, side="left")
    return float(((1 + above) / (1 + len(null)) <= alpha).mean())
