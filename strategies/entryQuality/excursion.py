"""The forward path: how far price ran for and against each entry, bar by bar."""

import numpy as np
import pandas as pd


def paths(frame: pd.DataFrame, entry: np.ndarray, side: np.ndarray,
          price: np.ndarray, horizon: int) -> dict:
    """MFE and MAE at every horizon from 1 to `horizon`, one row per trade.

    Args:
        frame: The bars.
        entry: Bar index of each entry.
        side: +1 long, -1 short.
        price: Entry price as SQX filled it.
        horizon: How many bars forward to walk.

    Returns:
        `mfe` and `mae`, both (trades x horizon) and both non-negative, in price. Longs
        take their favourable excursion off the highs and their adverse one off the lows,
        shorts the reverse -- an excursion measured on closes would understate both and
        would understate the adverse one most, since that is the one a stop would have hit.

        The walk starts at the bar **after** the entry bar. The entry bar's own high and
        low are partly before the fill, so counting them would credit the entry with a
        move it could not have caught.
    """
    steps = np.arange(1, horizon + 1)
    idx = entry[:, None] + steps[None, :]
    highs = np.maximum.accumulate(frame["High"].to_numpy()[idx], axis=1)
    lows = np.minimum.accumulate(frame["Low"].to_numpy()[idx], axis=1)
    up, down = highs - price[:, None], price[:, None] - lows
    long = side[:, None] > 0
    return {"mfe": np.where(long, up, down), "mae": np.where(long, down, up)}


def normalised(walk: dict, atr: np.ndarray) -> dict:
    """The same excursions in units of each entry's own volatility.

    Args:
        walk: What `paths` returned.
        atr: ATR at each entry, in price.

    Returns:
        The same two arrays divided by the ATR. Without it a trade taken in a violent week
        dominates the average for reasons that have nothing to do with the signal.
    """
    scale = atr[:, None]
    return {"mfe": walk["mfe"] / scale, "mae": walk["mae"] / scale}
