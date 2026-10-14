"""The one repricer: a market-order trade's money P/L from raw bar opens and the task's declared costs, as SQX charges them."""

from typing import TypedDict

import numpy as np
import pandas as pd

from core.assetdata import load, schema, sqx_settings, symbol_for
from core.barstore import source
from core.symbols import current

# `spread` and `slippage` in PRICE units (card points x tick_size). `swap_long` / `swap_short`
# as the card and MetaTrader 5 sign them, both sides alike: negative = the holder pays, positive
# = the holder is paid. Percent per year, unless `tick_step` is set: then points per night, a
# point being one tick_step of price. `triple` is the weekday (Monday 0) whose night counts
# three, `rollover` the hour the night is charged at.
Costs = TypedDict(
    "Costs",
    {
        "point_value": float,
        "tick_size": float,
        "spread": float,
        "slippage": float,
        "commission_method": str,
        "commission": float,
        "swap_long": float,
        "swap_short": float,
        "triple": int,
        "rollover": int,
        "tick_step": float | None,
    },
)  # may be absent: percent

WEEKDAYS = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)
DAY, EPOCH_WEEKDAY = 86400, 3  # seconds; 1970-01-01 was a Thursday
# SQX's `Close type`, by where the exit fills: at a price of its own inside the bar it is
# stamped with (SL measured; PT by the owner's rule, none verified; EndTest measured 2026-10-12: the
# trade still open when the window ends is closed at SQX's own price, 1,001 of 1,004 variants of
# a USA500 batch were 240 USD off when filled at the bar open), or at a bar open.
AT_PRICE = ("SL", "PT", "EndTest")
AT_OPEN = ("Exit After X Bars", "Exit Signal", "End Of Friday (Time)", "Deleted")


def costs(feed: str, segment: str) -> Costs:
    """What a task on this feed and segment charges, read from the asset card.

    Args:
        feed: SQX feed name, e.g. "NIKKEI225_M1".
        segment: "build", "oos1" or "oos2"; picks the spread, the slippage and the commission.

    Returns:
        The card's costs for that segment. A `points` swap (every forex card) is in tickStep,
        which the card does not carry: taken as tick_size / 10 (owner, 2026-10-06).
    """
    symbol = symbol_for(feed)
    assert symbol, f"no asset file declares the feed {feed}"
    data = load(symbol)
    s, tick = sqx_settings(data, segment), data["instrument"]["tick_size"]
    points = schema(data)["swap"]["sqx_type"] == "points"
    return {
        "point_value": data["instrument"]["point_value"],
        "tick_size": tick,
        "spread": s["defaultSpread"] * tick,
        "slippage": s["defaultSlippage"] * tick,
        "commission_method": s["commission"]["method"],
        "commission": s["commission"]["value"],
        "swap_long": s["swap"]["long"],
        "swap_short": s["swap"]["short"],
        "triple": WEEKDAYS.index(s["swap"]["triple_swap_on"]),
        "rollover": int(str(s["swap"]["rollout_hour"]).split(":")[0]),
        "tick_step": tick / 10 if points else None,
    }


