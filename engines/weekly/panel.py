"""Trades into weeks x units of excess, gross and net: each trade whole in the week it closes in."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from engines.market import reprice
from engines.variants import excess

DAY = np.timedelta64(1, "D")


def monday(time: np.ndarray | pd.Series | np.datetime64) -> np.ndarray:
    """The Monday of the calendar week each stamp falls in, on the stamps' own clock.

    Args:
        time: Naive datetimes.

    Returns:
        datetime64[D]; a Saturday or Sunday stamp belongs to the week that just traded.
    """
    day = np.asarray(time, "datetime64[D]")
    return day - (day.astype(np.int64) + 3) % 7 * DAY          # 1970-01-01 was a Thursday


def years(window: tuple[str, str]) -> float:
    """Length of a window in years of 365.25 days, as `engines.variants.excess.per_year` counts.

    Args:
        window: (first day, last day) as full dates, both inside it.
    """
    first, last = (pd.Timestamp(day) for day in window)
    return ((last - first).days + 1) / 365.25


def per_trade(trades: pd.DataFrame, bars: pd.DataFrame, costs: reprice.Costs,
              span: tuple[str, str], drift: dict, feed: str | None = None,
              drift_span: tuple[str, str] | None = None) -> pd.DataFrame:
    """One leg's trades on one market with their net and gross excess and their stamps.

    Args:
        As `engines.variants.excess.per_trade`, which this calls: `drift` is the gate's block,
        {"window": ..., "variant": ...} of `tradelevel.drift_term`, and decides the drift term.

    Returns:
        `excess.per_trade`'s frame plus `net` (= `excess`: the repriced P/L minus the drift),
        `gross` (= `net` + `cost`, the commission, swap, spread and slippage `reprice.real`
        charged that trade) and `open`, `close` (the trade's stamps). Frames of several legs
        and markets concatenate into what weekly() takes.
    """
    per = excess.per_trade(trades, bars, costs, span, drift, feed, drift_span)
    return per.assign(net=per["excess"], gross=per["excess"] + per["cost"],
                      open=trades["Open time"], close=trades["Close time"])


def weekly(per: pd.DataFrame, window: tuple[str, str], unit: str = "variant_id",
           units: Sequence | None = None) -> dict[str, pd.DataFrame]:
    """Weeks x units of excess over one window, every trade whole in the week it closes in.

    Args:
        per: per_trade()'s rows, any legs and markets together; reads `close`, `net`, `gross`
            and the `unit` column. Every trade closes inside `window`.
        window: (first day, last day) as full dates, both inside it.
        unit: The column naming what a column of the panel is: a variant, a cell, a market.
        units: The panel's columns, in this order; one without a trade is a column of zeros.
            None for those present, in order of first appearance.

    Returns:
        {"net", "gross"}: each indexed by the Monday of every calendar week touching `window`
        (one common index whatever the trades), columns `units`, account currency, zero where
        nothing closed. `signs @ frame.to_numpy()` is every draw of the flip null at once.
    """
    first, last = (monday(np.datetime64(day, "D")) for day in window)
    index = np.arange(first, last + DAY, 7 * DAY)
    close = np.asarray(per["close"], "datetime64[D]")
    assert len(close) == 0 or (close.min() >= np.datetime64(window[0], "D")
                               and close.max() <= np.datetime64(window[1], "D")), (
        f"a trade closes outside {window}")
    columns = pd.Index(per[unit].unique() if units is None else units, name=unit)
    col, week = columns.get_indexer(per[unit]), (monday(close) - first) // (7 * DAY)
    assert (col >= 0).all(), f"trades of a {unit} that is not among the panel's units"
    shape = (len(index), len(columns))
    return {name: pd.DataFrame(
        np.bincount(week * shape[1] + col, per[name].to_numpy(), shape[0] * shape[1]).reshape(shape),
        index=pd.DatetimeIndex(index.astype("datetime64[ns]"), name="week"), columns=columns)
        for name in ("net", "gross")}


def per_year(panel: pd.DataFrame, window: tuple[str, str]) -> pd.Series:
    """Each unit's excess over the window, per year of the window.

    Args:
        panel: One of weekly()'s frames, or `signs @` one of them with the same columns.
        window: The window weekly() was given.

    Returns:
        Indexed by unit, account currency per year of 365.25 days.
    """
    return panel.sum() / years(window)


def sqx_gap(per: pd.DataFrame, net_profit: pd.Series, unit: str = "variant_id",
            tolerance: float = 0.0, relative: float = 0.0) -> tuple[float, pd.Series]:
    """Whether the repriced trades add up to the NetProfit SQX reported, unit by unit.

    Args:
        per: per_trade()'s rows, exactly the trades SQX's figure covers; reads `profit`.
        net_profit: SQX's `NetProfit` per unit, indexed by the unit; these are the units
            judged, one without a trade summing to zero.
        tolerance: Account currency a unit may be off by: the floor.
        relative: This share of |NetProfit|; the allowance is the larger of the two (owner,
            2026-10-12), not their sum.

    Returns:
        (the share of units off by more than tolerance + relative x |NetProfit|, the gap sum -
        NetProfit of those units).
    """
    gap = per.groupby(unit, observed=True)["profit"].sum().reindex(net_profit.index, fill_value=0.0) \
        - net_profit
    off = gap[gap.abs() > np.maximum(tolerance, relative * net_profit.abs())]
    return len(off) / len(net_profit), off


def straddle(open_time: np.ndarray | pd.Series, close_time: np.ndarray | pd.Series) -> float:
    """Share of trades closed on a Monday or Tuesday after being held over the weekend.

    Args:
        open_time, close_time: Naive datetimes, one per trade.

    Returns:
        The share whose close is a Monday or a Tuesday of a later week than their open: trades
        the weekly flip puts in another week than a near twin closed on the Friday.
    """
    close = np.asarray(close_time, "datetime64[D]")
    early = (close - monday(close)) // DAY <= 1
    return float((early & (monday(open_time) < monday(close))).mean())
