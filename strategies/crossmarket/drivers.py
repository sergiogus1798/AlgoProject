"""What kind of market this is: the structural properties an edge might depend on (PDF §5.4)."""

import numpy as np
import pandas as pd

from strategies.crossmarket import pricing


def hurst(returns: np.ndarray, lags: list[int]) -> float:
    """Hurst exponent from the growth of the dispersion of lagged differences.

    Args:
        returns: Log returns per bar, NaNs already removed.
        lags: Horizons the slope is fitted over.

    Returns:
        The slope of log std(x[t+k] - x[t]) against log k on the cumulative series. Above 0.5
        the series trends, below it mean-reverts, 0.5 is a random walk. Read as an ordering
        between markets, not as a number with three decimals: it moves with the lag set.
    """
    path = np.cumsum(returns)
    spread = [np.std(path[k:] - path[:-k]) for k in lags]
    return float(np.polyfit(np.log(lags), np.log(spread), 1)[0])


def variance_ratio(returns: np.ndarray, q: int) -> float:
    """Lo-MacKinlay variance ratio at horizon q.

    Args:
        returns: Log returns per bar.
        q: Aggregation horizon in bars.

    Returns:
        Var(q-bar return) / (q * Var(1-bar return)). One is a random walk, above one is
        positive autocorrelation (trend), below one is mean reversion.
    """
    aggregate = np.add.reduceat(returns, np.arange(0, len(returns) - len(returns) % q, q))
    return float(aggregate.var(ddof=1) / (q * returns.var(ddof=1)))


def adx(bars: pd.DataFrame, period: int) -> np.ndarray:
    """Average Directional Index, Wilder's own smoothing.

    Args:
        bars: One market's bars.
        period: Lookback in bars.

    Returns:
        One value per bar; the first entries are NaN. Wilder's exponential smoothing here,
        unlike pricing.atr()'s plain mean, because ADX is only ever defined that way and the
        threshold that reads it is calibrated on that definition.
    """
    up = bars["High"].diff()
    down = -bars["Low"].diff()
    plus = np.where((up > down) & (up > 0), up, 0.0)
    minus = np.where((down > up) & (down > 0), down, 0.0)
    smooth = {"alpha": 1 / period, "adjust": False}
    tr = pd.Series(pricing.atr(bars, 1), index=bars.index).ewm(**smooth).mean()
    di_plus = 100 * pd.Series(plus, index=bars.index).ewm(**smooth).mean() / tr
    di_minus = 100 * pd.Series(minus, index=bars.index).ewm(**smooth).mean() / tr
    dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
    return dx.ewm(**smooth).mean().to_numpy()


def efficiency(bars: pd.DataFrame, window: int) -> np.ndarray:
    """Kaufman efficiency ratio: net move over the path walked to get it.

    Args:
        bars: One market's bars.
        window: Bars the ratio is measured over.

    Returns:
        One value per bar, between 0 and 1. Near one the market goes somewhere in a straight
        line; near zero it covers the same ground repeatedly.
    """
    close = bars["Close"]
    move = (close - close.shift(window)).abs()
    path = close.diff().abs().rolling(window).sum()
    return (move / path).to_numpy()


def profile(bars: pd.DataFrame, cfg: dict) -> dict:
    """Every structural property of one market, over the whole bar file.

    Args:
        bars: One market's bars.
        cfg: What config.load() returned.

    Returns:
        Hurst, variance ratio, the share of bars in an ADX trend, ATR as a share of price,
        the median efficiency ratio, and the window measured. These describe the *market*,
        not the strategy: they are the right-hand side of the edge-driver regression the
        source note asks for, which needs six or more markets before it can be fitted at all.
        With two, read them as a description of where the edge did and did not transfer.
    """
    d = cfg["drivers"]
    returns = np.log(bars["Close"]).diff().dropna().to_numpy()
    trend = adx(bars, d["adx_period"])
    return {"hurst": hurst(returns, d["hurst_lags"]),
            "variance_ratio": variance_ratio(returns, d["variance_ratio_q"]),
            "adx_trend_share": float(np.nanmean(trend > d["adx_trend"])),
            "atr_pct": 100 * pricing.unit(bars),
            "efficiency": float(np.nanmedian(efficiency(bars, d["efficiency_window"]))),
            "bars": len(bars), "from": str(bars.index[0].date()),
            "to": str(bars.index[-1].date())}
