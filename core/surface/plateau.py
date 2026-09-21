"""How much of a grid works, and whether its best point beats what pure search would give."""

import numpy as np
from scipy import stats

from core.significance import variance_factor

EULER = 0.5772156649015329


def plateau_area(values: np.ndarray, breakeven: float = 0.0) -> float:
    """Fraction of the grid that makes money.

    Args:
        values: One value per distinct tuple.
        breakeven: Where the metric stops being profitable. Zero for Sharpe, Ret/DD and
            anything that goes negative; 1.0 for profit factor.

    Returns:
        A probability, so it compares across metrics, strategies and windows without any
        rescaling. Read against the same number on the other window: a peak that collapses
        while the plateau holds is the real diagnosis of overfitting.
    """
    return float((values > breakeven).mean())


def above_half_max(values: np.ndarray) -> float:
    """Fraction of the grid within half of its own window's best point.

    Args:
        values: One value per distinct tuple.

    Returns:
        A probability. Normalising by each window's own maximum is what makes the IS and
        OOS numbers comparable when the whole surface dropped: it asks about shape, not
        level.
    """
    return float((values > values.max() / 2).mean())


def expected_max(sigma: float, n_eff: int) -> float:
    """The best score a grid of pure noise would still produce.

    Args:
        sigma: Dispersion of the grid's values.
        n_eff: Tuples with a distinct result. **Not** the row count -- inert parameters
            duplicate points, and feeding rows inflates the threshold.

    Returns:
        sigma * sqrt(2 * ln n_eff). If the grid's best point does not clearly beat this,
        no parameter is doing anything and the family is noise: neither the saturated
        phase nor the 5,000 variants are worth running.
    """
    return float(sigma * np.sqrt(2 * np.log(n_eff)))


def expected_max_sharpe(sigma_sr: float, n_eff: int) -> float:
    """Bailey and Lopez de Prado's sharper estimate of the same threshold.

    Args:
        sigma_sr: Standard deviation of the Sharpe ratios across the trials, ddof=1.
        n_eff: Trials with a distinct result.

    Returns:
        The expected maximum of n_eff independent draws. It sits below the sqrt(2 ln N)
        bound and is the benchmark the deflated Sharpe subtracts.
    """
    a = stats.norm.isf(1 / n_eff)
    b = stats.norm.isf(1 / (n_eff * np.e))
    return float(sigma_sr * ((1 - EULER) * a + EULER * b))


def deflated_sharpe(sharpe: float, sigma_sr: float, n_eff: int, n_obs: int,
                    skew: float, kurtosis: float) -> dict:
    """Is this Sharpe real, given how many configurations were tried to find it?

    Args:
        sharpe: The selected configuration's Sharpe, **per observation**.
        sigma_sr: Standard deviation of the trial Sharpes, in the **same unit**.
        n_eff: Trials with a distinct result.
        n_obs: Observations behind `sharpe`.
        skew: Skew of that configuration's returns.
        kurtosis: Raw kurtosis, 3 for a normal, as `core.significance.moments` returns it.

    Returns:
        The benchmark, and the probability the true Sharpe clears it. **Both Sharpes must
        be in the same unit**: SQX stores annualised ones and `core.significance` works
        per observation, and mixing the two produces a number that looks reasonable and
        means nothing. Convert before calling.
    """
    benchmark = expected_max_sharpe(sigma_sr, n_eff)
    z = (sharpe - benchmark) * np.sqrt(n_obs - 1) / np.sqrt(
        variance_factor(sharpe, skew, kurtosis))
    return {"benchmark": benchmark, "sharpe": sharpe, "n_eff": n_eff,
            "dsr": float(stats.norm.cdf(z))}
