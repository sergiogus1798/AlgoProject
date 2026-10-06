"""How far a surface moved between two windows, in units and in rank."""

import numpy as np
from scipy import stats

WALSH_CAP = 4000


def hodges_lehmann(before: np.ndarray, after: np.ndarray, seed: int = 0) -> float:
    """Median paired shift, in the metric's own units.

    Args:
        before: One value per distinct tuple, in the first window.
        after: The same tuples in the same order, in the second.
        seed: Fixes the subsample below.

    Returns:
        The median of the Walsh averages of the differences -- the paired estimator, which
        is what a saturated grid supports and what an unpaired one cannot see. Above
        WALSH_CAP differences the pairs are subsampled without replacement, because the
        estimator is quadratic in n and the grid is not.
    """
    diff = after - before
    if diff.size > WALSH_CAP:
        diff = np.random.default_rng(seed).choice(diff, WALSH_CAP, replace=False)
    i, j = np.triu_indices(diff.size)
    return float(np.median((diff[i] + diff[j]) / 2))


def cliff_delta(before: np.ndarray, after: np.ndarray) -> float:
    """Probability of superiority, rescaled so that nothing happening reads as zero.

    Args:
        before: Values in the first window.
        after: Values in the second. Need not pair with `before` and need not match length.

    Returns:
        2*P(after > before) - 1, from the Mann-Whitney statistic. Dimensionless and robust,
        so it survives the heavy tails these metrics carry: 0 is "the surface did not move",
        -1 is "every point of the second window is below every point of the first".
    """
    u = stats.mannwhitneyu(after, before, alternative="two-sided").statistic
    return float(2 * u / (after.size * before.size) - 1)


def tail_excess(before: np.ndarray, after: np.ndarray,
                tail: float = 0.95, middle: float = 0.50) -> float:
    """How much further the tail fell than the middle did.

    Args:
        before: Values in the first window.
        after: Values in the second.
        tail: The upper quantile read as the tail.
        middle: The quantile read as the middle.

    Returns:
        [Q_before(tail) - Q_after(tail)] - [Q_before(middle) - Q_after(middle)]. Zero means
        the surface fell in one piece; positive means the peak collapsed faster than the
        plateau.
    """
    return float((np.quantile(before, tail) - np.quantile(after, tail))
                 - (np.quantile(before, middle) - np.quantile(after, middle)))


def dispersion_ratio(before: np.ndarray, after: np.ndarray,
                     n_before: float, n_after: float) -> float:
    """Whether the parameters still govern the result, or noise took over.

    Args:
        before: Values in the first window.
        after: Values in the second.
        n_before: Trades behind a point of the first window -- the median over the grid.
        n_after: The same for the second.

    Returns:
        (IQR_after / IQR_before) divided by sqrt(n_before / n_after). The division removes
        the widening that a shorter window produces mechanically, since the standard error
        of these metrics falls with 1/sqrt(n). Above 1 after the adjustment the spread is
        real: the parameters stopped deciding the outcome.
    """
    iqr_before = float(np.subtract(*np.quantile(before, [0.75, 0.25])))
    iqr_after = float(np.subtract(*np.quantile(after, [0.75, 0.25])))
    return (iqr_after / iqr_before) / np.sqrt(n_before / n_after)
