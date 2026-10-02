"""Measures that trade a price event, written for longs: trend, breakout, reversion, momentum."""

import numpy as np

from studies.research.marketProfile.measure.trades import after, prev, tstat


def _trade(x: dict, cal: dict, mask: np.ndarray, hold: int, detail: dict | None = None) -> tuple:
    """A signal as (statistic, entry, exit, detail)."""
    entry, leave = after(mask, hold)
    return tstat(x, entry, leave, cal["least"]), entry, leave, detail or {}


def lookback(x: dict, cal: dict, L: int, H: int) -> tuple:
    """Long for H bars when the last L bars went up: does the past move predict the next."""
    c = x["c"]
    mask = np.zeros(c.size, dtype=bool)
    mask[L:] = c[L:] > c[:-L]
    return _trade(x, cal, mask, H)


def above_band(x: dict, cal: dict, k: float, H: int) -> tuple:
    """Fitschen's map: long while the close is k deviations above its mean — follow or fade."""
    return _trade(x, cal, x["c"] > x["sma"] + k * x["sd"], H)


def _breaks(x: dict, N: int) -> np.ndarray:
    """The first close above the highest high of the N bars before it."""
    out = x["c"] > x["hi"][N]
    return out & ~prev(out)


def breakout(x: dict, cal: dict, N: int, H: int) -> tuple:
    """Long for H bars after the first close outside the N-bar channel.

    The detail carries the characteristic size of the break and the ATR at it, in logs.
    """
    mask = _breaks(x, N)
    return _trade(x, cal, mask, H, {"size": float(np.median((x["c"] - x["hi"][N])[mask])),
                                    "atr": float(np.nanmedian(x["atr1"][mask]))})


def false_break(x: dict, cal: dict, N: int, within: int) -> tuple:
    """Minus the share of channel breaks that close back inside within a few bars.

    No trade: a rate. The detail carries the rate and the false breaks per year.
    """
    c, n = x["c"], x["c"].size
    idx = np.flatnonzero(_breaks(x, N)[: n - within])
    if idx.size < cal["least"]:
        return 0.0, None, None, {}
    level = x["hi"][N][idx]
    back = np.zeros(idx.size, dtype=bool)
    for j in range(1, within + 1):
        back |= c[idx + j] < level
    years = np.unique(cal["year"]).size
    return -back.mean(), None, None, {"false_rate": back.mean(), "per_year": back.sum() / years}


def extreme(x: dict, cal: dict, k: float, H: int) -> tuple:
    """Long for H bars when the close first falls k ATR below its mean: the stretch undone."""
    below = x["c"] < x["sma"] - k * x["atr"]
    return _trade(x, cal, below & ~prev(below), H)


def big_bar(x: dict, cal: dict, m: float, H: int) -> tuple:
    """Long for H bars after an up bar whose body exceeds m ATR of the bars before it."""
    return _trade(x, cal, (x["c"] - x["o"]) > m * x["atr1"], H)


def narrow_break(x: dict, cal: dict, H: int) -> tuple:
    """Long for H bars when the bar after the narrowest of the last k closes above its high."""
    mask = np.zeros(x["c"].size, dtype=bool)
    mask[1:] = x["narrow"][:-1] & (x["c"][1:] > x["h"][:-1])
    return _trade(x, cal, mask, H)
