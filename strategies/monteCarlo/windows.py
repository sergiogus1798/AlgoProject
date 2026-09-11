"""Family D in time: the calendar slices of a trade stream, defined in months, never in trades."""

import numpy as np
import pandas as pd


def rolling(opens: np.ndarray, months: int, step: int) -> list[dict]:
    """Windows of equal calendar length across the whole history.

    Args:
        opens: Open time of every trade, in stream order.
        months: Window length. Calendar months, because trade cadence varies far too much
            between strategies on the same asset for a trade-count window to compare them.
        step: Months between one window's start and the next. Equal to months gives the
            non-overlapping blocks; smaller gives the overlapping persistence curve.

    Returns:
        One dict per window with its start, its end and the positions of the trades inside
        it. Windows that would run past the last trade are dropped rather than shortened: a
        half-length window is not comparable to the others and would enter the vote as one.
    """
    when = pd.DatetimeIndex(opens)
    first = when.min().to_period("M").to_timestamp()
    last = when.max()
    out = []
    start = first
    while start + pd.DateOffset(months=months) <= last:
        end = start + pd.DateOffset(months=months)
        inside = np.flatnonzero((when >= start) & (when < end))
        out.append({"start": start.date().isoformat(), "end": end.date().isoformat(),
                    "positions": inside})
        start = start + pd.DateOffset(months=step)
    return out


def calendar(opens: np.ndarray, pnl: np.ndarray) -> dict[str, pd.Series]:
    """Where the profit sat in the year and in the week.

    Args:
        opens: Open time of every trade.
        pnl: Net USD per trade.

    Returns:
        Net profit by month of year and by weekday. Reporting only, and deliberately so:
        with twelve months and five weekdays, the best bucket of a random split looks
        remarkable, so no gate may read this.
    """
    when = pd.DatetimeIndex(opens)
    series = pd.Series(pnl)
    return {"month": series.groupby(when.month).sum(),
            "weekday": series.groupby(when.dayofweek).sum()}
