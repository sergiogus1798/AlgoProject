"""Frozen runs of identical bars, and holes in the session, as event tables."""

import numpy as np
import pandas as pd

from engines.market.feed import session


def frozen(o: np.ndarray, h: np.ndarray, low: np.ndarray, c: np.ndarray, at: np.ndarray,
           eligible: np.ndarray, length: int) -> pd.DataFrame:
    """Runs of at least `length` consecutive minutes whose four prices never change.

    Args:
        o, h, low, c: Prices per bar.
        at: Bar times in whole minutes.
        eligible: Per bar, whether it may be part of a run (in session, outside the
            rollover hours); an ineligible bar ends a run.
        length: Minimum run, in bars, counting the first bar of the run.

    Returns:
        One row per run: `start` (index of its first bar), `bars`. The run is the anomaly,
        not each of its bars.
    """
    same = np.zeros(len(c), bool)
    same[1:] = ((np.diff(at) == 1) & (o[1:] == o[:-1]) & (h[1:] == h[:-1])
                & (low[1:] == low[:-1]) & (c[1:] == c[:-1]) & eligible[1:] & eligible[:-1])
    edges = np.flatnonzero(np.diff(np.r_[0, same.astype(np.int8), 0]))
    begin, end = edges[::2], edges[1::2]
    bars = end - begin + 1
    keep = bars >= length
    return pd.DataFrame({"start": begin[keep] - 1, "bars": bars[keep]})


def gaps(at: np.ndarray, week_mask: np.ndarray, least: int) -> pd.DataFrame:
    """Stretches of at least `least` in-session minutes with no bar.

    Args:
        at: Bar times in whole minutes.
        week_mask: The feed's session (engines.market.feed.session).
        least: Minimum hole, in in-session minutes.

    Returns:
        One row per hole: `after` (index of the last bar before it), `from_min` (the first
        missing minute), `to_min` (the bar that ends it), `minutes` (in-session minutes
        missing). Out-of-session time between two bars is never a hole.
    """
    p = session.prefix(week_mask, at)
    missing = p[1:] - session.prefix(week_mask, at[:-1] + 1)
    k = np.flatnonzero(missing >= least)
    return pd.DataFrame({"after": k, "from_min": at[k] + 1, "to_min": at[k + 1],
                         "minutes": missing[k]})
