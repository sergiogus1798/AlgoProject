"""Family E: could this edge be zero, given how many trades there are and how they are shaped?"""

import numpy as np
import pandas as pd

from core.significance import moments, psr

__all__ = ["psr", "crosscheck", "footprint"]


def footprint(source: dict, day: pd.DataFrame, asset: dict) -> float:
    """The Sharpe a same-footprint random trader would have scored, for `psr()`'s benchmark.

    Args:
        source: What stream.build() or stream.portfolio() returned.
        day: Daily candles, from regime.daily(), spanning the trades' window.
        asset: What costs.load() returned.

    Returns:
        `moments()`'s sharpe of one value per trade: the market's own move over the whole
        window, weighted by the share of it that one trade's own hold occupied, times the
        account's point value and that trade's size, minus what SQX actually charged it
        (`source["cost"]`). Zero is not the null a trading strategy is measured against
        (OPEN.md #71): a random trader with this footprint rarely nets zero, because cost
        usually outweighs what a passive presence of this size would have captured of the
        drift — the reason `psr()`'s `benchmark` and its own `sharpe` are one ruler with two
        centrings (OPEN.md #72).
    """
    move = float(day["Close"].iloc[-1] - day["Close"].iloc[0])
    occupancy = (source["close"] - source["open"]) / np.timedelta64(1, "D") / len(day)
    captured = occupancy * move * asset["point_value"] * source["size"] - source["cost"]
    return moments(captured)[0]


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
