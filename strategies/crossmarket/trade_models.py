"""How a random run's trades are drawn: the study's modelling assumptions, and its alternatives."""

import numpy as np
import pandas as pd
from scipy import stats

MIN_HOLD = 1    # a trade that opens and closes on the same bar is not a trade


def _moments(shifted: np.ndarray) -> tuple[float, float]:
    """Mean and variance of counts already shifted to start at zero.

    Args:
        shifted: Observed counts minus MIN_HOLD.

    Returns:
        Mean and variance. Which distribution is fitted depends only on these two, so both
        the sampler and the goodness-of-fit check read them from here and cannot disagree.
    """
    return float(shifted.mean()), float(shifted.var())


def _overdispersed(mean: float, var: float) -> tuple[float, float]:
    """Negative binomial parameters matching a mean and a larger variance.

    Args:
        mean: Mean of the shifted counts.
        var: Variance, which must exceed the mean or the parameters are undefined.

    Returns:
        The number of successes and the success probability, by moment matching.
    """
    successes = mean ** 2 / (var - mean)
    return successes, successes / (successes + mean)


def _fit(values: np.ndarray, draws: int, size: int, rng: np.random.Generator) -> np.ndarray:
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
    mean, var = _moments(values - MIN_HOLD)
    if var <= mean:
        return MIN_HOLD + rng.poisson(mean, size=(draws, size))
    return MIN_HOLD + rng.negative_binomial(*_overdispersed(mean, var), size=(draws, size))


def _lay(holds: np.ndarray, gaps: np.ndarray, n_bars: int,
         rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Place a sequence of holds and gaps end to end from a random start bar.

    Args:
        holds: A (draws, trades) array of holding times in bars.
        gaps: A (draws, trades) array of flat bars before each trade.
        n_bars: Bars in the market.
        rng: Seeded generator.

    Returns:
        Entry indices and holds, wrapped circularly. Non-overlap holds by construction, since
        every trade starts after the previous one has closed.
    """
    start = rng.integers(0, n_bars, size=(holds.shape[0], 1))
    step = holds + gaps
    return (start + np.cumsum(step, axis=1) - step[:, :1]) % n_bars, holds


def block_shift(held: pd.DataFrame, market: dict, draws: int,
                rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Move each regime block's real trades by a whole number of weeks inside that block.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned for this market.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry indices and holds. Randomises the placement and nothing else: the count, the
        holds, the gaps, the clustering, the weekday and the hour are all the real ones. It is
        the only model here under which the real run and the random ones differ in exactly one
        thing, which is why it is the one the verdict uses.
    """
    entry = held["entry"].to_numpy()
    block, index = market["block"], market["calendar"]
    ids = block[entry]
    out = np.empty((draws, entry.size), dtype=np.int64)
    for b in np.unique(ids):
        member = ids == b
        here = entry[member]
        weeks = rng.integers(0, index["size"][here].max(), size=(draws, 1))
        rank = index["pos"][here] - index["start"][here]
        out[:, member] = index["order"][index["start"][here]
                                        + (rank + weeks) % index["size"][here]]
    return out, np.repeat(held["hold"].to_numpy()[None, :], draws, axis=0)


def segment_permute(held: pd.DataFrame, market: dict, draws: int,
                    rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Reorder the real hold-and-gap segments and lay them from a random start bar.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry indices and holds. Keeps the holds and gaps as multisets but randomises their
        order, so it also destroys the clustering and the calendar. A run without clustering
        has a smaller variance, which makes the real run look more extreme than it is: this
        answers a weaker question and is reported as a check, never as the verdict.
    """
    order = np.argsort(rng.random((draws, len(held))), axis=1)
    holds = held["hold"].to_numpy()[order]
    return _lay(holds, market["gaps"][order], market["n_bars"], rng)


def resampled_holds(held: pd.DataFrame, market: dict, draws: int,
                    rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Draw holds and gaps with replacement from the real ones, and lay them out.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry indices and holds. Unlike segment_permute the multiset is not preserved — a hold
        can appear twice and another not at all — so the run's total time in the market varies
        between draws. That makes it a test of the trading rhythm rather than of this exact
        realisation of it.
    """
    shape = (draws, len(held))
    pick = rng.integers(0, len(held), size=shape)
    return _lay(held["hold"].to_numpy()[pick], market["gaps"][pick], market["n_bars"], rng)


def fitted_holds(held: pd.DataFrame, market: dict, draws: int,
                 rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Fit a distribution to the real holds and gaps, and draw new ones from it.

    Args:
        held: What envelope.occupancy() returned.
        market: What envelope.describe() returned.
        draws: How many runs.
        rng: Seeded generator.

    Returns:
        Entry indices and holds. The holds are no longer the real ones, so this model differs
        from the real run in two things at once and cannot attribute what it finds to entry
        timing alone. It answers a different and still useful question: whether a system with
        this *shape* of holding time, entering at random, would have done as well.
    """
    shape = (draws, len(held))
    holds = _fit(held["hold"].to_numpy(), *shape, rng)
    return _lay(holds, _fit(market["gaps"] + MIN_HOLD, *shape, rng) - MIN_HOLD,
                market["n_bars"], rng)


MODELS = {"block_shift": block_shift, "segment_permute": segment_permute,
          "resampled_holds": resampled_holds, "fitted_holds": fitted_holds}

# What each model holds fixed and what it randomises. A model that randomises more than one
# thing cannot attribute a low p-value to any single cause, which is why the verdict uses
# block_shift and the others are read beside it.
RANDOMISES = {"block_shift": "placement, within the regime block and the weekday-hour slot",
              "segment_permute": "placement, order, clustering and calendar",
              "resampled_holds": "placement, which holds and gaps occur, and time in market",
              "fitted_holds": "placement, and the holding times themselves"}


def goodness(held: pd.DataFrame, gaps: np.ndarray) -> dict:
    """How well the fitted distributions describe the real holds and gaps.

    Args:
        held: What envelope.occupancy() returned.
        gaps: Flat bars before each trade.

    Returns:
        Dispersion (variance over mean) and a two-sided KS p-value against the fitted model,
        per quantity. Reported whenever fitted_holds is used: a fit that the data rejects makes
        that model's result a statement about the wrong distribution.
    """
    out = {}
    for name, values in (("hold", held["hold"].to_numpy()), ("gap", gaps + MIN_HOLD)):
        shifted = values - MIN_HOLD
        mean, var = _moments(shifted)
        fitted = stats.poisson(mean) if var <= mean else stats.nbinom(*_overdispersed(mean, var))
        out[f"{name}_dispersion"] = float(var / mean)
        out[f"{name}_ks_p"] = float(stats.ks_1samp(shifted, fitted.cdf).pvalue)
    return out
