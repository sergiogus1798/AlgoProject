"""Honest significance on the real trades: minimum track-record length, bootstrap CIs. No DSR:
see POSSIBLE_IMPROVEMENTS.md for why — it needs a trial count this study does not have."""

from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import stats

from strategies.crossmarket import bootstrap, pricing


def trade_returns(fixed: dict, bars: pd.DataFrame) -> np.ndarray:
    """Net log return per real trade.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.

    Returns:
        One value per trade, in the same units pricing.realised() uses, cost already
        subtracted.
    """
    return pricing.realised(bars, fixed["held"], fixed["fill"]["convention"]) - fixed["cost"]


def moments(returns: np.ndarray) -> tuple[float, float, float]:
    """Sharpe, skew and excess kurtosis of a return series.

    Args:
        returns: Per-trade returns.

    Returns:
        (sharpe, skew, kurtosis). Sharpe is the plain per-trade mean over its own standard
        deviation, unannualised: min_track_record() needs it in this unit, not a yearly one.
    """
    sharpe = float(returns.mean() / returns.std(ddof=1))
    return sharpe, float(stats.skew(returns)), float(stats.kurtosis(returns, fisher=True))


def min_track_record(returns: np.ndarray, alpha: float = 0.05) -> dict:
    """Bailey / Lopez de Prado minimum track-record length.

    Args:
        returns: Per-trade returns.
        alpha: Significance level for the one-sided test that Sharpe > 0.

    Returns:
        Keys needed, have and enough. Replaces the flat MIN_TRADES floor as a diagnostic —
        inference.testable() is unchanged, per the owner's decision not to touch the verdict.
    """
    sharpe, skew, kurt = moments(returns)
    z = stats.norm.isf(alpha)
    needed = 1 + (1 - skew * sharpe + (kurt - 1) / 4 * sharpe ** 2) * (z / sharpe) ** 2
    return {"needed": float(needed), "have": len(returns), "enough": bool(len(returns) >= needed)}


def bootstrap_metric(returns: np.ndarray, metric: Callable[[np.ndarray], float], draws: int,
                     block: int, rng: np.random.Generator) -> dict:
    """Confidence interval of a metric by block-bootstrap over the real trades.

    Args:
        returns: Per-trade returns.
        metric: A function of a returns array, e.g. profit factor or expectancy.
        draws: Bootstrap draws.
        block: Trades per block.
        rng: Seeded generator.

    Returns:
        What bootstrap.percentile_ci() returned, over `metric` applied to each draw.
    """
    picks = bootstrap.block_bootstrap(draws, len(returns), rng, block)
    values = np.array([metric(returns[p]) for p in picks])
    return bootstrap.percentile_ci(values)


def profit_factor(returns: np.ndarray) -> float:
    """Gross gain over gross loss, on log returns.

    Args:
        returns: Per-trade returns.

    Returns:
        A ratio; inf when there are no losing trades in the sample.
    """
    gains, losses = returns[returns > 0].sum(), -returns[returns < 0].sum()
    return float(gains / losses) if losses else float("inf")


def expectancy(returns: np.ndarray) -> float:
    """Mean return per trade.

    Args:
        returns: Per-trade returns.

    Returns:
        The plain mean.
    """
    return float(returns.mean())
