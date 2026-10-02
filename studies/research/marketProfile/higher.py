"""The wider frame of every bar: the D1 context as the day BEFORE left it, and the long averages."""

import numpy as np
import pandas as pd

from studies.research.marketProfile import series

# Keys that change sign when the series is turned upside down, and the level pairs that swap.
SIGNED = ("sma5", "sma10", "sma14", "sma30", "sma50", "sma200", "d1_mom", "d1_above", "d1_band", "d1_mid", "d1_mac",
          "d1_run", "d1_out", "d1_open")
SWAPPED = (("d1_hi", "d1_lo"),)


def _rsi(close: np.ndarray, period: int) -> np.ndarray:
    """Wilder's RSI of a log series, 0-100; NaN until `period` changes exist."""
    step = pd.Series(np.diff(close, prepend=close[0]))
    up = step.clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    down = (-step).clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return (100 * up / (up + down)).to_numpy()


def _sma(close: np.ndarray, n: int) -> np.ndarray:
    """Trailing mean of a log series over n values, computed around its first value."""
    return series._mean(close - close[0], n) + close[0]


def days(x: dict, cal: dict) -> dict:
    """The series as D1 bars, built from the cell's own bars.

    Args:
        x: Log arrays `h`, `l`, `c` of the cell's bars.
        cal: The calendar: `day_first`, the first bar of each day.

    Returns:
        {"h", "l", "c"}: each day's highest high, lowest low and last close.
    """
    first = cal["day_first"]
    last = np.append(first[1:] - 1, x["c"].size - 1)
    return {"h": np.maximum.reduceat(x["h"], first), "l": np.minimum.reduceat(x["l"], first),
            "c": x["c"][last]}


def _streak(close: np.ndarray, k: int) -> np.ndarray:
    """+1 after k higher closes in a row, -1 after k lower ones, else 0."""
    step = np.sign(np.diff(close, prepend=close[0]))
    total = pd.Series(step).rolling(k).sum().to_numpy()
    return np.where(total == k, 1.0, np.where(total == -k, -1.0, 0.0))


def _outside(close: np.ndarray, n: int) -> np.ndarray:
    """+1 when the close is above the highest of the n closes before it, -1 below the lowest."""
    s = pd.Series(close)
    top, bottom = s.rolling(n).max().shift(1).to_numpy(), s.rolling(n).min().shift(1).to_numpy()
    with np.errstate(invalid="ignore"):
        return np.where(close > top, 1.0, np.where(close < bottom, -1.0, 0.0))


