"""The doctrine's position size at any bar: fixed risk over a multiple of the ATR, at the card's point value."""

import numpy as np
import pandas as pd

from core import assetdata
from engines.market import atr


def doctrine() -> dict:
    """The sizing rule every project carries: `Amount` (1R, account currency), `ATRPeriod`,
    `ATRMult`. Read from assets/_build.yaml, never copied."""
    return assetdata.doctrine()["money_management"]["params"]


def entry_atr(bars: pd.DataFrame, period: int) -> np.ndarray:
    """The ATR a trade opening on each bar is sized with: SQX's, of the bar closed before it.

    Args:
        bars: One market's bars, in time order.
        period: The doctrine's ATRPeriod.

    Returns:
        One value per bar, in price; NaN on the first bar, which has none before it.
    """
    return np.concatenate([[np.nan], atr.sqx(bars, period)[:-1]])


def lots(entry_atr_: np.ndarray, point_value: float, params: dict) -> np.ndarray:
    """Lots that lose `Amount` on a move of `ATRMult` ATRs against the trade.

    Args:
        entry_atr_: As entry_atr() returns it.
        point_value: The card's, account currency per unit of price per lot.
        params: As doctrine() returns it.

    Returns:
        Lots per bar, unrounded and uncapped: the doctrine's `Decimals` and `MaxLots` are
        SQX's order plumbing, and rounding would make 1R differ from market to market.
    """
    return params["Amount"] / (params["ATRMult"] * entry_atr_ * point_value)


def usable(entry_atr_: np.ndarray, flat_fraction: float) -> np.ndarray:
    """For each bar, the first bar at or after it a trade can be sized on.

    Args:
        entry_atr_: As entry_atr() returns it.
        flat_fraction: travel.validity.flat_atr_fraction; a bar whose ATR is not above this
            fraction of the median ATR is a defective stretch of the feed. 0 keeps every bar
            with a positive ATR.

    Returns:
        Bar positions, same length. An entry on an excluded bar — the real run's or a random
        one's alike — moves to the position given here; past the last usable bar it is that bar.
    """
    ok = entry_atr_ > flat_fraction * np.nanmedian(entry_atr_)
    at = np.where(ok, np.arange(ok.size), ok.size)
    return np.minimum(np.minimum.accumulate(at[::-1])[::-1], np.flatnonzero(ok)[-1])
