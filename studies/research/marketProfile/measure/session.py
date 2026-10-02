"""Measures of the clock, written for longs: the best hour, band and weekday, and a band's range."""

import numpy as np

from studies.research.marketProfile.measure.trades import after, prev, tstat


def hour(x: dict, cal: dict) -> tuple:
    """The best hour to hold one bar, judged by the largest t over the 24.

    The null takes its own best hour in every draw, so the choice is paid for in the p.
    """
    r, hr = np.diff(x["o"]), cal["hour"][:-1]
    n = np.bincount(hr, minlength=24)
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = np.bincount(hr, r, 24) / n
        var = (np.bincount(hr, r * r, 24) - n * mean * mean) / (n - 1)
        t = np.where((n >= cal["least"]) & (var > 0), mean / np.sqrt(var / n), -np.inf)
    best = int(np.argmax(t))
    if not np.isfinite(t[best]):
        return 0.0, np.empty(0, int), np.empty(0, int), {}
    idx = np.flatnonzero(hr == best)
    return float(t[best]), idx, idx + 1, {"hour": best}


def _best(x: dict, cal: dict, trades: dict, key: str) -> tuple:
    """The entry-exit set with the largest t among several, the choice named in the detail."""
    scored = [(tstat(x, e, l, cal["least"]), name) for name, (e, l) in trades.items()]
    stat, name = max(scored)
    return stat, *trades[name], {key: name}


def band(x: dict, cal: dict) -> tuple:
    """The best session band to hold from its first bar to its last."""
    return _best(x, cal, cal["bands"], "band")


def weekday(x: dict, cal: dict) -> tuple:
    """The best weekday to hold from its first bar to the next day's first."""
    return _best(x, cal, cal["weekdays"], "weekday")


def band_range(x: dict, cal: dict) -> tuple:
    """Long when, after a band closes, a bar first closes above that band's high."""
    trades = {}
    for name, (inside, later) in cal["ranges"].items():
        top = np.maximum.reduceat(np.where(inside, x["h"], -np.inf), cal["day_first"])[cal["day"]]
        above = later & (x["c"] > top)
        trades[name] = after(above & ~prev(above), cal["range_hold"])
    return _best(x, cal, trades, "band")
