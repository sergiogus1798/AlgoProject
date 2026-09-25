"""Family D in market state: the daily volatility a trade was opened into, and its tercile."""

import numpy as np
import pandas as pd

BUCKETS = ("low", "mid", "high")


def daily(bars: pd.DataFrame) -> pd.DataFrame:
    """Intraday bars collapsed to one candle per day.

    Args:
        bars: What core.bars.read() returned, any intraday timeframe.

    Returns:
        Daily OHLC. The regime is defined on daily data whatever the strategy trades:
        an M30 range is a fact about the last half hour, not about the market's state.
    """
    out = bars.resample("1D").agg({"Open": "first", "High": "max", "Low": "min",
                                   "Close": "last"})
    return out.dropna()


def atr(day: pd.DataFrame, cfg: dict) -> dict:
    """Wilder-smoothed Average True Range of the daily candles.

    Args:
        day: What daily() returned.
        cfg: The family_d section of the config.

    Returns:
        The volatility series, the model that produced it and a note for the report. Zero
        fitted parameters, which is the reason it is the default: a regime definition with
        knobs is a place for the researcher to keep choosing until the buckets say
        something.
    """
    prev = day["Close"].shift(1)
    span = pd.concat([day["High"] - day["Low"], (day["High"] - prev).abs(),
                      (day["Low"] - prev).abs()], axis=1).max(axis=1)
    period = cfg["atr_period"]
    return {"vol": span.ewm(alpha=1 / period, adjust=False, min_periods=period).mean(),
            "model": f"ATR({period}) diario", "note": ""}


def garch(day: pd.DataFrame, cfg: dict) -> dict:
    """Conditional volatility of daily returns under a GARCH model.

    Args:
        day: What daily() returned.
        cfg: The family_d section of the config.

    Returns:
        The same contract atr() returns. Falls back to ATR and says so when the optimiser
        does not converge, which happens on short or heavily gapped histories. Orders above
        (1,1) are available and are not recommended: they add parameters that are hard to
        estimate to a module whose whole purpose is to avoid fitted choices.
    """
    from arch import arch_model
    returns = 100 * np.log(day["Close"]).diff().dropna()
    p, q = cfg["garch_order"]
    fit = arch_model(returns, p=p, q=q, dist=cfg["garch_dist"]).fit(disp="off")
    if not fit.convergence_flag == 0:
        return {**atr(day, cfg), "note": "GARCH no convergió; se usó ATR"}
    return {"vol": fit.conditional_volatility.reindex(day.index),
            "model": f"GARCH{tuple(cfg['garch_order'])} diario, dist {cfg['garch_dist']}",
            "note": ""}


VOL = {"atr": atr, "garch": garch}


def tag(opens: np.ndarray, vol: pd.Series) -> dict:
    """Which volatility tercile each trade was opened into.

    Args:
        opens: Open time of every trade, in stream order.
        vol: What a VOL model returned as "vol", indexed by day.

    Returns:
        The positions in each of BUCKETS, the tercile boundaries, and the share of trades
        the daily series could label. A trade whose day is absent from the bar file is a
        symbol or feed mismatch and raises: imputing it would silently compare a strategy
        against another instrument's regimes.
    """
    days = pd.DatetimeIndex(opens).normalize()
    missing = int((~days.isin(vol.index)).sum())
    if missing:
        raise ValueError(f"{missing} trades open on days the bar file does not have")
    at = vol.reindex(days).to_numpy()
    edges = np.nanquantile(at, [1 / 3, 2 / 3])
    where = np.digitize(at, edges)
    return {"positions": {b: np.flatnonzero(np.isfinite(at) & (where == i))
                          for i, b in enumerate(BUCKETS)},
            "edges": [float(e) for e in edges],
            "coverage": float(np.mean(np.isfinite(at)))}