def _rollovers_before(time: np.ndarray, costs: Costs) -> np.ndarray:
    """Charged nights with a rollover strictly before each stamp, counted from 1970."""
    weight = [(d < 5) + 2 * (d == costs["triple"]) for d in range(7)]
    week = np.cumsum([0] + [weight[(EPOCH_WEEKDAY + i) % 7] for i in range(7)])
    seconds = (
        np.asarray(time, "datetime64[s]").astype(np.int64) - costs["rollover"] * 3600
    )
    days = -(-seconds // DAY)
    return week[7] * (days // 7) + week[days % 7]


def nights(open_time: np.ndarray, close_time: np.ndarray, costs: Costs) -> np.ndarray:
    """Swap nights a trade is charged: rollovers T with open <= T < close, Monday to Friday.

    Args:
        open_time, close_time: Naive datetimes on the feed's clock, any equal shape.
        costs: As costs() returns it; reads `rollover` and `triple`.

    Returns:
        Nights per trade; the triple night counts 3, Saturday and Sunday 0.
    """
    return _rollovers_before(close_time, costs) - _rollovers_before(open_time, costs)


def pnl(
    open_px: np.ndarray,
    close_px: np.ndarray,
    open_time: np.ndarray,
    close_time: np.ndarray,
    side: np.ndarray,
    size: np.ndarray,
    costs: Costs,
) -> tuple[np.ndarray, np.ndarray]:
    """Money P/L of market-order trades at the declared costs, and the cost each one was charged.

    `open_px` and `close_px` are RAW BAR prices — the open of the entry bar and of the exit
    bar, as fills() returns them — never SQX's fill prices: the spread and the slippage are
    applied here and only here, so a fill passed in would be charged them twice.

    Audited against SQX (knowhow/research/monkey-reprice-audit.md): longs at zero commission with a
    percent swap to `0.02 + 2 * tick_size * point_value * size` per trade; 🔬 2026-10-12, over whole
    exports, a swap in points on longs AND shorts (47,610 USDJPY trades on the bar open, 99.994 %
    within 0.02 USD, short swap -10.4 points recovered to 0.001 per night, triple night included)
    and a SizeBased commission of 5 USD/lot (1.0 M longs to the cent). SQX puts the spread on the
    BUY fill (a long's entry, a short's exit) and sells at the bar open less slippage; this puts it
    on the entry of both sides: the same total, so the same P/L, and only a short stop would tell
    them apart. Still UNVERIFIED: a short stop or target, a PT exit, a PercentageBased commission.
    Args:
        open_px, close_px: Raw bar opens, in price.
        open_time, close_time: Naive datetimes of those bars, on the feed's clock.
        side: +1 long, -1 short.
        size: Lots.
        costs: As costs() returns it. Every array broadcasts against the others.

    Returns:
        (pnl, cost) in account currency, the inputs' shape. `pnl` is rounded to the cent as SQX
        reports it. `cost` is the declared charge, unrounded: `point_value * size * (spread +
        2 * slippage)` + swap + commission, negative swap being a credit; so `pnl + cost` is
        the bar-to-bar gross only up to the tick and cent rounding of that trade.
    """
    size, side = np.asarray(size, float), np.asarray(side, float)
    # Forex prices move in tickStep (a tenth of the pip the card calls tick_size): fills round
    # to it. 🔬 2026-10-07, USDJPY M30, 973 trades: max gap to SQX 77.73 USD -> 0.01.
    tick = costs.get("tick_step") or costs["tick_size"]
    value, slip = costs["point_value"] * size, costs["slippage"]
    entry = np.round((open_px + side * (costs["spread"] + slip)) / tick) * tick
    leave = np.round((close_px - side * slip) / tick) * tick
    rate, step = (
        np.where(side > 0, costs["swap_long"], costs["swap_short"]),
        costs.get("tick_step"),
    )
    night = value * (entry * rate / 100 / 360 if step is None else step * rate)
    charge = (
        -night * nights(open_time, close_time, costs)
        + {"PercentageBased": value * entry / 100, "SizeBased": size}[
            costs["commission_method"]
        ]
        * costs["commission"]
    )
    net = np.round(value * side * (leave - entry) - charge, 2)
    return net, value * (costs["spread"] + 2 * slip) + charge


def fills(bars: pd.DataFrame, positions: np.ndarray) -> np.ndarray:
    """The raw price a moved or drawn trade fills from: the open of each bar.

    Args:
        bars: One row per bar with `Open`, as engines.nulls.inputs.bars() returns them.
        positions: Bar positions (row numbers), any shape.

    Returns:
        `Open` at those positions, to pass to pnl() as `open_px` or `close_px`.
    """
    return bars["Open"].to_numpy()[positions]


def located(bars: pd.DataFrame, time: np.ndarray, feed: str | None) -> np.ndarray:
    """The bar each of SQX's stamps belongs to.

    Args:
        bars: The strategies' own timeframe, indexed by open time.
        time: Naive datetimes as SQX stamped them, 1-D.
        feed: SQX feed name, whose M1 bars `bars` were resampled from; None for trades
            that are on the bar grid by construction.

    Returns:
        Bar positions, -1 where the stamp is no bar's. SQX opens a bar at its first M1
        minute, so a bar whose first minutes are missing is stamped late (00:31 for the
        00:30 bar) and fills at that minute's open, which IS the resampled bar's `Open`: a
        stamp off the grid is its bar's only when no M1 minute precedes it inside the bar
        (knowhow/export/off-grid-stamps-and-stop-exits.md).
    """
    grid, time = bars.index, np.asarray(time, "datetime64[ns]")
    at = grid.searchsorted(time, side="right") - 1
    late = np.flatnonzero((at < 0) | (grid.to_numpy()[at] != time))
    if late.size:
        minutes = source(current(feed), ["Open"]).index if feed else grid[:0]
        first = minutes.searchsorted(grid.to_numpy()[at[late]])
        ok = (at[late] >= 0) & (first < len(minutes))
        ok[ok] = minutes.to_numpy()[first[ok]] == time[late[ok]]
        at[late[~ok]] = -1
    return at


def real(
    trades: pd.DataFrame, bars: pd.DataFrame, costs: Costs, feed: str | None = None
) -> pd.DataFrame:
    """SQX's own trades priced by pnl(): the one place a harvested trade becomes fills.

    Args:
        trades: `identity`, `Type`, `Open time`, `Close time`, `Size`, and from a harvest
            `Close type` and `Close price`. A frame without `Close type` is a drawn
            population (monkeys): every exit is a bar open.
        bars: The strategies' own timeframe, indexed by open time, with `Open`; `Low` and
            `High` too when an exit is one of AT_PRICE.
        costs: As costs() returns it, of the segment the trades ran in.
        feed: As located() takes it.

    Returns:
        Indexed as `trades`: `enter` and `leave` (bar positions, located()), `side`, `pnl`
        and `cost` (pnl(), on SQX's stamps), and `stop`, the raw exit price of an AT_PRICE
        exit and NaN on a bar exit. An AT_PRICE exit fills at SQX's `Close price` and not at
        the open of the bar it is stamped with, which the stop was hit AFTER (owner,
        2026-10-07): raw = `Close price` + side x slippage, so pnl() lands on SQX's fill.
        Reproduces SQX to 0.02 on 834 long SL exits and, as EndTest, to 2 ticks on the trade left
        open at the window's end; short SL and PT unverified. Raises on a
        stamp that is no bar's, a `Close type` in neither list and a price exit outside its
        bar's range by more than spread + slippage, naming the strategies: dropping them
        would drop the stopped trades and inflate every t.
    """
    opened, closed = (trades[k].to_numpy() for k in ("Open time", "Close time"))
    enter, leave = (located(bars, t, feed) for t in (opened, closed))
    side = np.where(trades["Type"].astype(str) == "Sell", -1.0, 1.0)
    stop, known = np.full(len(trades), np.nan), np.ones(len(trades), bool)
    if "Close type" in trades:
        kind, px = trades["Close type"].astype(str), trades["Close price"].to_numpy()
        priced, reach = (
            kind.isin(AT_PRICE).to_numpy(),
            costs["spread"] + costs["slippage"],
        )
        known = kind.isin(AT_OPEN).to_numpy()
        if priced.any():
            low, high = (bars[k].to_numpy()[leave] for k in ("Low", "High"))
            known |= priced & (px >= low - reach) & (px <= high + reach)
            stop[priced] = (px + side * costs["slippage"])[priced]
    bad = (enter < 0) | (leave < 0) | ~known
    if bad.any():
        raise ValueError(
            f"{bad.sum()} trades the common repricer cannot fill (a stamp that is no bar's, "
            f"an unknown Close type or a price exit outside its bar): strategies "
            f"{trades.loc[bad, 'identity'].unique()[:5].tolist()}, first at "
            f"{trades.loc[bad, 'Close time'].min()}; the bars end at {bars.index[-1]} "
            f"(behind the trades: python3 -m sqx.export.sync_bars)"
        )
    net, cost = pnl(
        fills(bars, enter),
        np.where(np.isnan(stop), fills(bars, leave), stop),
        opened,
        closed,
        side,
        trades["Size"].to_numpy(),
        costs,
    )
    return pd.DataFrame(
        {
            "enter": enter,
            "leave": leave,
            "side": side,
            "stop": stop,
            "pnl": net,
            "cost": cost,
        },
        index=trades.index,
    )
