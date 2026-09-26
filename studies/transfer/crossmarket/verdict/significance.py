"""Honest significance on the real trades: minimum track-record length, bootstrap CIs. No DSR:
see POSSIBLE_IMPROVEMENTS.md for why — it needs a trial count this study does not have."""

from collections.abc import Callable

import numpy as np

from core.significance import min_track_record, moments
from engines.nulls.placement import bootstrap

__all__ = ["moments", "min_track_record", "bootstrap_metric", "profit_factor",
           "expectancy"]


def bootstrap_metric(returns: np.ndarray, metric: Callable[[np.ndarray], float], cfg: dict,
                     rng: np.random.Generator) -> dict:
    """Confidence interval of a metric by block-bootstrap over the real trades.

    Args:
        returns: Per-trade returns.
        metric: A function of a returns array, e.g. profit factor or expectancy.
        cfg: What config.load() returned.
        rng: Seeded generator.

    Returns:
        What bootstrap.percentile_ci() returned, over `metric` applied to each draw.
    """
    b = cfg["bootstrap"]
    values = np.array([metric(returns[p])
                       for rows in bootstrap.block_rows(b["draws"], len(returns), rng, b["block"])
                       for p in rows])
    return bootstrap.percentile_ci(values, *b["ci"])


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
