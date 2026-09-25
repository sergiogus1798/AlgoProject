"""Recover from the real trades what SQX charged and how it sized, and prove it reconciles.

Second copy of the point-value and cost measurement `crossmarket/mechanics/pricing.py` makes.
`strategies/CLAUDE.md` promotes a helper to `core/` when a **third** study wants it; two
copies stay where they are, and this note is here so the third one is recognised as the third.
"""

import numpy as np
import pandas as pd


# One entry per (bars, window). A population study calls atr() once per strategy over the
# very same bars -- 234 calls x 39 ms = 9.2 s of the gate's 33 -- and the result depends on
# nothing else. The frame is held in the value so its id cannot be recycled under the key.
_ATR_CACHE: dict = {}


# The lookback both studies price volatility over unless they say otherwise.
ATR_BARS = 14


def atr(frame: pd.DataFrame, window: int = ATR_BARS) -> np.ndarray:
    """Average true range, as a plain rolling mean of the true range.

    Args:
        frame: The bars.
        window: Lookback in bars.

    Returns:
        One value per bar; the first `window` are NaN. Wilder's smoothing is deliberately
        not used: nothing here reproduces an indicator SQX computed. The array is shared,
        not copied: it is read-only to every caller here.
    """
    key = (id(frame), len(frame), window)
    if key not in _ATR_CACHE:
        prev = frame["Close"].shift(1)
        spread = pd.concat([frame["High"] - frame["Low"], (frame["High"] - prev).abs(),
                            (frame["Low"] - prev).abs()], axis=1).max(axis=1)
        _ATR_CACHE.clear()
        _ATR_CACHE[key] = (frame, spread.rolling(window).mean().to_numpy())
    return _ATR_CACHE[key][1]


def point_value(trades: pd.DataFrame) -> float:
    """Account currency per 1.0 of price per 1.0 lot, measured from the trades themselves.

    Args:
        trades: One strategy's trades.

    Returns:
        The slope of profit against price move times size. Measured rather than read from
        the asset file because what has to be reproduced is the simulation SQX already ran,
        not what the instrument ought to be worth. Recovers 99.85 for gold against a
        configured 100.
    """
    move = ((trades["Close price"] - trades["Open price"]) * trades["Size"]).to_numpy()
    return float(np.polyfit(move, trades["Profit/Loss"].to_numpy(), 1)[0])


def charged(trades: pd.DataFrame, value: float) -> np.ndarray:
    """What SQX took off each trade, in account currency.

    Args:
        trades: One strategy's trades.
        value: What point_value() measured.

    Returns:
        One positive cost per trade: the gross move minus the P/L SQX reported. Swap is
        inside it for trades held overnight, which is why it is recovered per trade rather
        than assumed constant.
    """
    move = (trades["Close price"] - trades["Open price"]) * trades["Size"] * value
    return (move - trades["Profit/Loss"]).to_numpy(np.float64)


def sizing(trades: pd.DataFrame, entry_atr: np.ndarray) -> dict:
    """The volatility-normalised sizing rule, recovered and scored.

    Args:
        trades: One strategy's trades.
        entry_atr: ATR at each trade's entry bar, same length.

    Returns:
        Keys `c` -- the constant of `size = c / ATR` -- and `cv`, the dispersion left over.
        A rule that holds exactly leaves cv at 0. Measured across the XAUUSD corpus it sits
        near 0.12 with ATR(50), so the constant is the family and not the parameters: the
        ATR period belongs to the strategy and is read from its `.sqx`, not fitted here.
    """
    product = trades["Size"].to_numpy(np.float64) * entry_atr
    return {"c": float(np.nanmedian(product)),
            "cv": float(np.nanstd(product) / np.nanmean(product))}


CONVENTIONS = {"open-open": ("Open", "Open"), "open-close": ("Open", "Close"),
               "close-open": ("Close", "Open"), "close-close": ("Close", "Close")}


def convention(trades: pd.DataFrame, frame: pd.DataFrame, located: dict, value: float,
               cost: np.ndarray) -> dict:
    """Which bar price SQX filled at, measured rather than assumed.

    Args:
        trades: One strategy's trades.
        frame: The bars.
        located: What inputs.on_grid() returned.
        value: What point_value() measured.
        cost: What charged() returned.

    Returns:
        The winning key of CONVENTIONS, its correlation against the P/L SQX reported, and
        the median gap in account currency. This is the gate the whole study rests on: a
        null run is priced by the same two lines, so a reconstruction that cannot reproduce
        the real run must not be trusted to price an imaginary one.

    🔬 On the XAUUSD corpus (2026-09-22) `open-open` reconciles at 1.0000 and every other
    convention between 0.86 and 0.96 -- 100% of reported entry and exit prices are the open
    of their own bar, which is what `Exit After X Bars` closing on a bar boundary looks like.
    """
    reported = trades["Profit/Loss"].to_numpy(np.float64)
    scored = {}
    for key, (enter, leave) in CONVENTIONS.items():
        move = (frame[leave].to_numpy()[located["exit"]]
                - frame[enter].to_numpy()[located["entry"]])
        rebuilt = value * located["size"] * move - cost
        scored[key] = (float(np.corrcoef(rebuilt, reported)[0, 1]),
                       float(np.median(np.abs(rebuilt - reported))))
    best = max(scored, key=lambda key: scored[key][0])
    return {"fill": best, "corr": scored[best][0], "median_gap": scored[best][1],
            "runner_up": sorted(value[0] for value in scored.values())[-2]}