def daily(day: dict, cfg: dict) -> dict:
    """The D1 indicators, one value per day, each computed with that day included.

    Args:
        day: What days() returned.
        cfg: The `higher` section of the config, periods in days.

    Returns:
        By N, as dicts: `d1_mom` (close less the close N days earlier), `d1_above` (close less
        its N-day mean), `d1_hi` / `d1_lo` (highest high and lowest low of the last N days),
        `d1_mid`, `d1_sd` and `d1_band` (the N-day mean and deviation of the close, and the
        close's distance to that mean in deviations).
        Arrays: `d1_atr` (mean true range, logs), `d1_vol` (short ATR over long ATR: above one
        the range is expanding), `d1_high` (ATR over its own rolling median: above one the
        volatility is high), `d1_atrup` (ATR over its value `atr` days earlier), `d1_rsi`,
        `d1_ibs` (where
        the close sits in the day's range, 0-1), `d1_mac` (the last four daily returns weighted
        4-3-2-1), `d1_run` (±1 after `streak` closes in a row), `d1_out` (±1 when the close is
        outside the `outside` closes before it), `d1_nr` (the range is the narrowest of
        `narrow` days) and `d1_squeeze` (the range of `squeeze[0]` days over that of
        `squeeze[1]`).
    """
    h, l, c = day["h"], day["l"], day["c"]
    before = np.concatenate([[c[0]], c[:-1]])
    true_range = np.maximum(h, before) - np.minimum(l, before)
    atr = series._mean(true_range, cfg["atr"])
    r = pd.Series(c - before)
    mom = {}
    for n in cfg["momentum"]:
        mom[n] = np.full(c.size, np.nan)
        mom[n][n:] = c[n:] - c[:-n]
    hs, ls, rg = pd.Series(h), pd.Series(l), pd.Series(h - l)
    hi = {n: hs.rolling(n).max().to_numpy() for n in cfg["channels"]}
    lo = {n: ls.rolling(n).min().to_numpy() for n in cfg["channels"]}
    base, mid, sd = c - c[0], {}, {}
    for n in cfg["band"]:
        mean = series._mean(base, n)
        mid[n], sd[n] = mean + c[0], np.sqrt(np.maximum(series._mean(base * base, n) - mean ** 2, 0))
    few, many = cfg["squeeze"]
    with np.errstate(divide="ignore", invalid="ignore"):
        return {"d1_mom": mom, "d1_above": {n: c - _sma(c, n) for n in cfg["means"]},
                "d1_hi": hi, "d1_lo": lo, "d1_atr": atr,
                "d1_vol": series._mean(true_range, cfg["vol"][0])
                / series._mean(true_range, cfg["vol"][1]),
                "d1_high": atr / pd.Series(atr).rolling(cfg["median"]).median().to_numpy(),
                "d1_atrup": atr / np.concatenate([np.full(cfg["atr"], np.nan), atr[:-cfg["atr"]]]),
                "d1_rsi": _rsi(c, cfg["rsi"]), "d1_mid": mid, "d1_sd": sd,
                "d1_band": {n: (c - mid[n]) / sd[n] for n in cfg["band"]},
                "d1_ibs": (c - l) / (h - l),
                "d1_mac": (4 * r + 3 * r.shift(1) + 2 * r.shift(2) + r.shift(3)).to_numpy(),
                "d1_run": _streak(c, cfg["streak"]), "d1_out": _outside(c, cfg["outside"]),
                "d1_nr": (rg == rg.rolling(cfg["narrow"]).min()).to_numpy().astype(float),
                "d1_squeeze": (hi[few] - lo[few]) / (hi[many] - lo[many])}


def closed(values: np.ndarray, cal: dict) -> np.ndarray:
    """A per-day array as each bar may use it: the value of the last day ALREADY closed.

    Every bar of day d reads day d-1, never its own day: the bars of the first day read NaN.
    """
    return np.concatenate([[np.nan], values[:-1]])[cal["day"]]


def context(d: dict, cal: dict, cfg: dict) -> dict:
    """The derived series plus its wider frame.

    Args:
        d: What series.derive() returned.
        cal: The calendar of the cell's bars (`day`, `day_first`).
        cfg: The `higher` section of the config.

    Returns:
        d plus, per bar: the D1 indicators of daily() as the previous day left them; `d1_open`,
        the open of the bar's own day (known from its first bar on); `sma5`, `sma10`, `sma14`,
        `sma30`, `sma50`, `sma200`, `sd10` and `rsi` of the cell's own closes.
    """
    out = dict(d)
    for key, value in daily(days(d, cal), cfg).items():
        out[key] = ({n: closed(v, cal) for n, v in value.items()} if isinstance(value, dict)
                    else closed(value, cal))
    for n in (5, 10, 14, 30, 50, 200):
        out[f"sma{n}"] = _sma(d["c"], n)
    base = d["c"] - d["c"][0]
    out["sd10"] = np.sqrt(np.maximum(series._mean(base * base, 10) - series._mean(base, 10) ** 2, 0))
    out["d1_open"] = d["o"][cal["day_first"]][cal["day"]]
    out["rsi"] = _rsi(d["c"], cfg["rsi"])
    return out


def mirror(d: dict) -> dict:
    """The context upside down, on top of series.mirror: a long rule here is a short there.

    Signed distances and means change sign, the daily channel swaps its two sides, the RSI
    and the IBS are read from the other end; ranges and volatility ratios stay as they are.
    """
    out = series.mirror(d)
    for key in SIGNED:
        out[key] = {n: -v for n, v in d[key].items()} if isinstance(d[key], dict) else -d[key]
    for top, bottom in SWAPPED:
        out[top] = {n: -v for n, v in d[bottom].items()}
        out[bottom] = {n: -v for n, v in d[top].items()}
    out["rsi"], out["d1_rsi"], out["d1_ibs"] = 100 - d["rsi"], 100 - d["d1_rsi"], 1 - d["d1_ibs"]
    return out
