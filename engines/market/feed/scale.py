"""The size of an ordinary one-minute move at each hour of the week, trailing, with a floor."""

import numpy as np
import pandas as pd

MAD_TO_SIGMA = 1.4826
MINUTE_NS = 60_000_000_000
# Monday 2003-01-06 00:00: every feed starts after it, and minute 0 of each week is a Monday.
ORIGIN = pd.Timestamp("2003-01-06").value // MINUTE_NS
WEEK = 7 * 1440


def minutes(index: pd.DatetimeIndex) -> np.ndarray:
    """Bar open times as whole minutes since ORIGIN, the axis every detector here counts on.

    Args:
        index: Bar open times.

    Returns:
        int64 minutes.
    """
    return index.asi8 // MINUTE_NS - ORIGIN


def returns(close: np.ndarray, at: np.ndarray) -> np.ndarray:
    """Close-to-close log return of each bar, NaN where the previous minute has no bar.

    Args:
        close: Close per bar.
        at: minutes() of the same bars.

    Returns:
        Same length; a return across a hole would measure the hole, not the minute.
    """
    r = np.full(len(close), np.nan)
    r[1:] = np.log(close[1:] / close[:-1])
    r[1:][np.diff(at) != 1] = np.nan
    return r


def _mad(values: np.ndarray) -> float:
    """MAD × 1.4826 of the finite values, NaN when there are none."""
    values = values[np.isfinite(values)]
    if not len(values):
        return np.nan
    return MAD_TO_SIGMA * np.median(np.abs(values - np.median(values)))


def by_week(r: np.ndarray, at: np.ndarray, weeks: int, min_weeks: int) -> tuple[np.ndarray, int]:
    """MAD × 1.4826 of each hour of the week, over the whole weeks before each week.

    Args:
        r: returns() of the feed.
        at: minutes() of the same bars.
        weeks: Trailing window, in weeks.
        min_weeks: Weeks of history a scale needs; before that the cell is NaN ("sin escala").

    Returns:
        (a 168 × n_weeks array, the feed's first week number). Week w's scale reads weeks
        [w - weeks, w) only, never w itself: a bar's label depends on what came before it.
        The window grows from min_weeks to weeks over the start of the feed.
    """
    week = at // WEEK
    first = int(week[0])
    n = int(week[-1]) - first + 1
    hour = (at % WEEK) // 60
    out = np.full((168, n), np.nan)
    order = np.lexsort((at, hour))
    hour_s, week_s, r_s = hour[order], week[order] - first, r[order]
    edges = np.searchsorted(hour_s, np.arange(169))
    for h in range(168):
        wk, rr = week_s[edges[h]:edges[h + 1]], r_s[edges[h]:edges[h + 1]]
        if not len(wk):
            continue
        cut = np.searchsorted(wk, np.arange(n + 1))
        for w in range(min_weeks, n):
            out[h, w] = _mad(rr[cut[max(0, w - weeks)]:cut[w]])
    return out, first


def own(at: np.ndarray, cells: np.ndarray, first: int) -> np.ndarray:
    """Each bar's cell of by_week(), before any floor.

    Args:
        at: minutes() of the bars.
        cells: by_week()'s array.
        first: by_week()'s first week.

    Returns:
        Per bar; NaN before the scale has warmed up.
    """
    return cells[(at % WEEK) // 60, at // WEEK - first]


def sigma(close: np.ndarray, at: np.ndarray, cells: np.ndarray, first: int, tick: float,
          floor_ticks: float, floor_rel: float) -> np.ndarray:
    """Each bar's scale: its cell's MAD, never under the two floors.

    Args:
        close: Close per bar.
        at: minutes() of the same bars.
        cells: by_week()'s array.
        first: by_week()'s first week.
        tick: The feed's price increment.
        floor_ticks: A move of this many ticks is never "large", in any hour.
        floor_rel: Nor is one under this share of the median scale across the hours of
            that week — a dead hour must not flag what would be noise at 15:00.

    Returns:
        Per bar, in log-return units; NaN before the scale has warmed up.
    """
    across = pd.DataFrame(np.where(cells > 0, cells, np.nan)).median(axis=0).to_numpy()
    prev = np.r_[close[0], close[:-1]]
    cell = own(at, cells, first)
    floor = np.maximum(floor_rel * across[at // WEEK - first], floor_ticks * tick / prev)
    return np.where(np.isfinite(cell), np.maximum(cell, floor), np.nan)
