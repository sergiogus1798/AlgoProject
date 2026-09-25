"""Item 2: whether trades are independent, which decides what the portfolio may resample."""

import numpy as np
from scipy import stats


def runs(wins: np.ndarray) -> dict:
    """Wald-Wolfowitz on the win/loss sequence.

    Args:
        wins: One boolean per trade, in time order.

    Returns:
        The number of runs, its expectation and variance under independence, and z.
        z below about -2 means wins and losses cluster, and a drawdown drawn by shuffling
        trades is then optimistic -- which is exactly what SQX's trade-shuffling Monte
        Carlo does.
    """
    n1, n2, n = int(wins.sum()), int((~wins).sum()), wins.size
    observed = 1 + int((wins[1:] != wins[:-1]).sum())
    mean = 2 * n1 * n2 / n + 1
    var = 2 * n1 * n2 * (2 * n1 * n2 - n) / (n ** 2 * (n - 1))
    return {"runs": observed, "expected": float(mean), "z": float((observed - mean)
                                                                  / np.sqrt(var)),
            "p": float(2 * stats.norm.sf(abs((observed - mean) / np.sqrt(var))))}


def ljung_box(x: np.ndarray, lags: int) -> dict:
    """Ljung-Box on a series, for autocorrelation at any lag up to `lags`.

    Args:
        x: Trade P&L in trade order, or daily P&L in calendar time.
        lags: How many lags to pool.

    Returns:
        Q, its p under chi-squared with `lags` degrees of freedom, and the largest lag
        whose own autocorrelation clears two standard errors. That last number is what the
        portfolio stage needs: it is the shortest block a block bootstrap may use and still
        break the dependence.
    """
    centred = x - x.mean()
    n = x.size
    rho = np.array([float(np.dot(centred[k:], centred[:-k]) / np.dot(centred, centred))
                    for k in range(1, lags + 1)])
    q = n * (n + 2) * float(np.sum(rho ** 2 / (n - np.arange(1, lags + 1))))
    significant = np.flatnonzero(np.abs(rho) > 2 / np.sqrt(n))
    return {"q": q, "p": float(stats.chi2.sf(q, lags)), "rho": rho,
            "last_significant": int(significant[-1] + 1) if significant.size else 0}


def longest_losing(wins: np.ndarray) -> int:
    """The longest run of consecutive losses.

    Args:
        wins: One boolean per trade, in time order.

    Returns:
        Its length in trades.
    """
    best = run = 0
    for won in wins:
        run = 0 if won else run + 1
        best = max(best, run)
    return best


def streak(wins: np.ndarray, draws: int, seed: int) -> dict:
    """The observed losing streak against the streaks independence would produce.

    Args:
        wins: One boolean per trade, in time order.
        draws: How many shuffles.
        seed: Seeded generator.

    Returns:
        The observed streak, the median and the 95th percentile of the shuffled ones, and
        the empirical p. Shuffling holds the win rate and the trade count exactly fixed
        and destroys only the order, so anything left is order.
    """
    rng = np.random.default_rng(seed)
    drawn = np.array([longest_losing(rng.permutation(wins)) for _ in range(draws)])
    observed = longest_losing(wins)
    return {"observed": observed, "median": float(np.median(drawn)),
            "p95": float(np.quantile(drawn, 0.95)),
            "p": float((1 + (drawn >= observed).sum()) / (draws + 1))}
