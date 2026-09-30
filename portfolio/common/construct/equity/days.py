"""One row per server day from a minute path, and the daily P&L it implies (contract D)."""

import pandas as pd

from . import clock

# Building the minute frame is the expensive step (a tz conversion and a group-by over
# millions of rows); server_days() and blocks.blocks() each need it for the same path, so a
# single-entry cache keyed on the path's identity halves the cost of calling both — the same
# trick engines.market.calibrate._ATR_CACHE uses. The path is held in the value so its id
# cannot be recycled under the key while it is still the current one.
_FRAME_CACHE: dict = {}


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
        `opened`, `open_end`. `attrs["n_nat"]` carries the minutes dropped for DST.
    """
    frame = _minute_frame(path, feed_zone, day_zone)
    frame["rel_worst"] = frame["worst"] - frame["e0"]
    frame["rel_best"] = frame["best"] - frame["e0"]
    grouped = frame.groupby("day")
    prev_realised = grouped["realised"].last().shift(1).fillna(0.0)
    days = pd.DataFrame({
        "closed": grouped["realised"].last() - prev_realised,
        "float_end": grouped["close"].last() - grouped["realised"].last(),
        "low": grouped["rel_worst"].min(),
        "high": grouped["rel_best"].max(),
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
