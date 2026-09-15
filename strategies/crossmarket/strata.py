"""The regime state of every bar — volatility quantile times trend sign — for regime_strata."""

import numpy as np
import pandas as pd

from strategies.crossmarket import pricing


def label(bars: pd.DataFrame, s: dict) -> np.ndarray:
    """One stratum id per bar, from what was known before that bar opened.

    Args:
        bars: One market's bars, already sliced to the backtest window.
        s: cfg["strata"] — atr_bins and trend_bars.

    Returns:
        Ids 0 to 2 * atr_bins - 1: the ATR quantile doubled, plus one when the close rose over
        the last trend_bars bars. -1 where either is not yet defined. Both are shifted a bar
        so a bar's own range — the move a trade entered on it is about to make — never
        decides which stratum it belongs to. The quantiles are the window's own.
    """
    vol = pd.Series(pricing.atr(bars)).shift(1).to_numpy()
    close, h = bars["Close"].to_numpy(), s["trend_bars"]
    trend = np.full(close.size, np.nan)
    trend[h + 1:] = close[h:-1] - close[:-h - 1]
    edges = np.nanpercentile(vol, np.linspace(0, 100, s["atr_bins"] + 1)[1:-1])
    ids = np.searchsorted(edges, vol, side="right") * 2 + (trend > 0)
    return np.where(np.isfinite(vol) & np.isfinite(trend), ids, -1)


def index(bars: pd.DataFrame, s: dict) -> dict[str, np.ndarray]:
    """Group every bar with the bars of its stratum, the way envelope.calendar_index groups them.

    Args:
        bars: One market's bars.
        s: cfg["strata"].

    Returns:
        Arrays order, start and size, one entry per bar: the bars of bar i's stratum are
        order[start[i]:start[i] + size[i]]. Drawing a uniform position in that slice is
        drawing a random bar of the same regime.
    """
    key = label(bars, s)
    order = np.argsort(key, kind="stable")
    ordered = key[order]
    start = np.searchsorted(ordered, key)
    return {"order": order, "start": start,
            "size": np.searchsorted(ordered, key, side="right") - start}
