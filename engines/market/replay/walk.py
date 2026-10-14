"""Each trade walked again on its own timeframe's bars, from a possibly shifted entry, until its stop or its scheduled exit."""

from typing import TypedDict

import numpy as np
import pandas as pd

from engines.market import atr

PERIOD = (
    20  # the chain's grafted stop is always ATR(20) (sqx/variants/build/stoploss.py)
)
SIGNAL = (
    "Exit Signal",
    "Deleted",
)  # exits a live signal decides: they move under full latency
CLOCK = (
    "End Of Friday (Time)",
    "EndTest",
)  # clock exits: the same bar whatever the delay
BARS = ("Exit After X Bars",)  # counted from the entry: it moves with it


class Walked(TypedDict):
    """One replay: per trade, where it entered and left, why, and at what raw price."""

    enter: np.ndarray  # bar position of the (shifted) entry
    leave: np.ndarray  # bar position of the exit; -1 for a dropped trade
    stopped: np.ndarray  # bool: the stop closed it
    stop_level: np.ndarray  # the stop's price level from the (shifted) fill
    exit_raw: (
        np.ndarray
    )  # raw exit price: the level (or a gapping open) on a stop, the bar open otherwise
    dropped: (
        np.ndarray
    )  # bool: the delayed entry falls on or after its signal exit — no trade
    unknown: (
        np.ndarray
    )  # bool: originally stopped, now not; its signal exit is unknown, capped


def stop_level(
    bars: pd.DataFrame,
    enter: np.ndarray,
    fill: np.ndarray,
    side: np.ndarray,
    coef: np.ndarray,
) -> np.ndarray:
    """SQX's ATR-based stop level for an entry at bar `enter` filled at `fill`.

    Uses the ATR of the bar closed BEFORE the entry bar (SQX's shift 1;
    `knowhow/export/sqx-atr-is-wilder.md`), so nothing from the entry bar itself leaks in.

    Args:
        bars: The strategy's timeframe, High/Low/Close, time order.
        enter: Entry bar positions (>= 1).
        fill: Entry fill price (spread included, as SQX filled it).
        side: +1 long, -1 short.
        coef: The stop's ATR multiple per trade.

    Returns:
        The level, in price.
    """
    if enter.size and enter.min() < 1:
        raise ValueError("stop_level: an entry on bar 0 has no closed bar before it")
    return fill - side * coef * atr.sqx(bars, PERIOD)[enter - 1]


def first_touch(
    bars: pd.DataFrame,
    start: np.ndarray,
    end: np.ndarray,
    level: np.ndarray,
    side: np.ndarray,
) -> np.ndarray:
    """The first bar in [start, end) whose range reaches each trade's stop; -1 when none does.

    A long is stopped in the bar whose Low is at or under its level, a short where the High is
    at or over it — SQX at testPrecision 1 (the selected timeframe), with no target in the way.
    A per-trade numpy slice: 3,000 trades of 200 bars take milliseconds, so no Numba (D-7).
    """
    low, high = bars["Low"].to_numpy(), bars["High"].to_numpy()
    out = np.full(start.size, -1)
    for i in range(start.size):
        span = (
            low[start[i] : end[i]] <= level[i]
            if side[i] > 0
            else high[start[i] : end[i]] >= level[i]
        )
        hit = np.flatnonzero(span)
        if hit.size:
            out[i] = start[i] + hit[0]
    return out


def replay(
    bars: pd.DataFrame,
    trades: pd.DataFrame,
    delay: int,
    latency: bool,
) -> Walked:
    """Every trade re-run from `delay` bars after its real entry.

    The entry logic is never re-run: the entries are SQX's. Only the stop is recomputed, from
    the ATR before the new entry bar and the new fill; signal, bar-count and clock exits are
    moved by the rules of `docs/encargos/56-lecturas-nuevas.md` §3.3:
    - Exit After X Bars moves with the entry (+delay); End Of Friday stays; a signal exit
      stays when only the entry is late and moves +delay under full `latency`.
    - A signal or clock exit at or before the delayed entry, or an entry past the last bar: the
      trade does not exist (`dropped`).
    - A trade SQX stopped has no known signal exit after the stop: if the new stop misses, it
      runs until `cap` bars after its entry and is marked `unknown`.

    Args:
        bars: The strategy's timeframe with Open/High/Low/Close, time order.
        trades: One row per trade (`inputs.ready`), with columns
            - enter, leave: SQX's entry and exit bar positions (reprice.located);
            - Close type: SQX's exit reason;
            - offset: fill minus that bar's open at the real entry, carried to the shifted bar
              (measured per trade, never assumed: `export/fill-and-pricing`);
            - side: +1 long, -1 short;
            - coef: ATR multiple of the trade's stop;
            - tick: the step the level is rounded to (tickStep on forex, tick_size otherwise);
            - cap: bars a trade with an unknown exit may run (the strategy's longest trade).
        delay: Bars late, >= 0.
        latency: True moves signal exits too (the live case); False delays the entry only.

    Returns:
        The walk; with delay 0 it should reproduce SQX's own list (`reconcile`).
    """
    enter, leave, offset, side, coef, tick, cap = (
        trades[k].to_numpy()
        for k in ("enter", "leave", "offset", "side", "coef", "tick", "cap")
    )
    kind = trades["Close type"].astype(str).to_numpy()
    opens = bars["Open"].to_numpy()
    last = len(opens) - 1
    unknown_kind = ~np.isin(kind, ("SL", *SIGNAL, *CLOCK, *BARS))
    if unknown_kind.any():
        raise ValueError(
            f"replay: Close type {sorted(set(kind[unknown_kind]))} has no delay rule"
        )
    past = enter + delay > last
    new_enter = np.minimum(enter + delay, last)
    fill = opens[new_enter] + offset
    level = np.round(stop_level(bars, new_enter, fill, side, coef) / tick) * tick
    sqx_stopped = kind == "SL"
    moves = np.isin(kind, BARS) | (latency & np.isin(kind, SIGNAL))
    scheduled = np.where(moves, leave + delay, leave)
    # cap + 1: the longest trade may itself have ended on a stop in its last bar
    scheduled = np.where(sqx_stopped, new_enter + cap + 1, scheduled)
    scheduled = np.minimum(scheduled, last)
    dropped = past | (
        (delay > 0) & ~sqx_stopped & ~np.isin(kind, BARS) & (scheduled <= new_enter)
    )
    # the stop is watched from the entry bar up to, not including, the bar whose open closes the
    # trade: that open comes before anything inside its bar
    touch = first_touch(bars, new_enter, np.maximum(scheduled, new_enter), level, side)
    stopped = (touch >= 0) & ~dropped
    out_bar = np.where(stopped, touch, np.where(dropped, -1, scheduled))
    at_open = opens[np.maximum(out_bar, 0)]
    # a bar that opens past the level fills the stop at that open (gap through)
    exit_raw = np.where(
        stopped,
        np.where(side > 0, np.minimum(level, at_open), np.maximum(level, at_open)),
        at_open,
    )
    return {
        "enter": new_enter,
        "leave": out_bar,
        "stopped": stopped,
        "stop_level": level,
        "exit_raw": exit_raw,
        "dropped": dropped,
        "unknown": sqx_stopped & ~stopped & ~dropped,
    }
