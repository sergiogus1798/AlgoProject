"""Could this edge be zero? The Sharpe-based tests three studies now share, and nothing else."""

import numpy as np
from scipy import stats


def moments(returns: np.ndarray) -> tuple[float, float, float]:
    """Sharpe, skew and raw kurtosis of a per-observation series.

    Args:
        returns: One value per trade. Any scale -- USD P/L or log return -- since every
            statistic below is scale-invariant.

    Returns:
        (sharpe, skew, kurtosis). Sharpe is the plain mean over standard deviation with
        ddof=1, unannualised, because that is the unit the two formulas below need.
        Kurtosis is raw, 3 for a normal, not excess: `variance_factor`'s (kurtosis - 1) / 4
        term expects it that way and excess kurtosis silently shifts both answers.
    """
    sharpe = float(returns.mean() / returns.std(ddof=1))
    return sharpe, float(stats.skew(returns)), float(stats.kurtosis(returns, fisher=False))


def variance_factor(sharpe: float, skew: float, kurtosis: float) -> float:
    """How much the shape of the returns inflates the variance of their Sharpe estimate.

    Args:
        sharpe: Per-observation Sharpe.
        skew: Its skew.
        kurtosis: Its raw kurtosis, 3 for a normal.

    Returns:
        The factor both PSR and the minimum track-record length divide by. Negative skew
        and fat tails push it above 1, which is what makes a strategy whose profit sits in
        a few enormous trades score worse than a normal-looking one with the same Sharpe.
    """
    return 1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe ** 2


def psr(returns: np.ndarray, benchmark: float) -> dict:
    """Probabilistic Sharpe Ratio of a return series.

    Args:
        returns: One value per trade.
        benchmark: Sharpe to beat, per observation. Zero asks whether there is any edge.

    Returns:
        The observed Sharpe, its skew and kurtosis, the observation count, and the
        probability that the true Sharpe exceeds the benchmark. It is a point estimate,
        not a distribution: bootstrapping it would count the same sampling uncertainty
        twice.
    """
    sharpe, skew, kurtosis = moments(returns)
    z = (sharpe - benchmark) * np.sqrt(returns.size - 1) / np.sqrt(
        variance_factor(sharpe, skew, kurtosis))
    return {"sharpe": sharpe, "skew": skew, "kurtosis": kurtosis, "n": returns.size,
            "psr": float(stats.norm.cdf(z))}


def min_track_record(returns: np.ndarray, alpha: float = 0.05) -> dict:
    """Bailey / Lopez de Prado minimum track-record length.

    Args:
        returns: One value per trade.
        alpha: Significance level for the one-sided test that Sharpe > 0.

    Returns:
        How many observations the observed shape would need before Sharpe > 0 is
        significant, how many there are, and whether that is enough.
    """
    sharpe, skew, kurtosis = moments(returns)
    z = stats.norm.isf(alpha)
    needed = 1 + variance_factor(sharpe, skew, kurtosis) * (z / sharpe) ** 2
    return {"needed": float(needed), "have": len(returns), "enough": bool(len(returns) >= needed)}
