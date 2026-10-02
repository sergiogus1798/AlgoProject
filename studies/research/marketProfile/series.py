"""A cell's bars as log arrays with their shared indicators, mirrored for shorts, and resampled."""

import numpy as np
import pandas as pd

from engines.resample import draws

MINUTES = {"M15": 15, "M30": 30, "H1": 60, "H4": 240}


def logs(bars: pd.DataFrame) -> dict:
    """The four prices of every bar, in logs.

    Args:
        bars: Open, High, Low, Close indexed by bar open time.

    Returns:
        {"o", "h", "l", "c"}, one array each. Every measure reads logs, so a resampled
        series can be rebuilt by adding up gaps.
    """
    o, h, l, c = np.log(bars[["Open", "High", "Low", "Close"]].to_numpy(dtype=float).T)
    return {"o": o, "h": h, "l": l, "c": c}


def calendar(index: pd.DatetimeIndex, timeframe: str, cfg: dict) -> dict:
    """What stays in place when the prices are resampled: the clock of every bar.

    Args:
        index: Bar open times, in the feed's clock.
        timeframe: A key of MINUTES.
        cfg: The parsed config.

    Returns:
        Hour and day of each bar, the first bar of each day, and for every session band its
        daily entry and exit bars; `ranges` holds, per band of `range_bands`, the bars inside
        it and the same-day bars after it. A null draw moves returns under this calendar, so
        under the null no hour, band or weekday owns a return.
    """
    hour = index.hour.to_numpy()
    day = pd.factorize(index.normalize())[0]
    first = np.flatnonzero(np.diff(day, prepend=-1))
    n = index.size
    cal = {"hour": hour, "day": day, "day_first": first, "n": n, "year": index.year.to_numpy(),
           "least": cfg["filters"]["min_trades"], "per_day": 1440 // MINUTES[timeframe],
           "bands": {}, "ranges": {}, "weekdays": {},
           "range_hold": max(1, cfg["range_hold_hours"] * 60 // MINUTES[timeframe])}
    for name, (start, end) in cfg["sessions"].items():
        inside = (hour >= start) & (hour < end)
        idx = np.flatnonzero(inside)
        edge = np.flatnonzero(np.diff(day[idx], prepend=-1))
        last = np.append(edge[1:] - 1, idx.size - 1)
        entry, leave = idx[edge], idx[last] + 1
        cal["bands"][name] = (entry[leave < n], leave[leave < n])
        if name in cfg["range_bands"]:
            cal["ranges"][name] = (inside, hour >= end)
    weekday = index[first].weekday.to_numpy()[:-1]
    for w in np.unique(weekday):
        cal["weekdays"][int(w)] = (first[:-1][weekday == w], first[1:][weekday == w])
    return cal


def _mean(a: np.ndarray, n: int) -> np.ndarray:
    """Trailing mean over n bars; the first n-1 are NaN."""
    total = np.cumsum(np.insert(a, 0, 0.0))
    out = np.full(a.size, np.nan)
    out[n - 1:] = (total[n:] - total[:-n]) / n
    return out


def _lag(a: np.ndarray) -> np.ndarray:
    """The series as the previous bar saw it."""
    return np.concatenate([[np.nan], a[:-1]])


def derive(x: dict, cfg: dict) -> dict:
    """The indicators the measures share, computed once per series.

    Args:
        x: What logs() or draw() returned.
        cfg: The `derive` section of the config, periods in bars.

    Returns:
        x plus `atr` (mean true range, in logs) and `atr1` (the same one bar earlier, so a
        bar never inflates its own ruler), `sma` and `sd` of the close, the bar's range `rg`,
        the narrowest and widest bar of the last `narrow`, and per channel length the highest
        high and lowest low of the bars BEFORE each one.
    """
    o, h, l, c = x["o"], x["h"], x["l"], x["c"]
    before = np.concatenate([[c[0]], c[:-1]])
    atr = _mean(np.maximum(h, before) - np.minimum(l, before), cfg["atr"])
    base = c - c[0]
    sma = _mean(base, cfg["mean"])
    sd = np.sqrt(np.maximum(_mean(base * base, cfg["mean"]) - sma * sma, 0.0))
    rg = pd.Series(h - l)
    roll = rg.rolling(cfg["narrow"])
    hs, ls = pd.Series(h), pd.Series(l)
    return {"o": o, "h": h, "l": l, "c": c, "atr": atr, "atr1": _lag(atr), "sma": sma + c[0],
            "sd": sd, "rg": rg.to_numpy(), "narrow": (rg == roll.min()).to_numpy(),
            "wide": (rg == roll.max()).to_numpy(),
            "hi": {n: _lag(hs.rolling(n).max().to_numpy()) for n in cfg["channels"]},
            "lo": {n: _lag(ls.rolling(n).min().to_numpy()) for n in cfg["channels"]}}


def mirror(d: dict) -> dict:
    """The same series upside down, so a measure written for longs reads shorts.

    Args:
        d: What derive() returned.

    Returns:
        Prices negated, highs and lows swapped, channels swapped. A long entry here is a
        short entry on the real series, bar for bar.
    """
    return {**d, "o": -d["o"], "h": -d["l"], "l": -d["h"], "c": -d["c"], "sma": -d["sma"],
            "hi": {n: -v for n, v in d["lo"].items()}, "lo": {n: -v for n, v in d["hi"].items()}}


def gaps(x: dict) -> dict:
    """Each bar as four distances from the previous close: what a null draw reorders."""
    before = np.concatenate([[x["o"][0]], x["c"][:-1]])
    return {k: x[k] - before for k in "ohlc"}


def path(g: dict, start: float) -> dict:
    """A log series rebuilt from per-bar gaps: what logs() returns."""
    c = start + np.cumsum(g["c"])
    before = np.concatenate([[start], c[:-1]])
    return {"o": before + g["o"], "h": before + g["h"], "l": before + g["l"], "c": c}


def draw(g: dict, start: float, model: str, block: int, rng: np.random.Generator) -> dict:
    """One null series: the same bars, in blocks, in another order.

    Args:
        g: What gaps() returned.
        start: The log price the path starts from.
        model: A key of engines.resample.draws.DRAWS.
        block: Bars per block.
        rng: Generator.

    Returns:
        What logs() returns. Volatility and drift are the real ones and so is everything
        shorter than a block; any dependence longer than a block is gone.
    """
    pos = draws.DRAWS[model](1, g["c"].size, rng, block)[0]
    return path({k: v[pos] for k, v in g.items()}, start)


def flipped(x: dict, rng: np.random.Generator) -> dict:
    """The series with every bar turned upside down or not, at the toss of a coin.

    Returns:
        What logs() returns: the real volatility bar by bar, and no direction that depends on
        anything — a series on which every directional measure is null by construction. It is
        what `blocklen` checks a block length against, never a null the profile uses.
    """
    g = gaps(x)
    up = rng.random(g["c"].size) < 0.5
    return path({"o": np.where(up, g["o"], -g["o"]), "c": np.where(up, g["c"], -g["c"]),
                 "h": np.where(up, g["h"], -g["l"]), "l": np.where(up, g["l"], -g["h"])},
                x["o"][0])
