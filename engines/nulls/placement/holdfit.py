"""Fit a discrete distribution to observed holds and gaps, and say whether it fits."""

import numpy as np

MIN_HOLD = 1    # a trade that opens and closes on the same bar is not a trade


def moments(shifted: np.ndarray) -> tuple[float, float]:
    """Mean and variance of counts already shifted to start at zero.

    Args:
        shifted: Observed counts minus MIN_HOLD.

    Returns:
        Mean and variance. Which distribution is fitted depends only on these two, so both
        the sampler and the goodness-of-fit check read them from here and cannot disagree.
    """
    return float(shifted.mean()), float(shifted.var())


def overdispersed(mean: float, var: float) -> tuple[float, float]:
    """Negative binomial parameters matching a mean and a larger variance.

    Args:
        mean: Mean of the shifted counts.
        var: Variance, which must exceed the mean or the parameters are undefined.

    Returns:
        The number of successes and the success probability, by moment matching.
    """
    successes = mean ** 2 / (var - mean)
    return successes, successes / (successes + mean)


def fit(values: np.ndarray, draws: int, size: int, rng: np.random.Generator) -> np.ndarray:
    """Sample from a discrete distribution fitted to `values` by its first two moments.

    Args:
        values: Observed counts in bars, all at least MIN_HOLD.
        draws: Rows to produce.
        size: Values per row.
        rng: Seeded generator.

    Returns:
        A (draws, size) array of counts. Negative binomial when the observations are
        overdispersed and Poisson when they are not, both shifted so the support starts at
        MIN_HOLD. Which of the two was used is a property of the data, not a setting: a
        strategy with a fixed bar cap has zero variance and lands on the Poisson branch, where
        the fitted distribution is degenerate and reproduces the constant.
    """
    mean, var = moments(values - MIN_HOLD)
    if var <= mean:
        return MIN_HOLD + rng.poisson(mean, size=(draws, size))
    return MIN_HOLD + rng.negative_binomial(*overdispersed(mean, var), size=(draws, size))

