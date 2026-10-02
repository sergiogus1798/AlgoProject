"""A rule a strategy could trade, written for longs: an entry, its filters, an exit — no clock."""

import numpy as np

from studies.research.marketProfile.measure.position import walk
from studies.research.marketProfile.measure.trades import prev, tstat


def _first(mask: np.ndarray) -> np.ndarray:
    """The bar a condition becomes true, not the bars it stays true."""
    return mask & ~prev(mask)


def _down(x: dict, k: int) -> np.ndarray:
    """k closes in a row, each below the one before."""
    one = np.diff(x["c"], prepend=x["c"][0]) < 0
    mask = one.copy()
    for j in range(1, k):
        mask[j:] &= one[:-j]
    return mask


# Every condition a rule may name, on a closed bar, read from prices alone: none looks at the
# hour, the weekday or the date. `d1_*` values are the previous day's (higher.closed). Written
# for longs; the short side is the same condition on the mirrored series.
CONDITIONS = {
    # oversold readings (entries of a reversion)
    "rsi_low": lambda x: x["rsi"] < 10,
    "down3": lambda x: _down(x, 3),
    "extreme2": lambda x: _first(x["c"] < x["sma"] - 2.0 * x["atr"]),
    "d1_rsi_low": lambda x: x["d1_rsi"] < 10,
    # moves that are followed (entries of a trend, a breakout, a momentum)
    "mom_d20": lambda x: x["d1_mom"][20] > 0,
    "mom_d60": lambda x: x["d1_mom"][60] > 0,
    "mom_d120": lambda x: x["d1_mom"][120] > 0,
    "sma50_over_200": lambda x: x["sma50"] > x["sma200"],
    "resume20": lambda x: _first(x["c"] > x["sma"]),
    "break55": lambda x: _first(x["c"] > x["hi"][55]),
    "break_d1": lambda x: _first(x["c"] > x["d1_hi"][1]),
    "break_d20": lambda x: _first(x["c"] > x["d1_hi"][20]),
    "break_d55": lambda x: _first(x["c"] > x["d1_hi"][55]),
    "bar2atr": lambda x: (x["c"] - x["o"]) > 2.0 * x["atr1"],
    # the literature's own entries (AlgoData/research/literature/edges-2026-10-02.yaml)
    "mom_d252": lambda x: x["d1_mom"][252] > 0,
    "slow_d50_200": lambda x: x["d1_above"][50] > x["d1_above"][200],
    "fast_d5_20": lambda x: x["d1_above"][5] > x["d1_above"][20],
    "band10": lambda x: x["c"] > x["sma10"] + x["sd10"],
    "band_d10": lambda x: x["c"] > x["d1_mid"][10] + x["d1_sd"][10],
    "strong_d20": lambda x: x["d1_band"][20] > 1,
    "weak_d20": lambda x: x["d1_band"][20] < -1,
    "chan_30_40": lambda x: (x["d1_mom"][30] < 0) & (x["d1_mom"][40] > 0),
    "noise03": lambda x: x["c"] > x["d1_open"] + 0.3 * x["d1_atr"],
    "noise05": lambda x: x["c"] > x["d1_open"] + 0.5 * x["d1_atr"],
    "noise07": lambda x: x["c"] > x["d1_open"] + 0.7 * x["d1_atr"],
    "noise10": lambda x: x["c"] > x["d1_open"] + 1.0 * x["d1_atr"],
    "day_down": lambda x: x["d1_mom"][1] < 0,
    "mac5_down": lambda x: x["d1_mac"] < 0,
    "week_down": lambda x: x["d1_mom"][5] < 0,
    "ibs_low": lambda x: x["d1_ibs"] < 0.2,
    "out10_low": lambda x: x["d1_out"] < 0,
    "williams": lambda x: (x["d1_mom"][30] > 0) & (x["d1_mom"][9] < 0),
    "d1_down3": lambda x: x["d1_run"] < 0,
    "keltner225": lambda x: _first(x["c"] < x["sma"] - 2.25 * x["atr"]),
    "break_d85": lambda x: _first(x["c"] > x["d1_hi"][85]),
    "week_up": lambda x: x["d1_mom"][5] > 0,
    # the wider frame (filters)
    "mom_d200": lambda x: x["d1_mom"][200] > 0,
    "vol_high": lambda x: x["d1_high"] > 1,
    "vol_low": lambda x: x["d1_high"] < 1,
    "vol_spike": lambda x: x["d1_high"] > 1.5,
    "atr_up": lambda x: x["d1_atrup"] > 1.5,
    "nr_day": lambda x: x["d1_nr"] > 0,
    "squeeze": lambda x: x["d1_squeeze"] <= 0.6,
    "up_d200": lambda x: x["d1_above"][200] > 0,
    "vol_up": lambda x: x["d1_vol"] > 1,
    "vol_down": lambda x: x["d1_vol"] < 1,
    # exits
    "above_sma5": lambda x: x["c"] > x["sma5"],
    "above_sma20": lambda x: x["c"] > x["sma"],
    "d1_above_sma5": lambda x: x["d1_above"][5] > 0,
    "below_d1": lambda x: x["c"] < x["d1_lo"][1],
    "below_d10": lambda x: x["c"] < x["d1_lo"][10],
    "below_d20": lambda x: x["c"] < x["d1_lo"][20],
    "below_d5": lambda x: x["c"] < x["d1_lo"][5],
    "below_d85": lambda x: x["c"] < x["d1_lo"][85],
    "below_d1_open": lambda x: x["c"] < x["d1_open"],
    "d1_above_sma20": lambda x: x["d1_above"][20] > 0,
    "out10_high": lambda x: x["d1_out"] > 0,
}
RULERS = {"bar": "atr1", "day": "d1_atr"}    # what a trailing exit counts its distance in


def met(x: dict, name: str) -> np.ndarray:
    """A named condition on every bar; `not:<name>` is its opposite."""
    with np.errstate(invalid="ignore"):
        if name.startswith("not:"):
            return ~CONDITIONS[name[4:]](x)
        return CONDITIONS[name](x)


def rule(x: dict, cal: dict, enter: str, when: list[str] | None = None,
         leave: str | None = None, cap: int = 0, days: int = 0, trail: float = 0.0,
         ruler: str = "bar") -> tuple:
    """Long at the next open when `enter` and every `when` hold; out on `leave`, cap or trail.

    Args:
        x: The derived series with its wider frame (higher.context).
        cal: The calendar; only `least` and `per_day` (bars in 24 hours) are read.
        enter: A key of CONDITIONS: the entry signal.
        when: Keys of CONDITIONS that must hold on the same bar.
        leave: A key of CONDITIONS (or `not:<key>`) that closes the trade; None for none.
        cap: Most bars held; 0 for no limit.
        days: The cap counted in days of bars (24 hours of the cell's timeframe each).
        trail: Trailing exit in units of `ruler` below the highest close; 0 for none.
        ruler: "bar" for the cell's ATR, "day" for the D1 ATR.

    Returns:
        (t of the trades' returns, entry bars, exit bars, {}) — one position at a time.
    """
    signal = met(x, enter)
    for name in when or []:
        signal = signal & met(x, name)
    out = met(x, leave) if leave else np.zeros(signal.size, dtype=bool)
    entry, exit_ = walk(signal, out, cap + days * cal["per_day"], trail, x["c"], x[RULERS[ruler]])
    return tstat(x, entry, exit_, cal["least"]), entry, exit_, {}
