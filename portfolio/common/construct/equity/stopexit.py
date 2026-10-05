"""A stopped trade's real exit minute: SQX stamps a stop-loss exit at the OPEN of the bar it was hit in."""

import numpy as np
import pandas as pd

INTRABAR = ("SL",)                           # `Close type`s that fill inside the bar, at their own price
MINUTES = {"M": 1, "H": 60, "D": 1440}       # per unit of a timeframe's letter


def retime(trades: pd.DataFrame, bars: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Move each intrabar exit from its bar's open to the M1 minute that reached its price.

    🔬 2026-10-05, 891 stops of 10 NIKKEI225 M30 strategies: every `Close time` is on the M30
    grid and the first M1 whose wick reaches `Close price` comes 0-29 minutes later. Left at
    the stamp, the rebuild books the loss before the price has moved and never sees the low.

    Args:
        trades: One strategy's trades (schema T, plus `Close type`).
        bars: M1 bars with High, Low, indexed by naive bar-open minute.
        timeframe: The grid the strategy trades on, e.g. "M30": how far past the stamp to look.

    Returns:
        The trades, `Close time` of each INTRABAR exit set to the first minute of its bar
        whose wick reaches the exit price — or, when slippage filled it beyond every wick, to
        the bar's most adverse minute. A stamp whose bar has no M1 at all is left alone.
    """
    span = np.timedelta64(MINUTES[timeframe[0]] * int(timeframe[1:]), "m")
    times, low, high = bars.index.to_numpy(), bars["Low"].to_numpy(), bars["High"].to_numpy()
    closes = trades["Close time"].to_numpy().copy()
    price = trades["Close price"].to_numpy(np.float64)
    long = (trades["Type"].astype(object) == "Buy").to_numpy()
    for k in np.flatnonzero(trades["Close type"].astype(str).isin(INTRABAR).to_numpy()):
        a, b = np.searchsorted(times, [closes[k], closes[k] + span])
        if a == b:
            continue
        adverse = price[k] - low[a:b] if long[k] else high[a:b] - price[k]   # ≥ 0: the wick reached it
        reached = np.flatnonzero(adverse >= 0)
        closes[k] = times[a + (reached[0] if reached.size else adverse.argmax())]
    return trades.assign(**{"Close time": closes})


def fills(rebuilt: pd.DataFrame, trades: pd.DataFrame, bars: pd.DataFrame, point_value: float) -> pd.DataFrame:
    """Each trade's excursions with its own exit in them, as SQX counts it.

    🔬 2026-10-05, 2,775 NIKKEI225 trades: a stopped trade's `MAE ($)` is its move to
    `Close price` (891 of 891, to the cent); any other exit's `MAE ($)`/`MFE ($)` reach the
    OPEN of the exit minute, before slippage — 49 trades whose exit bar gapped past every
    earlier wick read short without it.

    Args:
        rebuilt: `excursions.rebuild()` of the retimed trades — wicks up to the exit minute.
        trades: The same trades (schema T, plus `Close type`).
        bars: M1 bars with Open, indexed by naive bar-open minute.
        point_value: Account currency per 1.0 of price per lot.

    Returns:
        `rebuilt`, `mae` no higher and `mfe` no lower than the move to that exit price.
    """
    side = np.where(trades["Type"].astype(object) == "Buy", 1.0, -1.0)
    stopped = trades["Close type"].astype(str).isin(INTRABAR).to_numpy()
    at = np.searchsorted(bars.index.to_numpy(), trades["Close time"].to_numpy(), side="right") - 1
    price = np.where(stopped, trades["Close price"].to_numpy(np.float64), bars["Open"].to_numpy()[at])
    move = side * (price - trades["Open price"].to_numpy()) * trades["Size"].to_numpy() * point_value
    return rebuilt.assign(mae=np.minimum(rebuilt["mae"], move),
                          mfe=np.where(stopped, rebuilt["mfe"], np.maximum(rebuilt["mfe"], move)))
