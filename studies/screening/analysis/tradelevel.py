"""The t of a strategy's mean trade, plain or net of the market's own drift over each hold."""

import numpy as np
import pandas as pd


def mean_move(bars: pd.DataFrame, windows: dict) -> dict:
    """The market's mean bar-to-bar close change over each sample's window.

    Args:
        bars: One row per bar, indexed by open time, with `Close`.
        windows: {sample: (first, last)} as strings a DatetimeIndex slices by, e.g.
            {"IS": ("2008", "2017"), "OOS": ("2018", "2022")}.

    Returns:
        {sample: mean change in price units per bar}.
    """
    change = bars["Close"].diff()
    return {sample: float(change[first:last].mean()) for sample, (first, last) in windows.items()}


def drift(trades: pd.DataFrame, bars: pd.DataFrame, move: dict, point_value: float) -> np.ndarray:
    """What the market's drift alone paid each trade for being in it, at the trade's own size.

    Args:
        trades: `Open time`, `Close time`, `Type`, `Size` and `sample`.
        bars: The bars of the strategy's own timeframe, indexed by open time.
        move: What mean_move() returned.
        point_value: Account currency per 1.0 of price per 1.0 lot.

    Returns:
        Per trade, direction x mean move of its sample x bars held x size x point value: the
        mean term `core.significance.footprint` gives a same-footprint random trader.
    """
    grid = bars.index.to_numpy()
    held = (np.searchsorted(grid, trades["Close time"].to_numpy(), side="right")
            - np.searchsorted(grid, trades["Open time"].to_numpy(), side="right"))
    side = np.where(trades["Type"].astype(str) == "Sell", -1.0, 1.0)
    return side * trades["sample"].map(move).to_numpy() * held * trades["Size"].to_numpy() \
        * point_value


def t(trades: pd.DataFrame, value: str) -> pd.DataFrame:
    """The t of the mean of one per-trade column, per strategy.

    Args:
        trades: One sample's trades, already in time order within each `identity`.
        value: The column to test, in account currency.

    Returns:
        Indexed by identity: `n`, `iid` (mean / sd x sqrt(n)) and `ar1`, the same t at the
        AR(1) effective n(1 - rho) / (1 + rho), capped at n so that negative autocorrelation
        cannot manufacture observations, and floored at 2.
    """
    by = trades.groupby("identity", sort=False)[value]
    n = by.size()
    x = (trades[value] - by.transform("mean")).to_numpy()
    keys = trades["identity"].to_numpy()
    lagged = np.where(np.r_[False, keys[1:] == keys[:-1]], x * np.r_[0.0, x[:-1]], 0.0)
    sums = pd.DataFrame({"g0": x * x, "g1": lagged}).groupby(keys, sort=False).sum().reindex(n.index)
    rho = sums["g1"] / sums["g0"]
    effective = np.minimum(n * (1 - rho) / (1 + rho), n).clip(lower=2)
    iid = by.mean() / by.std(ddof=1) * np.sqrt(n)
    return pd.DataFrame({"n": n, "iid": iid, "ar1": iid * np.sqrt(effective / n)})
