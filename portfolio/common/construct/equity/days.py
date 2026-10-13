"""One row per server day from a minute path, and the daily P&L it implies (contract D)."""

import numpy as np
import pandas as pd

from . import clock

# Building the minute frame is the expensive step (a tz conversion and a group-by over
# millions of rows); server_days() and blocks.blocks() each need it for the same path, so a
# single-entry cache keyed on the path's identity halves the cost of calling both — the same
# trick engines.market.calibrate._ATR_CACHE uses. The path is held in the value so its id
# cannot be recycled under the key while it is still the current one.
_FRAME_CACHE: dict = {}


def _runs(day: pd.Series | pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray] | None:
    """Start row of each day's run and the run lengths, or None if the days are not sorted.

    The path is time-sorted and the day of an instant never decreases in any zone, so each
    day is one contiguous run and a `reduceat` over the starts equals a `groupby("day")`.
    """
    d = np.asarray(day).view("int64")
    if len(d) == 0 or (d[1:] < d[:-1]).any():
        return None
    starts = np.flatnonzero(np.r_[True, d[1:] != d[:-1]])
    return starts, np.diff(np.r_[starts, len(d)])


def _minute_frame(path: dict, feed_zone: str, day_zone: str) -> pd.DataFrame:
    """Path minutes tagged with their server day and day-start equity.

    DST-ambiguous or nonexistent minutes are dropped (`clock.to_utc`); the count is not
    lost, it rides in the returned frame's `attrs["n_nat"]` so `server_days` can pass it on.

    Returns:
        Columns `t` (UTC), `t_i8` (int64 ns epoch, for a fast search into a block grid),
        `day` (naive midnight), `e0` (previous day's closing equity, 0 on the first),
        `worst`, `best`, `close`, `realised`, `open`, `opens`.
    """
    key = (id(path), feed_zone, day_zone)
    if key not in _FRAME_CACHE or _FRAME_CACHE[key][0] is not path:
        naive = pd.DatetimeIndex(path["t"])
        utc, n_nat = clock.to_utc(naive, feed_zone)
        keep = ~utc.isna()
        day = clock.day_of(utc[keep], day_zone)
        frame = pd.DataFrame({"t": utc[keep], "t_i8": utc[keep].astype("int64"), "day": day,
                               "worst": path["worst"][keep], "best": path["best"][keep],
                               "close": path["close"][keep], "realised": path["realised"][keep],
                               "open": path["open"][keep], "opens": path["opens"][keep]})
        runs = _runs(day)
        close = frame["close"].to_numpy()
        if runs is not None and not np.isnan(close).any():
            starts, counts = runs
            prev = np.r_[0.0, close[starts + counts - 1][:-1]]
            frame["e0"] = np.repeat(prev, counts)
        else:   # unsorted days or NaN closes: groupby.last() skips NaN, reduceat would not
            prev_close = frame.groupby("day")["close"].last().shift(1).fillna(0.0)
            frame["e0"] = prev_close.reindex(frame["day"]).to_numpy()
        frame.attrs["n_nat"] = n_nat
        _FRAME_CACHE.clear()
        _FRAME_CACHE[key] = (path, frame)
    return _FRAME_CACHE[key][1]


def server_days(path: dict, feed_zone: str, day_zone: str) -> pd.DataFrame:
    """Fold a minute path into one row per server day (contract D).

    Args:
        path: `minute_path()` output.
        feed_zone: The clock `path["t"]` is stamped in.
        day_zone: The server clock whose midnight cuts a day.

    Returns:
        DataFrame indexed by naive day label: `closed`, `float_end`, `low`, `high`,
        `low_open` (the low over the minutes a position was open, NaN on a flat day — what
        SQX's daily curve samples), `opened`, `open_end`. `attrs["n_nat"]` carries the
        minutes dropped for DST.
    """
    frame = _minute_frame(path, feed_zone, day_zone)
    cols = {k: frame[k].to_numpy() for k in ("worst", "best", "close", "realised", "open", "opens", "e0")}
    runs = _runs(frame["day"])
    opens = cols["opens"]
    # groupby skips NaN and sums with compensation; reduceat does neither, so the fast path
    # takes only NaN-free columns and whole-number opens (sums exact in float).
    if (runs is None or any(np.isnan(cols[k]).any() for k in ("worst", "best", "close", "realised", "open"))
            or np.isnan(opens).any() or (opens != np.floor(opens)).any()):
        return _server_days_groupby(frame)
    starts, counts = runs
    last = starts + counts - 1
    rel_worst, rel_best = cols["worst"] - cols["e0"], cols["best"] - cols["e0"]
    realised, close = cols["realised"][last], cols["close"][last]
    low_open = np.minimum.reduceat(np.where(cols["open"] > 0, rel_worst, np.inf), starts)
    days = pd.DataFrame({
        "closed": realised - np.r_[0.0, realised[:-1]],
        "float_end": close - realised,
        "low": np.minimum.reduceat(rel_worst, starts),
        "high": np.maximum.reduceat(rel_best, starts),
        "low_open": np.where(np.isinf(low_open), np.nan, low_open),
        "opened": np.add.reduceat(opens.astype(np.int64), starts).astype(int),
        "open_end": cols["open"][last] > 0,
    }, index=pd.DatetimeIndex(frame["day"].to_numpy()[starts], name="day"))
    days.attrs["n_nat"] = frame.attrs["n_nat"]
    return days


def _server_days_groupby(frame: pd.DataFrame) -> pd.DataFrame:
    """The general fold, a groupby per column: any day order, NaN-skipping."""
    rel_worst = frame["worst"] - frame["e0"]
    rel_best = frame["best"] - frame["e0"]
    grouped = frame.groupby("day")
    prev_realised = grouped["realised"].last().shift(1).fillna(0.0)
    days = pd.DataFrame({
        "closed": grouped["realised"].last() - prev_realised,
        "float_end": grouped["close"].last() - grouped["realised"].last(),
        "low": rel_worst.groupby(frame["day"]).min(),
        "high": rel_best.groupby(frame["day"]).max(),
        "low_open": rel_worst.where(frame["open"] > 0).groupby(frame["day"]).min(),
        "opened": grouped["opens"].sum().astype(int),
        "open_end": grouped["open"].last() > 0,
    })
    days.attrs["n_nat"] = frame.attrs["n_nat"]
    return days


def daily_pnl(days: pd.DataFrame) -> pd.Series:
    """Mark-to-market P&L per server day.

    Args:
        days: `server_days()` output.

    Returns:
        `closed + float_end − float_end.shift(fill 0)`; summed over a whole strategy this
        equals Σ `Profit/Loss` exactly (the realised P&L anchors each close).
    """
    return days["closed"] + days["float_end"] - days["float_end"].shift(1).fillna(0.0)
