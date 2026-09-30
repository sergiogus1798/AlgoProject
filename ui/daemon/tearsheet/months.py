"""Calendar arithmetic on one sample's daily cumulative P&L: months and years."""

import pandas as pd


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
