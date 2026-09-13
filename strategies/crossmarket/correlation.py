"""Cross-market correlation and factor structure: is this eight markets, or one bet sampled
eight times? Weekly equity curves, as the owner decided, forward-filled across trade-free weeks."""

import numpy as np
import pandas as pd

from strategies.crossmarket import pricing


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


def pca(matrix: pd.DataFrame) -> dict:
    """Principal components of the weekly return streams, by SVD.

    Args:
        matrix: What returns_matrix() returned.

    Returns:
        Keys variance_share (one fraction per component) and pc1. The PDF's gate is
        pc1 < 0.70: above that the diversification across markets is illusory.
    """
    standardised = ((matrix - matrix.mean()) / matrix.std(ddof=0)).dropna()
    _, s, _ = np.linalg.svd(standardised.to_numpy(), full_matrices=False)
    variance_share = (s ** 2) / (s ** 2).sum()
    return {"variance_share": variance_share.tolist(), "pc1": float(variance_share[0])}
