"""Per-strategy daily P&L series stacked into day and month matrices, and a calendar segment slice."""

import pandas as pd


def stack(series: dict[str, pd.Series], spans: dict[str, tuple[pd.Timestamp, pd.Timestamp]]) -> pd.DataFrame:
    """Daily P&L per identity: 0 inside its own history with no P&L, NaN outside it.

    Args:
        series: One daily P&L series per identity; a day missing from it, inside the span,
            reads 0 (no trade moved the curve that day), never NaN.
        spans: Each identity's own (first, last) day, both inclusive.

    Returns:
        `days × identities`, float64. The rows are the days some series carries — market
        days — never the whole calendar: a weekend of zeros would read as shared flat days
        and move every daily correlation.
    """
    days = pd.DatetimeIndex(sorted(set().union(*(s.index for s in series.values()))))
    cols = {}
    for identity, (lo, hi) in spans.items():
        inside = (days >= lo) & (days <= hi)
        cols[identity] = series[identity].reindex(days).fillna(0.0).where(inside)
    return pd.DataFrame(cols)


def monthly(daily: pd.DataFrame) -> pd.DataFrame:
    """Calendar-month sums; NaN only where the whole month is outside a column's history."""
    return daily.groupby(daily.index.to_period("M")).sum(min_count=1)


def segment(frame: pd.DataFrame, calendar: dict, name: str) -> pd.DataFrame:
    """One portfolio calendar segment's rows.

    Args:
        frame: Day-indexed (`stack()`'s output) or month-indexed (`monthly()`'s output).
        calendar: `inputs.calendar.portfolio()`'s result, naive Timestamps, both inclusive.
        name: Segment name, e.g. "build".

    Returns:
        The rows of `frame` that fall inside that segment.
    """
    lo, hi = calendar[name]
    if isinstance(frame.index, pd.PeriodIndex):
        return frame.loc[lo.to_period("M"):hi.to_period("M")]
    return frame.loc[lo:hi]
