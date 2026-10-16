"""A population's close-to-close daily P&L on its feed's own days, rebuilt from trades and M1."""

import numpy as np
import pandas as pd

from core import fanout

from . import days, paths, reconcile

# The feed's own midnight cuts the day, as SQX cuts its curve: naive times read as one fixed
# clock on both sides, so no minute falls in a change of time and none is dropped.
CLOCK = "UTC"
WORKERS = 16  # ~0.25 GB each: one strategy's minute frame over a five-year segment
_STATE: dict = {}


def _one(identity: str) -> tuple[pd.Series, pd.Series]:
    """One strategy in a worker: its mark-to-market P&L per day and each day's lowest equity."""
    trades, value = _STATE["trades"].get_group(identity), _STATE["point_value"]
    cost = paths.entry_commission(trades, _STATE["commission"], value)
    table = days.server_days(
        paths.minute_path(trades, _STATE["bars"], value, cost), CLOCK, CLOCK
    )
    return days.daily_pnl(table), reconcile.low_equity(table)


def calendar(bars: pd.DataFrame) -> pd.DatetimeIndex:
    """Every day the feed has a bar on, naive midnight of the feed's clock."""
    return pd.DatetimeIndex(bars.index.normalize().unique())  # pyright: ignore[reportAttributeAccessIssue]  # stub lacks DatetimeIndex.normalize


def measured(trades: pd.DataFrame) -> tuple[float, dict]:
    """The point value and the commission the backtest itself ran with, read off its trades.

    Args:
        trades: Trades of one feed and one segment (schema T), any number of strategies.

    Returns:
        Account currency per 1.0 of price per lot, and the commission as the asset card
        spells one (`SizeBased`, $ per lot round turn). Fitted on the trades that opened and
        closed the same day, which carry no swap: per lot, `Profit/Loss` = point value x
        signed move − commission, exact to the cent once the few that still carry a
        swap (a rollover inside the same calendar day) are trimmed: 🔬 untrimmed, XAUUSD's
        fit read 6.1 and 8.2 $/lot against the card's 5.0 and lost the day-low match. Measured, not read from the card: 🔬 a
        card recalibrated after the build no longer holds the build's figures (USDJPY's
        point value 653.92 in a build of 2026-09-30, 631.34 on the card four days later).
    """
    same = trades[
        trades["Open time"].dt.normalize() == trades["Close time"].dt.normalize()
    ]
    side = np.where(same["Type"].astype(object) == "Buy", 1.0, -1.0)
    move = side * np.asarray(same["Close price"] - same["Open price"], dtype=np.float64)
    per_lot = np.asarray(same["Profit/Loss"] / same["Size"], dtype=np.float64)
    design, keep = np.c_[move, np.ones(len(move))], np.ones(len(move), dtype=bool)
    value = minus_cost = 0.0
    # Trim the swap-bearing outliers, which drag a plain fit off the card. The bound starts at
    # the median residual: 🔬 a fixed 0.5 kept none of XAUUSD M15's 44 trades after a first
    # fit biased by its swaps (median residual 12 $/lot), and the empty fit read 0.
    for _ in range(5):
        value, minus_cost = np.linalg.lstsq(design[keep], per_lot[keep], rcond=None)[0]
        off = np.abs(per_lot - design @ [value, minus_cost])
        keep = off <= max(0.5, float(np.median(off)))
    return float(value), {"method": "SizeBased", "value": float(-minus_cost)}


def panel(
    trades: pd.DataFrame, bars: pd.DataFrame, point_value: float, commission: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every strategy's daily mark-to-market P&L, and the lowest-equity curve that licenses it.

    Args:
        trades: The trades of ONE segment of one feed (schema T) with an `identity` column.
        bars: That feed's M1 bars over the segment: High, Low, Close, naive bar-open index.
        point_value, commission: What `measured(trades)` returned.

    Returns:
        Two frames, one column per identity, one row per feed day in `bars`: the day's P&L
        marked at the day's last M1 close (flat days 0; a column sums to its trades'
        `Profit/Loss`), and the day's lowest equity since the segment's first trade (NaN
        outside the strategy's own first-to-last trade) — SQX's own curve, to reconcile
        against with `reconcile.curve` before the first frame is trusted.
    """
    grouped = trades.groupby("identity")
    _STATE.update(
        trades=grouped, bars=bars, point_value=point_value, commission=commission
    )
    got = dict(fanout.run(_one, grouped.size().to_dict(), WORKERS))
    _STATE.clear()
    index = calendar(bars)
    pnl = pd.DataFrame({i: got[i][0] for i in sorted(got)}).reindex(index).fillna(0.0)
    low = pd.DataFrame({i: got[i][1] for i in sorted(got)}).reindex(index)
    return pnl, low
