"""Drawdown arithmetic on one sample's daily cumulative P&L: underwater, episodes, flat spells."""

import numpy as np
import pandas as pd


def underwater(equity: pd.Series, capital: float | None) -> tuple[pd.Series, pd.Series | None]:
    """Distance below the running peak, in money and in % of the running peak of the account.

    Args:
        equity: Cumulative P&L per day, starting at 0, indexed by day.
        capital: The account the backtest started with; the P&L alone peaks at 0 on day
            one, so a percentage needs the balance (capital + P&L) underneath it.

    Returns:
        (money ≤ 0, percent ≤ 0 or None when the capital is unknown).
    """
    peak = equity.cummax()
    money = equity - peak
    return money, (None if capital is None else 100 * money / (capital + peak))


def episodes(equity: pd.Series, most: int = 5) -> pd.DataFrame:
    """The deepest drawdown episodes, from the peak they fell from to the day it was regained.

    Args:
        equity: Cumulative P&L per day, indexed by day.
        most: How many to keep, deepest first.

    Returns:
        One row per episode: depth (money, ≤ 0), peak, trough, recovery (NaT when the
        sample ends below the peak), length in calendar days (peak → recovery or the
        sample's last day) and recovery time (trough → recovery, NaN when unrecovered).
    """
    peak = equity.cummax()
    under = (equity < peak).to_numpy()
    days = equity.index
    rows = []
    start = None
    for i, u in enumerate(np.append(under, False)):
        if u and start is None:
            start = i
        elif not u and start is not None:
            stretch = equity.iloc[start:i]
            trough = stretch.idxmin()
            recovered = i < len(equity)
            end = days[i] if recovered else days[-1]
            rows.append({"depth": stretch.min() - peak.iloc[start], "peak": days[start - 1],
                         "trough": trough, "recovery": days[i] if recovered else pd.NaT,
                         "length": (end - days[start - 1]).days,
                         "recovery_days": (days[i] - trough).days if recovered else np.nan})
            start = None
    out = pd.DataFrame(rows, columns=["depth", "peak", "trough", "recovery", "length",
                                      "recovery_days"])
    return out.sort_values("depth", kind="stable").head(most).reset_index(drop=True)


def longest_flat(equity: pd.Series) -> tuple[int, pd.Timestamp, pd.Timestamp]:
    """The longest stretch without a new high, the sample's start and end counted as edges.

    Args:
        equity: Cumulative P&L per day, starting at 0, indexed by day.

    Returns:
        (calendar days, from, to): from is the last high before the stretch, to the next
        new high or the sample's last day.
    """
    prior = equity.cummax().shift(1, fill_value=equity.iloc[0])
    highs = list(equity.index[equity > prior])
    edges = [equity.index[0]] + highs + ([equity.index[-1]] if highs[-1:] != [equity.index[-1]]
                                         else [])
    gaps = [(b - a).days for a, b in zip(edges, edges[1:])]
    k = int(np.argmax(gaps))
    return gaps[k], edges[k], edges[k + 1]


def annual_max(equity: pd.Series) -> pd.Series:
    """Each calendar year's deepest fall below its own running peak, money ≤ 0.

    Args:
        equity: Cumulative P&L per day, indexed by day.

    Returns:
        One value per year present, partial first and last years included.
    """
    return equity.groupby(equity.index.year).apply(lambda y: (y - y.cummax()).min())


def first_high(equity: pd.Series) -> tuple[int | None, pd.Timestamp | None]:
    """Calendar days from the sample's first day to its first close above the start (0).

    Args:
        equity: Cumulative P&L per day, starting at 0, indexed by day.

    Returns:
        (days, the day), or (None, None) when it never closes above where it started.
    """
    above = equity.index[equity > 0]
    if not len(above):
        return None, None
    return (above[0] - equity.index[0]).days, above[0]
