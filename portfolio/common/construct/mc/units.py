"""A member's trades as whole units: each one's floating path per block since entry, at unit risk."""

from typing import TypedDict

import numba
import numpy as np
import pandas as pd

from ..equity import clock

NS_PER_MINUTE = 60_000_000_000


class Slots(TypedDict):
    """`slots()` output: per-bar day and block position, plus the calendar's shape."""

    day: np.ndarray
    slot: np.ndarray
    abs: np.ndarray
    per_day: int
    n_days: int


class Unit(TypedDict):
    """One member's trades as bootstrap units, as `units()` returns them."""

    low: np.ndarray
    high: np.ndarray
    level: np.ndarray
    off: np.ndarray
    pnl: np.ndarray
    open_day: np.ndarray
    open_slot: np.ndarray
    gaps: np.ndarray
    n_overlap: int
    per_day: int
    n_days: int


def slots(
    bar_times: np.ndarray, feed_zone: str, day_zone: str, days: np.ndarray, minutes: int
) -> Slots:
    """Where each M1 bar sits on the server-day calendar: its day, its block of the day.

    Args:
        bar_times: Naive bar-open minutes in the feed's clock (int64 ns or datetime64).
        feed_zone: The clock the bars are stamped in.
        day_zone: The server clock whose midnight cuts a day.
        days: Sorted int64 ns labels of the server days a path may use (one segment).
        minutes: Block length.

    Returns:
        `day` (int32, index into `days`, -1 outside them or in an hour a change of time
        repeats), `slot` (int32, block of that server day, counted from its midnight in real
        elapsed time, so a 25-hour day has 300 five-minute blocks) and `abs` (int64, blocks
        since the first day's midnight, -1 where `day` is); `per_day` (blocks in a 24-hour
        day) and `n_days`, which every unit built on it carries.
    """
    utc, _ = clock.to_utc(pd.DatetimeIndex(bar_times), feed_zone)
    ok = ~utc.isna()
    label = clock.day_of(pd.DatetimeIndex(utc[ok]), day_zone).as_unit("ns").asi8
    pos = np.minimum(np.searchsorted(days, label), len(days) - 1)
    inside = days[pos] == label
    index = pd.DatetimeIndex(days)
    starts = clock.to_utc(index, day_zone)[0].as_unit("ns").asi8
    length = (clock.day_end(index, day_zone).as_unit("ns").asi8 - starts) // (
        minutes * NS_PER_MINUTE
    )
    before = np.concatenate([[0], np.cumsum(length)[:-1]])
    slot = (pd.DatetimeIndex(utc[ok]).as_unit("ns").asi8 - starts[pos]) // (
        minutes * NS_PER_MINUTE
    )
    day = np.full(len(bar_times), -1, dtype=np.int32)
    slot_all = np.zeros(len(bar_times), dtype=np.int32)
    abs_all = np.full(len(bar_times), -1, dtype=np.int64)
    where = np.flatnonzero(ok)[inside]
    day[where] = pos[inside]
    slot_all[where] = slot[inside]
    abs_all[where] = before[pos[inside]] + slot[inside]
    return {
        "day": day,
        "slot": slot_all,
        "abs": abs_all,
        "per_day": 1440 // minutes,
        "n_days": len(days),
    }


