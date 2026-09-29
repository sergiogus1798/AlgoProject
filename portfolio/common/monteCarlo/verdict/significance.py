"""Family E: could this edge be zero, given how many trades there are and how they are shaped?"""

import numpy as np
import pandas as pd

from core.significance import footprint as _footprint
from core.significance import psr

__all__ = ["psr", "crosscheck", "footprint"]


def footprint(source: dict, day: pd.DataFrame, asset: dict) -> float:
    """The Sharpe a same-footprint random trader would have scored, for `psr()`'s benchmark.

    Args:
        source: What stream.build() or stream.portfolio() returned.
        day: Daily candles, from regime.daily() -- `core.barstore`'s whole feed history;
            sliced here to the trades' own window, not read as already sliced.
        asset: What costs.load() returned.

    Returns:
        `core.significance.footprint()`'s SR_b: one hypothetical random trade per real trade,
        each holding the same number of days (`source["close"] - source["open"]`) in the same
        direction (`source["direction"]`) and size (`source["size"]`) as the real one, against
        the market's own daily mean move and its own day-to-day noise over the trades' window
        -- not the window's whole move with no noise around it, which is the bug of
        2026-09-29 (OPEN.md #71): that version scored the random trader a per-trade Sharpe of
        the market's own drift, dispersed only by how long each trade happened to hold, which
        is a market-sized Sharpe, not a random trader's. `source["cost"]` is what SQX actually
        charged. The arithmetic itself is the implementation this study, `crossmarket` and
        `mcRetest` all share (`core.significance.footprint`, 2026-09-29).
    """
    window = day.loc[pd.Timestamp(source["open"].min()):pd.Timestamp(source["close"].max())]
    diffs = window["Close"].diff().dropna().to_numpy()
    mu, sigma = float(diffs.mean()), float(diffs.std(ddof=1))
    hold = (source["close"] - source["open"]) / np.timedelta64(1, "D")
    return _footprint(hold, source["direction"], source["size"], source["cost"], mu, sigma,
                      asset["point_value"])


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
