"""One sample's cumulative P&L: SQX's daily curve and the one at the real costs, each with or without its best trades."""

import math

import pandas as pd

from ui.daemon.strategy.costcurve import REAL


def _best(days: pd.DatetimeIndex, closes: pd.Series, pnl: pd.Series, top: float) -> pd.Series:
    """The running sum of the best `top` % of trades, on the curve's days, to take off it.

    Args:
        days: The curve's days.
        closes: Each trade's close day.
        pnl: Each trade's P&L in the curve's own column; the best are ranked by it.
        top: Percent of the trades, at least one trade.
    """
    k = max(1, math.ceil(top / 100 * len(pnl)))
    best = pnl.nlargest(k).groupby(closes).sum()
    return best.reindex(days.union(best.index), fill_value=0.0).cumsum().reindex(days)


def curves(equity: pd.Series, trades: pd.DataFrame, repriced: pd.DataFrame | None,
           top: float) -> dict[str, pd.Series]:
    """The sample's curves on one daily index, each starting from 0.

    Args:
        equity: Its cumulative P&L per day (equity.parquet), indexed by day.
        trades: Its trades (trades.parquet).
        repriced: Its rows of the `spread` report (`Close time`, `Profit/Loss`, the real
            column), or None when no report repriced it.
        top: Percent of the best trades to leave out; 0 draws no such curve.

    Returns:
        `sqx`, and `real` with a report — SQX's daily curve corrected on each closing day by
        what the real costs change, as `costcurve.curve` does; with `top`, `sqx_top` and
        `real_top`: each curve without its own best `top` % of trades, ranked in its column.
    """
    pnl = equity.diff().fillna(equity.iloc[0])
    real = repriced is not None and len(repriced)
    if real:
        closes = repriced["Close time"].dt.normalize()
        delta = (repriced[REAL] - repriced["Profit/Loss"]).groupby(closes).sum()
        pnl = pnl.reindex(pnl.index.union(delta.index), fill_value=0.0)
    out = {"sqx": pnl.cumsum()}
    if real:
        out["real"] = (pnl + delta.reindex(pnl.index, fill_value=0.0)).cumsum()
    if top > 0 and len(trades):
        out["sqx_top"] = out["sqx"] - _best(pnl.index, trades["Close time"].dt.normalize(),
                                            trades["Profit/Loss"], top)
        if "real" in out:
            out["real_top"] = out["real"] - _best(pnl.index, closes, repriced[REAL], top)
    return out
