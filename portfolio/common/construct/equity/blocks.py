"""M5 floating-equity blocks per member, and a combination's joint day extremes (contract M)."""

import numpy as np
import pandas as pd

from . import clock
from . import days as days_mod


def grid(start: pd.Timestamp, end: pd.Timestamp, minutes: int) -> pd.DatetimeIndex:
    """A UTC grid of block starts covering [start, end].

    Args:
        start, end: Bounds, inclusive; localised to UTC if naive.
        minutes: Block length in minutes.

    Returns:
        Tz-aware UTC `DatetimeIndex`.
    """
    idx = pd.date_range(start, end, freq=f"{minutes}min")
    return idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")


def block_days(grid: pd.DatetimeIndex, day_zone: str) -> np.ndarray:
    """The server day each block falls in, as int64 ns day labels.

    Server midnights fall on whole hours, so no block straddles two days.
    """
    return clock.day_of(grid, day_zone).to_numpy(dtype="int64")


def blocks(path: dict, feed_zone: str, day_zone: str, grid: pd.DatetimeIndex) -> dict[str, np.ndarray]:
    """One member's worst/best floating equity per grid block (contract M).

    Args:
        path: `minute_path()` output.
        feed_zone: The clock `path["t"]` is stamped in.
        day_zone: The server clock whose midnight resets the day's E0.
        grid: Block starts, UTC, as `grid()` returns.

    Returns:
        `low`, `high` float32, length `len(grid)`: the block's min/max of (`worst`/`best` −
        E0 of that minute's server day). A block with no minute carries the member's last
        known level (`close` − E0) of the same server day, 0 before its first minute of the
        day, or 0 outside the path — including a bars gap (a weekend) mid-history.
    """
    frame = days_mod._minute_frame(path, feed_zone, day_zone)
    # int64 ns epoch, not tz-aware Timestamp objects: searchsorted on the latter is 40x slower.
    starts = grid.astype("int64").to_numpy()
    block_idx = np.searchsorted(starts, frame["t_i8"].to_numpy(), side="right") - 1
    inside = (block_idx >= 0) & (block_idx < len(grid))
    block_idx = block_idx[inside]
    rel_worst = (frame["worst"] - frame["e0"]).to_numpy()[inside]
    rel_best = (frame["best"] - frame["e0"]).to_numpy()[inside]
    rel_close = (frame["close"] - frame["e0"]).to_numpy()[inside]

    n = len(grid)
    low = np.full(n, np.nan)
    high = np.full(n, np.nan)
    level = np.full(n, np.nan)
    if len(block_idx):
        # frame is time-sorted, so block_idx is non-decreasing: each block's rows are one
        # run, and a reduceat over those runs replaces a groupby over ~1e6 keys.
        starts_of_run = np.flatnonzero(np.diff(block_idx, prepend=block_idx[0] - 1))
        ids = block_idx[starts_of_run]
        ends_of_run = np.append(starts_of_run[1:], len(block_idx)) - 1
        low[ids] = np.minimum.reduceat(rel_worst, starts_of_run)
        high[ids] = np.maximum.reduceat(rel_best, starts_of_run)
        level[ids] = rel_close[ends_of_run]

    day_per_block = block_days(grid, day_zone)
    filled = pd.Series(level).groupby(day_per_block).ffill().fillna(0.0).to_numpy()
    low = np.where(np.isnan(low), filled, low).astype(np.float32)
    high = np.where(np.isnan(high), filled, high).astype(np.float32)
    return {"low": low, "high": high}


def joint_day_low(members: list[np.ndarray], days: np.ndarray) -> pd.Series:
    """A combination's joint intraday worst: per day, the min over blocks of the members' sum.

    Args:
        members: Each member's `low` block array (contract M), same grid.
        days: `block_days()` output for that grid.

    Returns:
        Series indexed by day label (int64 ns) — exact at block resolution
        (`knowhow/perf/intraday-floating-resolution.md`).
    """
    return pd.Series(np.sum(members, axis=0), index=days).groupby(level=0).min()


def joint_day_high(members: list[np.ndarray], days: np.ndarray) -> pd.Series:
    """A combination's joint intraday best: per day, the max over blocks of the members' sum."""
    return pd.Series(np.sum(members, axis=0), index=days).groupby(level=0).max()
