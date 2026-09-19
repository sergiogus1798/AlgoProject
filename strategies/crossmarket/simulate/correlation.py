"""Cross-market correlation: is this several markets, or one bet sampled several times?

Weekly equity curves, forward-filled across trade-free weeks. A PCA used to live here and was
removed on 2026-09-16: with two or three streams PC1 is close to a function of the mean
pairwise correlation, so it added an axis that carried no information the matrix did not."""

import pandas as pd

from strategies.crossmarket.mechanics import pricing


def weekly_equity(fixed: dict, bars: pd.DataFrame) -> pd.Series:
    """One market's cumulative net return, resampled to weekly.

    Args:
        fixed: What backtest.setting() returned.
        bars: That market's bars.

    Returns:
        A series indexed by week end, forward-filled through weeks with no trade closing.
        Indexed by the real trades' close time, since that is when the P/L is realised.
    """
    net = pricing.realised(bars, fixed["held"], fixed["fill"]["convention"]) - fixed["cost"]
    equity = pd.Series(net, index=pd.DatetimeIndex(fixed["aligned"]["Close time"])).cumsum()
    return equity.resample("W").last().ffill()


def returns_matrix(curves: dict[str, pd.Series]) -> pd.DataFrame:
    """Weekly returns of every curve, aligned on their combined index.

    Args:
        curves: {market or "gold": what weekly_equity() returned}.

    Returns:
        One column per market, one row per week the union of curves covers, gaps
        forward-filled before differencing. The first week is dropped: diff() leaves it NaN.
    """
    return pd.DataFrame(curves).sort_index().ffill().diff().dropna(how="all")


def correlation_matrix(curves: dict[str, pd.Series]) -> pd.DataFrame:
    """Pairwise correlation of weekly returns across markets plus the base asset.

    Args:
        curves: {market or "gold": what weekly_equity() returned}.

    Returns:
        A market x market correlation matrix. Streams at 0.8+ mean the "eight-market
        robustness" is really one macro bet, not independent evidence.
    """
    return returns_matrix(curves).corr()
