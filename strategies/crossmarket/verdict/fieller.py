"""Fieller's interval for a ratio whose denominator is noisy — the honest CI for E.

A percentile bootstrap on a ratio quietly returns a finite interval even when the denominator
cannot be told from zero, which is exactly when the ratio has no finite interval at all.
Fieller's theorem returns the unbounded one instead, and says so."""

import math

import numpy as np

# Below this the denominator is not distinguishable from zero at the interval's own level and
# the ratio has no finite bounds: Fieller's g crosses 1 and the quadratic stops having two
# real roots on the same side. It is not a threshold anyone chose — it falls out of the algebra.
UNBOUNDED = 1.0


def interval(num: float, den: float, var_num: float, var_den: float, cov: float,
             z: float) -> dict:
    """The ratio num/den and its Fieller confidence interval.

    Args:
        num: Mean of the numerator — here the mean bar return while a trade was open.
        den: Mean of the denominator — the market's own mean bar return.
        var_num, var_den: Their sampling variances.
        cov: Their covariance. The occupied bars are a subset of the market's own, so the two
            estimates move together and assuming independence would understate the interval.
        z: Normal quantile of the interval, e.g. 1.645 for 90%.

    Returns:
        Keys ratio, lo, hi and bounded. When `bounded` is False the data do not bound the
        ratio at this level: lo and hi are -inf and +inf, and the number to read is the
        drift-neutral excess A, which subtracts instead of dividing.
    """
    g = z * z * var_den / (den * den) if den else float("inf")
    ratio = num / den if den else float("nan")
    if not (g < UNBOUNDED):
        return {"ratio": ratio, "lo": -math.inf, "hi": math.inf, "bounded": False}
    centre = (ratio - g * cov / var_den) / (1 - g)
    inside = var_num - 2 * ratio * cov + ratio * ratio * var_den - g * (
        var_num - cov * cov / var_den)
    half = z / (abs(den) * (1 - g)) * math.sqrt(max(inside, 0.0))
    return {"ratio": ratio, "lo": centre - half, "hi": centre + half, "bounded": True}


def moments(num_draws: np.ndarray, den_draws: np.ndarray) -> dict:
    """The two means, their variances and their covariance, from paired bootstrap replicates.

    Args:
        num_draws: Numerator of each replicate.
        den_draws: Denominator of the same replicate, resampled together with it.

    Returns:
        The keyword arguments interval() needs. Taking both from the same replicate is the
        whole point: it is what carries the dependence between the occupied bars and the
        market they are a subset of.
    """
    return {"num": float(num_draws.mean()), "den": float(den_draws.mean()),
            "var_num": float(num_draws.var(ddof=1)), "var_den": float(den_draws.var(ddof=1)),
            "cov": float(((num_draws - num_draws.mean())
                          * (den_draws - den_draws.mean())).mean())}
