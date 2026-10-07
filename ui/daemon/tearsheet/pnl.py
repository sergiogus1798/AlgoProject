"""One sample's cumulative P&L: SQX's daily curve, with or without its best trades."""

import math

import pandas as pd


def _best(days: pd.DatetimeIndex, closes: pd.Series, pnl: pd.Series, top: float) -> pd.Series:
    """The running sum of the best `top` % of trades, on the curve's days, to take off it.

    Args:
        days: The curve's days.
        closes: Each trade's close day.
        pnl: Each trade's P&L; the best are ranked by it.
        top: Percent of the trades, at least one trade.
    """
    k = max(1, math.ceil(top / 100 * len(pnl)))
    best = pnl.nlargest(k).groupby(closes).sum()
    return best.reindex(days.union(best.index), fill_value=0.0).cumsum().reindex(days)


def curves(equity: pd.Series, trades: pd.DataFrame, top: float) -> dict[str, pd.Series]:
    """The sample's curves on one daily index, each starting from 0.

    Args:
        equity: Its cumulative P&L per day (equity.parquet), indexed by day.
        trades: Its trades (trades.parquet).
        top: Percent of the best trades to leave out; 0 draws no such curve.

    Returns:
        `sqx`, and with `top`, `sqx_top`: the curve without its best `top` % of trades.
    """
    pnl = equity.diff().fillna(equity.iloc[0])
    out = {"sqx": pnl.cumsum()}
    if top > 0 and len(trades):
        out["sqx_top"] = out["sqx"] - _best(pnl.index, trades["Close time"].dt.normalize(),
                                            trades["Profit/Loss"], top)
    return out
