"""Minute-by-minute floating and realised equity from trades and M1 bars (contract P)."""

import numpy as np
import pandas as pd


def _locate(times: np.ndarray, bar_times: np.ndarray) -> np.ndarray:
    """Index of the bar that contains each time: the last bar open at or before it."""
    return np.searchsorted(bar_times, times, side="right") - 1


def entry_commission(trades: pd.DataFrame, commission: dict, point_value: float) -> np.ndarray:
    """Each trade's round-turn commission in account currency, as the asset card states it.

    Args:
        trades: One strategy's trades of ONE segment (schema T).
        commission: That segment's `costs.commission.use` entry: `method` and `value`
            ($ per lot when `SizeBased`, % of the notional at the open when `PercentageBased`).
        point_value: Account currency per 1.0 of price per lot.

    Returns:
        One figure per trade, ≥ 0 — what `minute_path` takes off the floating equity from the
        entry. 🤔 The `PercentageBased` branch has only been reconciled at 0 %.
    """
    size = trades["Size"].to_numpy(np.float64)
    if commission["method"] == "SizeBased":
        return commission["value"] * size
    return commission["value"] / 100 * trades["Open price"].to_numpy(np.float64) * point_value * size


def minute_path(trades: pd.DataFrame, bars: pd.DataFrame, point_value: float,
                commission: np.ndarray | float = 0.0) -> dict[str, np.ndarray]:
    """Every bar's equity for one strategy, relative to its start (contract P).

    Args:
        trades: One strategy's trades (schema T): Type, Open/Close time, Open/Close price,
            Size, Profit/Loss.
        bars: M1 bars with High, Low, Close, indexed by naive bar-open minute.
        point_value: Account currency per 1.0 of price per lot.
        commission: Account currency per trade (`entry_commission`), charged on the floating
            equity from the entry minute: 🔬 SQX's curve carries the whole round turn while
            the position is open (`knowhow/sqx-format/equity-reconstruction-usdjpy-gap.md`).
            It is already inside `Profit/Loss`, so the days still sum to the trades.

    Returns:
        `t` (int64 ns, bar open, naive feed clock), `worst`/`best`/`close` (float64, equity
        since the path's first minute) and `open` (int16, positions open that minute) —
        the four fields of contract P. Two extra fields a lone `path` dict cannot do without:
        `realised` (float64, cumulative booked Profit/Loss) and `opens` (int16, trades that
        opened that exact minute, not cumulative) — `days.py` needs both to split a day's
        booked P&L from its floating end and to count trades opened per day.
    """
    bar_times = bars.index.to_numpy()
    open_idx = _locate(trades["Open time"].to_numpy(), bar_times)
    close_idx = _locate(trades["Close time"].to_numpy(), bar_times)
    start, end = int(open_idx.min()), int(close_idx.max())
    open_idx, close_idx = open_idx - start, close_idx - start
    n = end - start + 1

    side = np.where(trades["Type"].astype(object) == "Buy", 1.0, -1.0)
    size = trades["Size"].to_numpy(np.float64)
    k = side * size * point_value
    is_long = side > 0
    offset = k * trades["Open price"].to_numpy(np.float64) + commission
    pnl = trades["Profit/Loss"].to_numpy(np.float64)

    k_long, k_short, off, opens, realised = (np.zeros(n) for _ in range(5))
    np.add.at(k_long, open_idx[is_long], k[is_long])
    np.add.at(k_long, close_idx[is_long], -k[is_long])
    np.add.at(k_short, open_idx[~is_long], k[~is_long])
    np.add.at(k_short, close_idx[~is_long], -k[~is_long])
    np.add.at(off, open_idx, offset)
    np.add.at(off, close_idx, -offset)
    np.add.at(opens, open_idx, 1)
    np.add.at(realised, close_idx, pnl)

    held = opens.copy()
    np.add.at(held, close_idx, -1)   # the exit bar is not exposed, as k is not
    open_count = np.cumsum(held)
    k_long, k_short, off = np.cumsum(k_long), np.cumsum(k_short), np.cumsum(off)
    realised_cum = np.cumsum(realised)

    low = bars["Low"].to_numpy(np.float64)[start:end + 1]
    high = bars["High"].to_numpy(np.float64)[start:end + 1]
    close = bars["Close"].to_numpy(np.float64)[start:end + 1]

    worst = realised_cum + low * k_long + high * k_short - off
    best = realised_cum + high * k_long + low * k_short - off
    close_eq = realised_cum + close * (k_long + k_short) - off

    return {"t": bar_times[start:end + 1].astype("int64"), "worst": worst, "best": best,
            "close": close_eq, "open": open_count.astype(np.int16),
            "realised": realised_cum, "opens": opens.astype(np.int16)}
