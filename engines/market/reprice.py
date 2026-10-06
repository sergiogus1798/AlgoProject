"""The one repricer: a market-order trade's money P/L from raw bar opens and the task's declared costs, as SQX charges them."""

from typing import TypedDict

import numpy as np
import pandas as pd

from core.assetdata import load, schema, sqx_settings, symbol_for

# `spread` and `slippage` in PRICE units (card points x tick_size). `swap_long` / `swap_short`
# as the card and MetaTrader 5 sign them, both sides alike: negative = the holder pays, positive
# = the holder is paid. Percent per year, unless `tick_step` is set: then points per night, a
# point being one tick_step of price. `triple` is the weekday (Monday 0) whose night counts
# three, `rollover` the hour the night is charged at.
Costs = TypedDict("Costs", {"point_value": float, "tick_size": float, "spread": float,
                            "slippage": float, "commission_method": str, "commission": float,
                            "swap_long": float, "swap_short": float, "triple": int,
                            "rollover": int, "tick_step": float | None})      # may be absent: percent

WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
DAY, EPOCH_WEEKDAY = 86400, 3      # seconds; 1970-01-01 was a Thursday


def costs(feed: str, segment: str) -> Costs:
    """What a task on this feed and segment charges, read from the asset card.

    Args:
        feed: SQX feed name, e.g. "NIKKEI225_M1".
        segment: "build", "oos1" or "oos2"; picks the spread, the slippage and the commission.

    Returns:
        The card's costs for that segment. A `points` swap (every forex card) is in tickStep,
        which the card does not carry: taken as tick_size / 10 (owner, 2026-10-06).
    """
    data = load(symbol_for(feed))
    s, tick = sqx_settings(data, segment), data["instrument"]["tick_size"]
    points = schema(data)["swap"]["sqx_type"] == "points"
    return {"point_value": data["instrument"]["point_value"], "tick_size": tick,
            "spread": s["defaultSpread"] * tick, "slippage": s["defaultSlippage"] * tick,
            "commission_method": s["commission"]["method"], "commission": s["commission"]["value"],
            "swap_long": s["swap"]["long"], "swap_short": s["swap"]["short"],
            "triple": WEEKDAYS.index(s["swap"]["triple_swap_on"]),
            "rollover": int(str(s["swap"]["rollout_hour"]).split(":")[0]),
            "tick_step": tick / 10 if points else None}


def _rollovers_before(time: np.ndarray, costs: Costs) -> np.ndarray:
    """Charged nights with a rollover strictly before each stamp, counted from 1970."""
    weight = [(d < 5) + 2 * (d == costs["triple"]) for d in range(7)]
    week = np.cumsum([0] + [weight[(EPOCH_WEEKDAY + i) % 7] for i in range(7)])
    seconds = np.asarray(time, "datetime64[s]").astype(np.int64) - costs["rollover"] * 3600
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


def pnl(open_px: np.ndarray, close_px: np.ndarray, open_time: np.ndarray,
        close_time: np.ndarray, side: np.ndarray, size: np.ndarray,
        costs: Costs) -> tuple[np.ndarray, np.ndarray]:
    """Money P/L of market-order trades at the declared costs, and the cost each one was charged.

    `open_px` and `close_px` are RAW BAR prices — the open of the entry bar and of the exit
    bar, as fills() returns them — never SQX's fill prices: the spread and the slippage are
    applied here and only here, so a fill passed in would be charged them twice.

    Audited against SQX to `0.02 + 2 * tick_size * point_value * size` per trade on longs at
    zero commission with a percent swap (knowhow/research/monkey-reprice-audit.md). UNVERIFIED
    against SQX, never reconciled trade by trade: shorts (the literal mirror, owner 2026-10-06:
    sell at open - spread - slippage, buy back at open + slippage; `swap_short` applied with
    the long's sign rule), a non-zero commission (once, at the open: `PercentageBased` on the
    entry notional, `SizeBased` per lot) and a swap in points (forex).

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
    tick, value, slip = costs["tick_size"], costs["point_value"] * size, costs["slippage"]
    entry = np.round((open_px + side * (costs["spread"] + slip)) / tick) * tick
    leave = np.round((close_px - side * slip) / tick) * tick
    rate, step = np.where(side > 0, costs["swap_long"], costs["swap_short"]), costs.get("tick_step")
    night = value * (entry * rate / 100 / 360 if step is None else step * rate)
    charge = (-night * nights(open_time, close_time, costs)
              + {"PercentageBased": value * entry / 100, "SizeBased": size
                 }[costs["commission_method"]] * costs["commission"])
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
