"""Calendar arithmetic on one sample's daily cumulative P&L: months, years, rolling windows."""

import pandas as pd

WINDOWS = (3, 6, 12, 24)       # Campbell's rolling lengths, in months


def monthly(equity: pd.Series) -> pd.Series:
    """P&L of each calendar month the sample covers, in money, exact to the cent.

    Args:
        equity: Cumulative P&L per day, starting at 0, indexed by day.

    Returns:
        Indexed by month-start Timestamp. Month-end levels are rounded to whole cents
        before differencing, so the months add up to the last level to the cent.
    """
    cents = (equity * 100).round().groupby(equity.index.to_period("M")).last()
    moves = cents.diff().fillna(cents.iloc[0])      # each sample starts from 0
    moves.index = moves.index.to_timestamp()
    return moves / 100


def yearly(months: pd.Series) -> pd.Series:
    """P&L per calendar year from the months, indexed by year."""
    return months.groupby(months.index.year).sum().round(2)


def rolling(months: pd.Series) -> pd.DataFrame:
    """Share of rolling windows of consecutive months with positive P&L, per length.

    Args:
        months: `monthly()`'s output, one row per calendar month, flat months included.

    Returns:
        One row per length in `WINDOWS`: months, windows, positive, share (%, None when the
        sample is shorter than the window).
    """
    rows = []
    for k in WINDOWS:
        sums = months.rolling(k).sum().dropna()
        rows.append({"months": k, "windows": len(sums), "positive": int((sums > 0).sum()),
                     "share": 100 * (sums > 0).mean() if len(sums) else None})
    return pd.DataFrame(rows)


def heat(months: pd.Series) -> tuple[list[str], list[list[float | None]]]:
    """The months laid out as year rows × twelve month columns, blank outside the sample.

    Args:
        months: `monthly()`'s output.

    Returns:
        (year labels, values[year][month]).
    """
    years = sorted(set(months.index.year))
    at = {(d.year, d.month): v for d, v in months.items()}
    return [str(y) for y in years], [[at.get((y, m)) for m in range(1, 13)] for y in years]
