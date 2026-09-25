"""How much of the market's open time the strategy actually held a position, and how big."""

import numpy as np
import pandas as pd

WEEK = pd.Timedelta(days=7)


def held(trades: pd.DataFrame, index: pd.DatetimeIndex) -> dict:
    """Lots held at every bar of the window, gross and signed.

    Args:
        trades: One strategy's trades on one sample.
        index: Open times of the window's bars.

    Returns:
        Keys `gross` (lots held regardless of direction) and `signed` (long positive,
        short negative), one entry per bar. Overlapping trades add up rather than being
        counted once: two open positions are twice the exposure, not the same exposure.

        A trade that closes on the bar it opened still occupies that bar. Its exit is
        pushed one bar forward so the arithmetic never credits a position with zero
        market time, which would make a scalper look like it was never exposed.
    """
    entry = index.searchsorted(trades["Open time"].to_numpy())
    leave = index.searchsorted(trades["Close time"].to_numpy())
    leave = np.maximum(leave, entry + 1)
    size = trades["Size"].to_numpy(np.float64)
    direction = np.where(trades["Type"].to_numpy() == "Buy", 1.0, -1.0)
    out = {}
    for name, weight in (("gross", size), ("signed", size * direction)):
        edges = np.zeros(len(index) + 1)
        np.add.at(edges, entry, weight)
        np.add.at(edges, np.minimum(leave, len(index)), -weight)
        out[name] = np.cumsum(edges)[:len(index)]
    return out


def bar_minutes(index: pd.DatetimeIndex) -> float:
    """Length of one bar, in minutes, read from the grid itself.

    Args:
        index: Open times of the window's bars.

    Returns:
        The median gap between consecutive bars. The median and not the mean because a
        weekend is a gap of two days and would otherwise stretch every bar.
    """
    return float(np.median(np.diff(index.to_numpy())) / np.timedelta64(1, "m"))


def measure(trades: pd.DataFrame, bars: pd.DataFrame, point_value: float,
            equity: float) -> dict:
    """Everything about how much market the strategy was standing in.

    Args:
        trades: One strategy's trades on one sample.
        bars: The window's bars, indexed by open time, with a `Close` column.
        point_value: Account currency per 1.0 of price and 1.0 of lot.
        equity: Account balance at the start of the window.

    Returns:
        `share` of open bars with a position, `hours_per_week` in the market,
        `avg_notional_pct` of the account committed on average across the whole window,
        `notional_when_in_pct` the same while actually in a position, and `tilt`, the
        signed lots as a fraction of the gross — +1 always long, -1 always short, 0 a
        book that is as often one way as the other.
    """
    lots = held(trades, bars.index)
    inside = lots["gross"] > 0
    notional = lots["gross"] * bars["Close"].to_numpy() * point_value
    span = (bars.index[-1] - bars.index[0]) + pd.Timedelta(minutes=bar_minutes(bars.index))
    return {"share": float(inside.mean()),
            "hours_per_week": float(inside.sum() * bar_minutes(bars.index) / 60
                                    / (span / WEEK)),
            "avg_notional_pct": float(notional.mean() / equity * 100),
            "notional_when_in_pct": float(notional[inside].mean() / equity * 100),
            "tilt": float(lots["signed"].sum() / lots["gross"].sum())}


def presence(lots: np.ndarray, moves: np.ndarray) -> dict:
    """How much of the market's own movement happened while the strategy was in it.

    Args:
        lots: Signed lots held at each bar, as `held` returns them.
        moves: Price change from each bar to the next, same length.

    Returns:
        `captured`, the share of the market's total absolute movement that occurred on
        bars the strategy was holding, and `aligned`, the share of that movement it was
        pointed the right way for. Together they say whether an edge is market timing --
        being present for the good stretches -- or something the benchmark cannot explain.
    """
    total = np.abs(moves).sum()
    inside = lots != 0
    return {"captured": float(np.abs(moves[inside]).sum() / total),
            "aligned": float(np.sign(lots[inside]) @ moves[inside] / total)}
