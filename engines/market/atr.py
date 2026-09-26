"""The ATR exactly as SQX computes it for an ATR-based stop: Wilder with an averaged start."""

import numpy as np
import pandas as pd

ROUND = 6       # ATRBasedValue multiplies X by SQUtils.round(atr, 6), not by the raw value


def true_range(frame: pd.DataFrame) -> np.ndarray:
    """High-low widened to the previous close, the first bar's being its own high-low.

    Args:
        frame: Bars with High, Low and Close, in time order.

    Returns:
        One value per bar, in price.
    """
    high, low, close = (frame[c].to_numpy(dtype=float) for c in ("High", "Low", "Close"))
    prev = np.concatenate([[np.nan], close[:-1]])
    out = np.fmax(high - low, np.fmax(np.abs(high - prev), np.abs(low - prev)))
    out[0] = high[0] - low[0]
    return out


def sqx(frame: pd.DataFrame, period: int = 20) -> np.ndarray:
    """SQX's ATR on every bar, rounded as the stop formula rounds it.

    The recurrence of Blocks/Indicators/ATR/ATR.java: the divisor grows 1, 2, ... up to
    `period` and then stays, so the first `period` bars are a running mean and the rest are
    Wilder's smoothing. It depends on where the series starts, and forgets that start at
    (1 - 1/period) per bar: at 20, under 1e-6 after 270 bars.

    Args:
        frame: Bars with High, Low and Close, in time order, on the strategy's timeframe.
        period: The ATR period; the chain's stop always uses 20.

    Returns:
        One value per bar, the ATR as it stood at that bar's close, in price.
    """
    tr = true_range(frame)
    out = np.empty_like(tr)
    value = tr[0]
    out[0] = value
    for i in range(1, len(tr)):
        n = min(i + 1, period)
        value = ((n - 1) * value + tr[i]) / n
        out[i] = value
    return np.round(out, ROUND)
