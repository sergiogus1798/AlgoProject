"""The replay at delay 0 against SQX's own trade list: same exit bar, same reason, same price."""

from typing import TypedDict

import numpy as np
import pandas as pd

from engines.market.replay.walk import Walked


class Match(TypedDict):
    """How far a delay-0 replay reproduces SQX, trade by trade and in total."""

    same_bar: np.ndarray  # bool per trade: exit in the bar SQX stamped
    same_reason: np.ndarray  # bool per trade: stopped exactly when SQX says SL
    price_gap: (
        np.ndarray
    )  # |replayed exit fill − SQX's Close price|, price; NaN off a stop
    rate: float  # share of trades with same bar AND same reason
    stops_within: (
        float  # share of SQX's stops whose replayed fill is within `tolerance`
    )


def reconcile(
    walked: Walked,
    trades: pd.DataFrame,
    tolerance: float,
) -> Match:
    """Compare a delay-0 `walk.replay` with what SQX exported.

    Args:
        walked: `walk.replay(..., delay=0, ...)`.
        trades: The rows replayed, with SQX's `leave` (exit bar), `Close type`, `Close price`
            (the fill, slippage included), `side` (+1/-1) and `slippage` (in price, of the
            segment the trade ran in).
        tolerance: Largest fill gap, in price, that counts as the same stop fill.

    Returns:
        The per-trade comparison and its two shares. Nothing is judged here: what rate is
        good enough is the caller's.
    """
    leave, close_price, side, slippage = (
        trades[k].to_numpy() for k in ("leave", "Close price", "side", "slippage")
    )
    kind = trades["Close type"].astype(str).to_numpy()
    sqx_stop = kind == "SL"
    same_reason = walked["stopped"] == sqx_stop
    same_bar = walked["leave"] == leave
    fill = walked["exit_raw"] - side * slippage
    gap = np.where(sqx_stop & walked["stopped"], np.abs(fill - close_price), np.nan)
    within = (np.nan_to_num(gap, nan=np.inf) <= tolerance)[sqx_stop]
    return {
        "same_bar": same_bar,
        "same_reason": same_reason,
        "price_gap": gap,
        "rate": float((same_bar & same_reason).mean()) if kind.size else float("nan"),
        "stops_within": float(within.mean()) if within.size else float("nan"),
    }