def units(
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    where: Slots,
    point_value: float,
    factor: float,
) -> Unit:
    """One member's trades as bootstrap units (the `members` item of `mc.paths`).

    The wicks and the window are `equity.paths`' own: a long's worst price in a minute is
    its Low, the exit minute is not floating and books the realised P&L.

    Args:
        trades: The member's trades (schema T of EXECUTION.md).
        bars: The feed's M1 bars (High, Low, Close), the same frame `where` was built on.
        where: `slots()` output for `bars.index`.
        point_value: Account currency per 1.0 of price per lot.
        factor: The member's sizing factor (`inputs.risk.sizing`); 1.0 leaves SQX's money.

    Returns:
        Only the trades that open and close inside the days of `where`, in open-time order:
        `low`, `high`, `level` (float32 [Q], each trade's worst, best and last floating per
        block since its entry block, one after another; its last block holds the realised
        P&L), `off` (int64 [T + 1], where each trade's blocks start), `pnl` (float64 [T]),
        `open_day`, `open_slot` (int32 [T]), `gaps` (int64 [T - 1], blocks from a trade's
        close to the next one's open, 0 when they overlap), `n_overlap` (how many did),
        `per_day` and `n_days` (the calendar of `where`).
    """
    order = np.argsort(trades["Open time"].to_numpy(), kind="stable")
    bar_times = bars.index.to_numpy()
    open_idx = (
        np.searchsorted(bar_times, trades["Open time"].to_numpy(), side="right") - 1
    )[order]
    close_idx = (
        np.searchsorted(bar_times, trades["Close time"].to_numpy(), side="right") - 1
    )[order]
    # A trade outside the bars given would land on their first or last bar: out by its own times.
    inside = (
        (trades["Open time"].to_numpy() >= bar_times[0])
        & (trades["Close time"].to_numpy() < bar_times[-1] + np.timedelta64(1, "m"))
    )[order]
    keep = inside & (where["abs"][open_idx] >= 0) & (where["abs"][close_idx] >= 0)
    open_idx, close_idx = open_idx[keep], close_idx[keep]
    side = np.where(
        trades["Type"].astype(object).to_numpy()[order][keep] == "Buy", 1.0, -1.0
    )
    k = side * trades["Size"].to_numpy(np.float64)[order][keep] * point_value * factor
    open_price = trades["Open price"].to_numpy(np.float64)[order][keep]
    pnl = trades["Profit/Loss"].to_numpy(np.float64)[order][keep] * factor

    first, last = where["abs"][open_idx], where["abs"][close_idx]
    off = np.concatenate([[0], np.cumsum(last - first + 1)]).astype(np.int64)
    low, high, level = (np.full(off[-1], np.nan, dtype=np.float32) for _ in range(3))
    _fill(
        open_idx,
        close_idx,
        k,
        open_price,
        pnl,
        bars["Low"].to_numpy(np.float64),
        bars["High"].to_numpy(np.float64),
        bars["Close"].to_numpy(np.float64),
        where["abs"],
        off,
        low,
        high,
        level,
    )
    raw = first[1:] - last[:-1]
    return {
        "low": low,
        "high": high,
        "level": level,
        "off": off,
        "pnl": pnl,
        "open_day": where["day"][open_idx],
        "open_slot": where["slot"][open_idx],
        "gaps": np.maximum(raw, 0),
        "n_overlap": int((raw < 0).sum()),
        "per_day": where["per_day"],
        "n_days": where["n_days"],
    }


@numba.njit(cache=True)
def _fill(
    open_idx: np.ndarray,
    close_idx: np.ndarray,
    k: np.ndarray,
    open_price: np.ndarray,
    pnl: np.ndarray,
    bar_low: np.ndarray,
    bar_high: np.ndarray,
    bar_close: np.ndarray,
    bar_abs: np.ndarray,
    off: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    level: np.ndarray,
) -> None:
    """Each trade's floating per block: wicks while open, the realised P&L in its exit block."""
    for i in range(open_idx.shape[0]):
        base, first = off[i], bar_abs[open_idx[i]]
        for m in range(open_idx[i], close_idx[i]):
            if bar_abs[m] < 0:
                continue
            q = base + bar_abs[m] - first
            a = k[i] * (bar_low[m] - open_price[i])
            b = k[i] * (bar_high[m] - open_price[i])
            worst, best = min(a, b), max(a, b)
            if np.isnan(low[q]) or worst < low[q]:
                low[q] = worst
            if np.isnan(high[q]) or best > high[q]:
                high[q] = best
            level[q] = k[i] * (bar_close[m] - open_price[i])
        q = off[i + 1] - 1
        if np.isnan(low[q]) or pnl[i] < low[q]:
            low[q] = pnl[i]
        if np.isnan(high[q]) or pnl[i] > high[q]:
            high[q] = pnl[i]
        level[q] = pnl[i]
        carry = np.float32(0.0)
        for q in range(base, off[i + 1]):
            if np.isnan(low[q]):
                low[q] = high[q] = level[q] = carry
            else:
                carry = level[q]
