"""Each trade's adverse excursion and final result in units of the ATR the stop would have used."""

import numpy as np
import pandas as pd

from core.trades import excursions


def before_entry(index: pd.DatetimeIndex, opens: pd.Series) -> np.ndarray:
    """The position of the last bar closed before each entry.

    Args:
        index: Bar open times of the strategy's timeframe.
        opens: Each trade's `Open time`.

    Returns:
        One bar position per trade: the bar before the one the entry falls in. An entry at a
        bar open and a pending fill inside the bar both read the bar that closed last.
    """
    return index.searchsorted(opens.to_numpy(), side="right") - 2


def measure(trades: pd.DataFrame, index: pd.DatetimeIndex, atr: np.ndarray,
            point_value: float) -> pd.DataFrame:
    """MAE and final result per trade, in ATR of the bar before the entry.

    Args:
        trades: One strategy's trades, any segments, with `segment`.
        index: Bar open times the ATR was computed on.
        atr: `engines.market.atr.sqx` on those bars.
        point_value: Account currency per 1.0 of price and 1.0 of lot.

    Returns:
        The trades with `atr` (price), `mae_atr`, `result_atr` (the net P/L, costs included,
        in ATR) and `winner` (net P/L > 0, the owner's definition). MAE comes from the export,
        measured by SQX on the M1 path in dollars, and is converted with each trade's size.
    """
    out = trades.copy()
    out["atr"] = atr[before_entry(index, trades["Open time"])]
    scale = trades["Size"].to_numpy() * point_value
    out["mae_atr"] = excursions(trades, point_value)["mae"].to_numpy() / out["atr"]
    out["result_atr"] = trades["Profit/Loss"].to_numpy() / scale / out["atr"]
    out["winner"] = trades["Profit/Loss"] > 0
    return out
