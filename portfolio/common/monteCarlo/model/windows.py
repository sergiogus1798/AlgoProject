"""Family D in time: the calendar slices of a trade stream, defined in months, never in trades."""

from typing import cast

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
    first = cast(pd.Timestamp, when.min()).to_period("M").to_timestamp()
    last = cast(pd.Timestamp, when.max())
    out = []
    start = first
    while start + pd.DateOffset(months=months) <= last:
        end = cast(pd.Timestamp, start + pd.DateOffset(months=months))
        inside = np.flatnonzero((when >= start) & (when < end))
        out.append(
            {
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
                "positions": inside,
            }
        )
        start = cast(pd.Timestamp, start + pd.DateOffset(months=step))
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
    month = when.month  # pyright: ignore[reportAttributeAccessIssue]  # stub lacks DatetimeIndex.month
    weekday = when.dayofweek  # pyright: ignore[reportAttributeAccessIssue]  # stub lacks DatetimeIndex.dayofweek
    return {
        "month": cast(pd.Series, series.groupby(month).sum()),
        "weekday": cast(pd.Series, series.groupby(weekday).sum()),
    }
