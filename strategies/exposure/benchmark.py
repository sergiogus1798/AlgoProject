"""What "buy and hold" means here: three sizing conventions, and the P&L each one earns."""

import numpy as np
import pandas as pd

# The three answers to "how much of the thing would I have held?". They are not variants
# of one benchmark; each makes a different sentence true, and the study reports all three.
#
#   convention   holds                                     the comparison it licenses
#   one_lot      one lot, start to end                     an absolute yardstick, sizing-free
#   avg_size     the strategy's own average position       same capital committed per trade
#   equal_risk   whatever matches the strategy's daily     "more or less return for the same
#                standard deviation                         risk", the only fair rate question
#
# `equal_risk` is the headline because the other two are answers about position sizing
# wearing the clothes of an answer about edge.


def one_lot(trades: pd.DataFrame, moves: pd.Series, daily: pd.Series,
            point_value: float) -> float:
    """One lot held for the whole window.

    Args:
        trades: One strategy's trades on one sample.
        moves: Daily change in the close price.
        daily: The strategy's own daily profit and loss, in account currency.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        Lots held, which is 1.0 whatever the strategy did.
    """
    return 1.0


def avg_size(trades: pd.DataFrame, moves: pd.Series, daily: pd.Series,
             point_value: float) -> float:
    """The strategy's own mean position size, held for the whole window.

    Args:
        trades: One strategy's trades on one sample.
        moves: Daily change in the close price.
        daily: The strategy's own daily profit and loss, in account currency.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        The mean of the `Size` column. This is the convention that answers "the same money,
        left in the market instead of traded".
    """
    return float(trades["Size"].mean())


def equal_risk(trades: pd.DataFrame, moves: pd.Series, daily: pd.Series,
               point_value: float) -> float:
    """The size whose daily profit and loss is as volatile as the strategy's.

    Args:
        trades: One strategy's trades on one sample.
        moves: Daily change in the close price.
        daily: The strategy's own daily profit and loss, in account currency.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        Lots held. Both standard deviations are taken over the same daily calendar, flat
        days included, so a strategy that is out of the market most of the time is held to
        the risk it actually ran and not to the risk it ran only while trading.
    """
    return float(daily.std(ddof=1) / (moves.std(ddof=1) * point_value))


CONVENTIONS = {"one_lot": one_lot, "avg_size": avg_size, "equal_risk": equal_risk}


def moves(bars: pd.DataFrame) -> pd.Series:
    """Daily change in the close price over the window.

    Args:
        bars: The window's bars, indexed by open time, with a `Close` column.

    Returns:
        One entry per trading day, the first day dropped because it has no previous close.
    """
    closes = bars["Close"].resample("D").last().dropna()
    return closes.diff().dropna()


def daily(trades: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    """The strategy's profit and loss per calendar day, on the benchmark's own days.

    Args:
        trades: One strategy's trades on one sample.
        index: The days the benchmark is measured over.

    Returns:
        Account currency per day, zero on days it closed nothing.

        ⚠️ Profit is attributed to the day a trade **closed**, which is what SQX reports.
        A position held over three weeks therefore lands entirely on one day. That makes
        the daily series lumpier than a mark-to-market one and inflates its standard
        deviation, so every risk figure built on it -- `equal_risk` included -- is
        conservative towards the strategy rather than flattering.
    """
    closed = trades.groupby(trades["Close time"].dt.floor("D"))["Profit/Loss"].sum()
    return closed.reindex(index, fill_value=0.0)


def profit(lots: float, moves: pd.Series, point_value: float) -> pd.Series:
    """What holding that many lots earned per day.

    Args:
        lots: Position held for the whole window.
        moves: Daily change in the close price.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        Account currency per day. The one spread it costs to enter and the swap it pays to
        stay are ignored: over a window of years the entry is a rounding error, and the
        swap is a financing decision about the benchmark rather than a fact about it.
    """
    return moves * lots * point_value
