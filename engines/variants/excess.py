"""A batch's trades net of the market's drift: per trade, per variant and year, and per day."""

from typing import cast

import numpy as np
import pandas as pd

from core import metrics
from engines.market import reprice, tradelevel

CHUNK = 200_000  # trades spread over their held bars at a time: bounds daily()'s memory


def per_trade(
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    costs: reprice.Costs,
    span: tuple[str, str],
    drift: dict,
    feed: str | None = None,
    drift_span: tuple[str, str] | None = None,
) -> pd.DataFrame:
    """Each trade's repriced profit, the drift the market paid it for being in, and the excess.

    Args:
        trades: One leg's trades on one market, every variant of the batch: `variant_id`,
            `Type`, `Open time`, `Close time`, `Size`, and from an export `Close type` and
            `Close price`.
        bars: The strategies' own timeframe, the whole file, indexed by open time.
        costs: `reprice.costs` of the feed and this window's segment.
        span: (first, last) of the window, as strings a DatetimeIndex slices by.
        drift: The gate's `drift` block: `window` and `variant`.
        feed: As `reprice.located` takes it; None for trades on the bar grid by construction.
        drift_span: The bars the drift is measured on; None for the window's own.

    Returns:
        Indexed as `trades`: `variant_id`, `profit` (`reprice.real`'s P/L), `drift`
        (`tradelevel.drift_term`), `excess` = profit - drift, and `reprice.real`'s own columns.
        Raises as `reprice.real` does, and on a trade whose drift has no bars to be measured
        on: under variants `b` and `d` a trade takes the drift of its own calendar window, so
        a `drift_span` that leaves that window out has none.
    """
    trades = trades.assign(
        identity=trades["variant_id"]
    )  # reprice.real names it on a bad fill
    priced = reprice.real(trades, bars, costs, feed)
    term, label = tradelevel.drift_term(
        trades,
        bars,
        drift_span or span,
        drift["window"],
        drift["variant"],
        costs["point_value"],
    )
    assert np.isfinite(term).all(), (
        f"no bars of {drift_span or span} to measure the drift of the trades opened in "
        f"{sorted(set(label[~np.isfinite(term)]))} (drift variant {drift['variant']})"
    )
    return priced.assign(
        variant_id=trades["variant_id"],
        profit=priced["pnl"],
        drift=term,
        excess=priced["pnl"] - term,
    )


def per_year(excess: pd.DataFrame, window: tuple[str, str]) -> pd.Series:
    """Each variant's excess summed over one window, per year of the window.

    Args:
        excess: What per_trade() returned for that window's trades.
        window: (first day, last day) of the window as full dates, both inside it.

    Returns:
        Indexed by `variant_id`, account currency per year (`core.metrics.years`). A variant without
        a trade in the window has no row.
    """
    first, last = (pd.Timestamp(day) for day in window)
    total = cast(pd.Series, excess.groupby("variant_id")["excess"].sum())
    return total / metrics.years(first, last)


def daily(
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    costs: reprice.Costs,
    span: tuple[str, str],
    drift: dict,
    feed: str | None = None,
    drift_span: tuple[str, str] | None = None,
) -> pd.DataFrame:
    """The excess of each variant day by day: the day's gain minus the drift collected that day.

    A trade is marked to the bar opens: each bar it holds books the move to the next open,
    less an equal share of the trade's drift (drift / bars held). The day of the bar the exit
    is stamped with books what is left — the move from that open to a stop's fill, and every
    cost. So each variant's row sums to the sum of per_trade()'s excess, whatever the variant.

    Args:
        As per_trade(); `span` also names the days, and every trade lies inside it.

    Returns:
        Variants x days, account currency: indexed by `variant_id` (those with a trade), one
        column per calendar day with a bar in `span`.
    """
    per = per_trade(trades, bars, costs, span, drift, feed, drift_span)
    stamps = cast(pd.DatetimeIndex, bars.index)
    days = stamps[stamps.slice_indexer(*span)].normalize().unique()  # pyright: ignore[reportAttributeAccessIssue]  # stub lacks DatetimeIndex.normalize
    day, opened = days.get_indexer(stamps.normalize()), bars["Open"].to_numpy()  # pyright: ignore[reportAttributeAccessIssue]  # same
    enter, leave, term = (per[k].to_numpy() for k in ("enter", "leave", "drift"))
    assert (day[enter] >= 0).all() and (day[leave] >= 0).all(), (
        f"a trade outside {span}"
    )
    code, ids = pd.factorize(per["variant_id"])
    held, cells = leave - enter, len(ids) * len(days)
    value = per["side"].to_numpy() * trades["Size"].to_numpy() * costs["point_value"]
    rate = term / np.maximum(held, 1)
    rest = (
        per["profit"].to_numpy()
        - value * (opened[leave] - opened[enter])
        - np.where(held == 0, term, 0.0)
    )
    out = np.bincount(code * len(days) + day[leave], rest, cells)
    for start in range(0, len(per), CHUNK):
        n = held[start : start + CHUNK]
        j = np.repeat(np.arange(start, start + len(n)), n)
        bar = enter[j] + np.arange(len(j)) - np.repeat(n.cumsum() - n, n)
        out += np.bincount(
            code[j] * len(days) + day[bar],
            value[j] * (opened[bar + 1] - opened[bar]) - rate[j],
            cells,
        )
    return pd.DataFrame(
        out.reshape(len(ids), len(days)),
        index=pd.Index(ids, name="variant_id"),
        columns=days,
    )
