"""The one repricer: a market-order trade's money P/L from raw bar opens and the task's declared costs, as SQX charges them."""

from typing import TypedDict

import numpy as np
import pandas as pd

from core.assetdata import load, schema, sqx_settings, symbol_for

# `spread` and `slippage` in PRICE units (card points x tick_size). `swap_long` / `swap_short`
# as the card signs them: percent per year, negative = the holder pays. `triple` is the weekday
# (Monday 0) whose night counts three, `rollover` the hour the night is charged at.
Costs = TypedDict("Costs", {"point_value": float, "tick_size": float, "spread": float,
                            "slippage": float, "commission_method": str, "commission": float,
                            "swap_long": float, "swap_short": float, "triple": int,
                            "rollover": int})

WEEKDAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
DAY, EPOCH_WEEKDAY = 86400, 3      # seconds; 1970-01-01 was a Thursday


def costs(feed: str, segment: str) -> Costs:
    """What a task on this feed and segment charges, read from the asset card.

    Args:
        feed: SQX feed name, e.g. "NIKKEI225_M1".
        segment: "build", "oos1" or "oos2"; picks the spread, the slippage and the commission.

    Returns:
        The card's costs for that segment. Refuses a card whose swap is not `percent`: a
        `points` swap (every forex card) is in tickStep, which the card does not carry.
    """
    data = load(symbol_for(feed))
    assert schema(data)["swap"]["sqx_type"] == "percent", f"{feed}: swap is not percent per year"
    s, tick = sqx_settings(data, segment), data["instrument"]["tick_size"]
    return {"point_value": data["instrument"]["point_value"], "tick_size": tick,
            "spread": s["defaultSpread"] * tick, "slippage": s["defaultSlippage"] * tick,
            "commission_method": s["commission"]["method"], "commission": s["commission"]["value"],
            "swap_long": s["swap"]["long"], "swap_short": s["swap"]["short"],
            "triple": WEEKDAYS.index(s["swap"]["triple_swap_on"]),
            "rollover": int(str(s["swap"]["rollout_hour"]).split(":")[0])}


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
    zero commission (knowhow/research/monkey-reprice-audit.md). UNVERIFIED, written from SQX's
    documented convention and never reconciled trade by trade: shorts (sell at the bar open
    minus slippage, buy back at open + spread + slippage, `swap_short` on the entry fill) and
    a non-zero commission (charged once, at the open: `PercentageBased` on the entry notional,
    `SizeBased` per lot).

    Args:
        open_px, close_px: Raw bar opens, in price.
        open_time, close_time: Naive datetimes of those bars, on the feed's clock.
        side: +1 long, -1 short.
        size: Lots.
        costs: As costs() returns it. Every array broadcasts against the others.

    Returns:
        (pnl, cost) in account currency, the inputs' shape. `pnl` is rounded to the cent as SQX
        reports it; `cost` is the raw bar-to-bar move minus `pnl`, so `pnl + cost` is exactly
        the gross: `point_value * size * (spread + 2 * slippage)` + swap + commission, plus the
        tick and cent rounding of that trade.
    """
    tick, value = costs["tick_size"], costs["point_value"] * np.asarray(size, float)
    side = np.asarray(side, float)
    long = side > 0
    buy = lambda px: np.round((px + costs["spread"] + costs["slippage"]) / tick) * tick
    sell = lambda px: np.round((px - costs["slippage"]) / tick) * tick
    entry = np.where(long, buy(open_px), sell(open_px))
    leave = np.where(long, sell(close_px), buy(close_px))
    rate = np.where(long, costs["swap_long"], costs["swap_short"]) / 100 / 360
    swap = -value * entry * rate * nights(open_time, close_time, costs)
    commission = {"PercentageBased": value * entry / 100, "SizeBased": np.asarray(size, float)
                  }[costs["commission_method"]] * costs["commission"]
    net = np.round(value * side * (leave - entry) - swap - commission, 2)
    return net, value * side * (np.asarray(close_px) - np.asarray(open_px)) - net


def fills(bars: pd.DataFrame, positions: np.ndarray) -> np.ndarray:
    """The raw price a moved or drawn trade fills from: the open of each bar.

    Args:
        bars: One row per bar with `Open`, as engines.nulls.inputs.bars() returns them.
        positions: Bar positions (row numbers), any shape.

    Returns:
        `Open` at those positions, to pass to pnl() as `open_px` or `close_px`.
    """
    return bars["Open"].to_numpy()[positions]
