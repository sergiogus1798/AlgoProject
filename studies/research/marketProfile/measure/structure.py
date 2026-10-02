"""Measures of the series as a whole: no trade, no direction, only a statistic."""

import numpy as np


def variance_ratio(x: dict, cal: dict, q: int, tail: int) -> tuple:
    """Lo-MacKinlay's variance ratio at q bars, less one.

    Args:
        x: The derived series.
        cal: The calendar (unused).
        q: Horizon in bars.
        tail: +1 reads persistence (ratio above one), -1 reads reversion (below one).
    """
    c = x["c"]
    ratio = np.var(c[q:] - c[:-q]) / (q * np.var(np.diff(c)))
    return tail * (ratio - 1), None, None, {"vr": ratio}


def hurst(x: dict, cal: dict) -> tuple:
    """Hurst exponent less one half, from how the spread of k-bar moves grows with k."""
    c = x["c"]
    lags = 2 ** np.arange(7)
    spread = [np.std(c[k:] - c[:-k]) for k in lags]
    slope = np.polyfit(np.log(lags), np.log(spread), 1)[0]
    return slope - 0.5, None, None, {"hurst": slope}


def adf(x: dict, cal: dict, of: str) -> tuple:
    """Dickey-Fuller regression of the next change on the current level, sign flipped.

    Args:
        x: The derived series.
        cal: The calendar (unused).
        of: "level" for the log close itself (the stationarity test), "deviation" for its
            distance to the moving average (how fast an excursion comes back).

    Returns:
        Minus the t of the slope, so a larger statistic is a stronger pull back; the detail
        carries the half-life in bars.
    """
    z = x["c"] if of == "level" else (x["c"] - x["sma"])[~np.isnan(x["sma"])]
    y, z = np.diff(z), z[:-1] - z[:-1].mean()
    slope = (z @ y) / (z @ z)
    rest = y - y.mean() - slope * z
    t = slope / np.sqrt(rest @ rest / (y.size - 2) / (z @ z))
    half = -np.log(2) / np.log1p(slope) if -1 < slope < 0 else np.inf
    return -t, None, None, {"t": t, "half_life": half}


def range_acf(x: dict, cal: dict, lags: int) -> tuple:
    """Mean autocorrelation of the bar's range over the first `lags` lags."""
    d = x["rg"] - x["rg"].mean()
    acf = np.mean([d[k:] @ d[:-k] for k in range(1, lags + 1)]) / (d @ d)
    return acf, None, None, {"acf": acf}


def narrow_wide(x: dict, cal: dict) -> tuple:
    """Range of the bar after the narrowest of the last k, over the one after the widest.

    Clustering alone puts it far below one; compression that precedes expansion lifts it.
    """
    nxt = x["rg"][1:]
    ratio = nxt[x["narrow"][:-1]].mean() / nxt[x["wide"][:-1]].mean()
    return ratio, None, None, {"ratio": ratio}
