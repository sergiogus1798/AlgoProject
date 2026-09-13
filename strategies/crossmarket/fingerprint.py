"""Behavioural fingerprint — descriptive only: does the strategy do the same thing everywhere?
Compared against the base asset (gold), never against chance; see significance.py for that."""

import numpy as np
import pandas as pd
from scipy import stats

from core import trades as tradeio
from strategies.crossmarket import pricing, significance


def holding_ks(held_a: pd.DataFrame, held_b: pd.DataFrame) -> dict:
    """Two-sample KS test comparing holding-time distributions.

    Args:
        held_a: One market's held["hold"] source, from envelope.occupancy().
        held_b: Another market's, normally the base asset's.

    Returns:
        Keys statistic and p. A market whose holds have a wildly different shape from the
        base asset's is doing something else, not one edge working twice.
    """
    result = stats.ks_2samp(held_a["hold"], held_b["hold"])
    return {"statistic": float(result.statistic), "p": float(result.pvalue)}


def excursion_profile(aligned: pd.DataFrame, bars: pd.DataFrame, held: pd.DataFrame,
                      point_value: float) -> dict:
    """MAE/MFE normalised by entry-bar ATR, so markets of different volatility compare.

    Args:
        aligned: One market's trades, already restricted to the rows envelope kept.
        bars: That market's bars.
        held: What envelope.occupancy() returned, same rows as aligned.
        point_value: What pricing.point_value() measured for this market.

    Returns:
        Mean and 25th/75th percentile of MAE and MFE in units of entry-bar ATR.
    """
    excursions = tradeio.excursions(aligned, point_value)
    entry_atr = pricing.atr(bars)[held["entry"].to_numpy()]
    out = {}
    for name in ("mae", "mfe"):
        normalised = excursions[name].to_numpy() / entry_atr
        out[name] = {"mean": float(np.nanmean(normalised)),
                     "p25": float(np.nanpercentile(normalised, 25)),
                     "p75": float(np.nanpercentile(normalised, 75))}
    return out


def return_shape(returns: np.ndarray) -> dict:
    """Skew, kurtosis and tail ratio of the real per-trade returns.

    Args:
        returns: What significance.trade_returns() returned.

    Returns:
        Keys skew, kurtosis and tail_ratio (|p95| / |p5|). A fat left tail on only one market
        is a warning, not a fixable defect of the test.
    """
    return {"skew": float(stats.skew(returns)), "kurtosis": float(stats.kurtosis(returns)),
            "tail_ratio": float(abs(np.percentile(returns, 95)) / abs(np.percentile(returns, 5)))}


def fingerprint(strategy: str, base: dict, market: dict) -> dict:
    """Assemble the three fingerprint pieces for one market against the base asset.

    Args:
        strategy: Strategy name, carried through for the panel's table.
        base: backtest.setting()'s return for the base asset (gold), plus its "bars".
        market: The same, for the additional market.

    Returns:
        Keys strategy, holding_ks, excursion and shape for `market`, ready for the panel's
        table with the base asset's own row shown alongside for comparison.
    """
    held_returns = significance.trade_returns(market, market["bars"])
    return {"strategy": strategy, "holding_ks": holding_ks(market["held"], base["held"]),
            "excursion": excursion_profile(market["aligned"], market["bars"], market["held"],
                                           market["point_value"]),
            "shape": return_shape(held_returns)}
