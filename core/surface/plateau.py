"""How much of a grid works, and whether its best point beats what pure search would give."""

from typing import TypedDict

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
    best = (
        values.max()
    )  # |best|, as `plateau_fraction`: on a negative best `best / 2` sits above it
    return float((values > best - abs(best) / 2).mean())


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
    if n_eff <= 1:
        return 0.0
    a = stats.norm.isf(1 / n_eff)
    b = stats.norm.isf(1 / (n_eff * np.e))
    return float(sigma_sr * ((1 - EULER) * a + EULER * b))


class Deflated(TypedDict):
    """A Sharpe against the benchmark its own search sets."""

    benchmark: float
    sharpe: float
    n_eff: int
    dsr: float
    state: str


def deflated_sharpe(
    sharpe: float,
    sigma_sr: float,
    n_eff: int,
    n_obs: float,
    skew: float,
    kurtosis: float,
) -> Deflated:
    """Is this Sharpe real, given how many configurations were tried to find it?

    Args:
        sharpe: The selected configuration's Sharpe, **per observation**.
        sigma_sr: Standard deviation of the trial Sharpes, in the **same unit**.
        n_eff: Trials with a distinct result.
        n_obs: Observations behind `sharpe`.
        skew: Skew of that configuration's returns.
        kurtosis: Raw kurtosis, 3 for a normal, as `core.significance.moments` returns it.

    Returns:
        The benchmark, the probability the true Sharpe clears it, and `state` ("undefined"
        when that probability is NaN: a flat series, not a fail). **Both Sharpes must
        be in the same unit**: SQX stores annualised ones and `core.significance` works
        per observation, and mixing the two produces a number that looks reasonable and
        means nothing. Convert before calling.
    """
    benchmark = expected_max_sharpe(sigma_sr, n_eff)
    z = (
        (sharpe - benchmark)
        * np.sqrt(n_obs - 1)
        / np.sqrt(variance_factor(sharpe, skew, kurtosis))
    )
    return {
        "benchmark": benchmark,
        "sharpe": sharpe,
        "n_eff": n_eff,
        "dsr": float(stats.norm.cdf(z)),
        "state": "undefined" if np.isnan(z) else "measured",
    }


def effective_n(returns: np.ndarray) -> float:
    """How many independent observations an autocorrelated return series is worth.

    Args:
        returns: One return per period, in time order (daily P&L, any constant unit).

    Returns:
        `n / (1 + 2 Σ_k w_k ρ_k)` over lags k = 1..L, with Newey and West's (1994) automatic
        truncation L = floor(4 (n/100)^(2/9)) (8 lags for ten years of days) and Bartlett
        weights w_k = 1 - k/(L+1): the same long-run variance a HAC standard error uses, and
        the Bartlett kernel keeps it non-negative where raw ρ sums can go below -1/2. Capped
        at n: a negative ρ estimate on a short series is mostly noise, and deflation must
        never grant more certainty than the i.i.d. count. NaN with fewer than 3 returns or
        a flat series. Written beside `deflated_sharpe`'s i.i.d. `n_obs` (encargo 75 E);
        production does not read it until the owner says so.
    """
    x = np.asarray(returns, dtype=np.float64)
    n = x.size
    if n < 3 or not np.isfinite(x).all():
        return float("nan")
    d = x - x.mean()
    var = float(d @ d)
    if var <= 0:
        return float("nan")
    lags = max(1, min(n - 2, int(4 * (n / 100) ** (2 / 9))))
    rho = np.array([float(d[k:] @ d[:-k]) / var for k in range(1, lags + 1)])
    weights = 1 - np.arange(1, lags + 1) / (lags + 1)
    return float(min(n, n / max(1 + 2 * float(weights @ rho), 1 / n)))


def rank_of(values: np.ndarray, reference: float) -> float:
    """Where one chosen point sits among every point of its own grid.

    Args:
        values: One value per distinct tuple, the reference included or not.
        reference: The chosen point's value, in the same metric.

    Returns:
        The fraction of the grid the reference beats, so 1.0 means nothing did better.
        Read it with `plateau_fraction`: a rank near 1 is only alarming when almost
        nothing else comes close, which is the shape of a point picked off a noise peak.
    """
    return float((values <= reference).mean())


def plateau_fraction(values: np.ndarray, reference: float, delta: float = 0.2) -> float:
    """How much of the grid performs within a given shortfall of the chosen point.

    Args:
        values: One value per distinct tuple.
        reference: The chosen point's value.
        delta: Relative shortfall still counted as company, 0.2 for "within 20%".

    Returns:
        A probability. The floor is `reference - delta * |reference|` rather than
        `(1 - delta) * reference`: on a metric that goes negative the second form raises
        the bar above the reference itself and the fraction stops meaning anything.
    """
    return float((values >= reference - delta * abs(reference)).mean())


def shrunk(values: np.ndarray) -> float:
    """What a point drawn from this neighbourhood is worth on average.

    Args:
        values: One value per distinct tuple of the neighbourhood.

    Returns:
        The median. It is the number to carry into any downstream expectation instead of
        the chosen point's own: the chosen point was selected, its neighbours were not.
    """
    return float(np.median(values))
