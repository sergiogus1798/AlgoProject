"""Volatility and trend at entry, cut into terciles whose edges never see the sample they tag.

Rule 1 of encargo 14: the cut-offs come from an expanding window or the build segment, never
from the sample being described. This module takes the second, simpler reading — the edges
are the build segment's own tercile boundaries, frozen, and every trade of every sample is
then compared against that fixed pair of numbers, never against its own sample's distribution.
"""

import numpy as np
import pandas as pd

from core import assetdata
from engines.regimes import regime as vol_engine

BUCKETS = ("baja", "media", "alta")


def build_span(symbol: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The asset's build segment, as calendar timestamps.

    Args:
        symbol: Asset name, e.g. "USDJPY".

    Returns:
        (from, to), both inclusive — the only window the tercile edges are allowed to see.
    """
    data = assetdata.load(symbol)
    lo, hi = assetdata.window(data, "build")
    return pd.Timestamp(lo, unit="ms"), pd.Timestamp(hi, unit="ms")


def daily(bars: pd.DataFrame) -> pd.DataFrame:
    """One candle per day, whatever timeframe the strategy trades on.

    Args:
        bars: What core.barstore.read() returned, any intraday timeframe.

    Returns:
        Daily OHLC (engines.regimes.regime.daily): the regime is a fact about the day, not
        about the strategy's own bar size.
    """
    return vol_engine.daily(bars)


def _shift(series: pd.Series) -> pd.Series:
    """Push a daily series one day into the future, so day D reads through D-1's close.

    `engines.regimes.regime.daily()` folds a whole calendar day into one candle — high,
    low and close all include bars that have not happened yet for a trade entering that
    same day. A trade on day D never sees D's own candle here: it reads the value the
    series carried on D-1, the last day that had fully closed before D opened. Found by
    review 2026-09-26 (`_coord/F-review.md`): 79% of USDJPY 2018-01-03's bars, including
    the one setting that day's high, postdate a trade that entered at 05:00 the same day.
    """
    return series.shift(1)


def volatility(day: pd.DataFrame, atr_period: int) -> pd.Series:
    """Daily realised volatility, lagged one day so a trade never reads its own entry day.

    Args:
        day: One candle per day (engines.regimes.regime.daily).
        atr_period: Lookback in trading days.

    Returns:
        One value per day — the ATR as it stood at the PREVIOUS day's close. The first
        atr_period + 1 are NaN.
    """
    return _shift(vol_engine.atr(day, {"atr_period": atr_period})["vol"])


def efficiency(day: pd.DataFrame, window: int) -> pd.Series:
    """Kaufman's efficiency ratio of daily closes, lagged one day for the same reason.

    Args:
        day: One candle per day.
        window: Trading days behind t the ratio looks.

    Returns:
        One value per day in [0, 1] — the ratio as it stood at the PREVIOUS day's close.
        The first `window` + 1 are NaN. 1 is a straight run, near 0 is noise round a flat
        mean.
    """
    close = day["Close"]
    net = (close - close.shift(window)).abs()
    path = close.diff().abs().rolling(window).sum()
    return _shift((net / path).replace([np.inf, -np.inf], np.nan))


def frozen_edges(series: pd.Series, span: tuple[pd.Timestamp, pd.Timestamp]) -> np.ndarray:
    """Tercile cut-offs measured on the build segment alone.

    Args:
        series: A daily series (volatility() or efficiency()).
        span: What build_span() returned.

    Returns:
        [p33, p67] of the values inside the build segment. These two numbers are what every
        later classification compares against — never the sample being read.
    """
    within = series.loc[span[0]:span[1]].to_numpy()
    return np.nanquantile(within, [1 / 3, 2 / 3])


def bucket(series: pd.Series, edges: np.ndarray, days: pd.DatetimeIndex) -> np.ndarray:
    """Which tercile each trade's entry day falls in, against the frozen edges.

    Args:
        series: A daily series, indexed by day.
        edges: What frozen_edges() returned.
        days: One entry day per trade, normalised.

    Returns:
        Index into BUCKETS, or -1 where the day's value is missing or NaN — a day the daily
        series does not cover, or inside the series' own warm-up.
    """
    at = series.reindex(days).to_numpy()
    idx = np.digitize(at, edges)
    return np.where(np.isfinite(at), idx, -1)
