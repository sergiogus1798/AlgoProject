"""Family E: could this edge be zero, given how many trades there are and how they are shaped?"""

import numpy as np
from scipy import stats


def psr(pnl: np.ndarray, benchmark: float) -> dict:
    """Probabilistic Sharpe Ratio of a trade stream.

    Args:
        pnl: Net USD per trade.
        benchmark: Sharpe to beat, per trade. Zero asks whether there is any edge at all.

    Returns:
        The observed per-trade Sharpe, its skew and kurtosis, and the probability that the
        true Sharpe exceeds the benchmark. Skew and fat tails enter the denominator, so a
        strategy whose profit sits in a few enormous trades gets a lower PSR than a
        normal-looking one with the same Sharpe. It is a point estimate, not a
        distribution: bootstrapping it would count the same sampling uncertainty twice.
    """
    n = pnl.size
    sr = float(pnl.mean() / pnl.std(ddof=1))
    skew = float(stats.skew(pnl))
    kurt = float(stats.kurtosis(pnl, fisher=False))
    var = 1 - skew * sr + (kurt - 1) / 4 * sr ** 2
    z = (sr - benchmark) * np.sqrt(n - 1) / np.sqrt(var)
    return {"sharpe": sr, "skew": skew, "kurtosis": kurt, "n": n,
            "psr": float(stats.norm.cdf(z))}


def crosscheck(psr_value: float, bootstrap_sharpe: np.ndarray) -> dict:
    """The analytic answer against the resampled one.

    Args:
        psr_value: What psr() returned as "psr".
        bootstrap_sharpe: Sharpe of every Family B simulation.

    Returns:
        Both probabilities that the edge is above zero and the gap between them. They are
        two pictures of the same question under different assumptions: agreement means the
        conclusion does not depend on the normal approximation, and a wide gap means the
        trades are skewed or fat-tailed enough that it does — which is a finding, not an
        error in either number.
    """
    empirical = float(np.mean(bootstrap_sharpe > 0))
    return {"psr": psr_value, "bootstrap": empirical,
            "gap": abs(psr_value - empirical)}
