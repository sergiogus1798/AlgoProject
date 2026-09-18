"""Question 2 — does it decay, or collapse? Whether the outcome is one regime or two."""

import diptest
import numpy as np
from scipy import stats


def outcomes(values: np.ndarray) -> int:
    """How many distinct results a task actually produced.

    Args:
        values: One value per simulation.

    Returns:
        The count of distinct values, rounded to the cent the P/L is stored in. This is the
        number that decides whether a task produced a *distribution* or a short list, and
        it is not the same question as how far apart those values are.
    """
    return int(np.unique(np.round(np.asarray(values, dtype=np.float64), 2)).size)


def discriminated(values: np.ndarray, cfg: dict) -> bool:
    """Whether this task produced enough distinct outcomes for a distributional test.

    Args:
        values: One value per simulation.
        cfg: What inputs.config.load() returned.

    Returns:
        False when a thousand simulations landed on a handful of values. **The test is
        cardinality, not spread**, and that distinction was learned the hard way here: an
        earlier version compared the dispersion against the control's and let the exit task
        through, which then came back "bimodal" with p = 0.000 -- because it has **four to
        six distinct outcomes in a thousand runs**, so of course the density has gaps. That
        is not a hidden failure regime, it is a discrete variable, and a dip test cannot
        tell the difference.

        The test is a **share** of the simulations, not a count, because the failure has two
        shapes and a count only catches one. Minimum distance gives 1 outcome in 1,000, the
        starting bar 2 to 3, the exit parameters 2 to 6: those barely move at all. But spread
        gives 69 and slippage 100 -- not degenerate, yet still not distributions. SQX samples
        those from a grid, so a thousand runs land on seventy values and the density is a
        comb; the dip test then rejects unimodality on **every strategy**, and it is reading
        the gaps between grid points, not the strategy. Requiring most runs to give distinct
        values keeps the dip on the three tasks whose output really is continuous -- the
        strategy parameters, the price history and the combined stress.

        The right analysis for a grid-sampled task is a dose-response curve of the result
        against the parameter, which this study does not do yet.
    """
    values = np.asarray(values, dtype=np.float64)
    return outcomes(values) >= cfg["modes"]["min_outcome_share"] * values.size


def bimodality(values: np.ndarray, cfg: dict) -> dict:
    """Hartigan's dip: is there a subset of runs where the strategy simply stopped working?

    Args:
        values: One value per simulation.
        cfg: What inputs.config.load() returned.

    Returns:
        The dip statistic, its p-value and the verdict at alpha. This is the only test in
        the battery that finds this shape: a ladder of percentiles is perfectly smooth over
        a distribution with two separate peaks, so no quantile can reveal it. A low p turns
        "robust to the data on average" into "robust except in an identifiable regime",
        which are different conclusions with the same mean.
        Its p-value is one of the two that earn a place in the multiplicity pool; measured
        on this battery it rejects in 20 of 40 runs and ranges the whole interval, unlike
        Jarque-Bera which rejected 40 of 40 and therefore said nothing.
    """
    statistic, p_value = diptest.diptest(np.asarray(values, dtype=np.float64))
    return {"dip": float(statistic), "p": float(p_value),
            "bimodal": bool(p_value < cfg["modes"]["dip_alpha"]),
            "n": int(values.size)}


def shape(values: np.ndarray) -> dict:
    """How far from normal the outcome distribution sits.

    Args:
        values: One value per simulation.

    Returns:
        Skew and raw kurtosis, 3 for a normal. Descriptive on purpose and carrying no
        p-value: Jarque-Bera at a thousand simulations rejects normality for any real P&L
        distribution -- 40 of 40 here, the largest p being 0.014 -- so its answer is known
        before it runs, and in a multiplicity pool it would spend the budget on certain
        rejections and widen everyone else's q. These two numbers are still worth having:
        they are the inputs to the Sharpe variance factor and they are what the dip result
        has to be read beside.
    """
    return {"skew": float(stats.skew(values)),
            "kurtosis": float(stats.kurtosis(values, fisher=False))}


def regime_collapse(trades: np.ndarray, original: float, cfg: dict) -> dict:
    """Whether the strategy was still the same strategy, or stopped trading.

    Args:
        trades: NumberOfTrades of every simulation.
        original: Trade count of the unperturbed backtest.
        cfg: What inputs.config.load() returned.

    Returns:
        The median and worst trade count as shares of the original, and whether the median
        fell through the floor. A simulation that fired six times is not a degraded version
        of the strategy, it is a different one, and its net profit is meaningless in every
        percentile it contributes to -- so the trade count is a response to be gated on,
        not a diagnostic to glance at.
    """
    share = np.asarray(trades, dtype=np.float64) / original
    return {"median_share": float(np.median(share)), "worst_share": float(share.min()),
            "collapsed": bool(np.median(share) < cfg["gates"]["collapse_frac"]),
            "min_trades": int(trades.min())}


def describe(metrics: dict, original_trades: float, cfg: dict) -> dict:
    """Everything question 2 asks of one strategy under one task.

    Args:
        metrics: The reconstructed metrics of that task, one array per name.
        original_trades: Trade count of the unperturbed backtest.
        cfg: What inputs.config.load() returned.

    Returns:
        The shape of the outcome and whether the strategy survived as itself, or a bare
        `discriminated: False` when the task moved nothing and there is nothing to describe.
    """
    net = metrics["NetProfit"]
    if not discriminated(net, cfg):
        return {"discriminated": False, "outcomes": outcomes(net),
                "trades": regime_collapse(metrics["NumberOfTrades"], original_trades, cfg)}
    return {"discriminated": True, "outcomes": outcomes(net),
            "bimodality": bimodality(net, cfg),
            "shape": shape(net),
            "trades": regime_collapse(metrics["NumberOfTrades"], original_trades, cfg)}
