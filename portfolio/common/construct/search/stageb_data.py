"""What stage B reads per member on one stretch of server days: day figures, exact minutes, trade units."""

import mmap
from typing import TypedDict, cast

import numba
import numpy as np
import pandas as pd

from core import fanout
from portfolio.common.construct.equity import blocks, paths, stopexit, universe
from portfolio.common.construct.mc import units
from portfolio.common.construct.mc.units import Unit

# Set before the pool forks, so a worker reads the bars and the sources without pickling.
_STATE: dict = {}


class DayArrays(TypedDict):
    """The members' server-day figures on one stretch, as `day_arrays()` returns them."""

    days: np.ndarray
    closed: np.ndarray
    float_end: np.ndarray
    opened: np.ndarray


class StageBData(TypedDict):
    """Everything stage B sums over combinations of, as `prepare()` returns it."""

    days: np.ndarray
    closed: np.ndarray
    float_end: np.ndarray
    opened: np.ndarray
    identities: np.ndarray
    low1: np.ndarray
    high1: np.ndarray
    minute_day: np.ndarray
    units: list[Unit]
    lot_unit: np.ndarray


def day_arrays(day_table: pd.DataFrame, members: list[str], span: tuple, factors: dict) -> DayArrays:
    """The members' server-day figures on one stretch, dense, at unit risk.

    Args:
        day_table: One firm clock's long day table (`equity.store.load()["days"][firm]`).
        members: Identities, in the order the rows follow.
        span: (first, last) day, both inclusive.
        factors: Each member's fixed-risk factor.

    Returns:
        `days` (int64 ns, the stretch's server days some member has), `closed`, `float_end`
        (float64 [N, D]; the floating carried over a member's days without a minute),
        `opened` (int64 [N, D]).
    """
    frame = cast(pd.DataFrame, day_table[(day_table["day"] >= span[0]) & (day_table["day"] <= span[1])])
    days = np.sort(np.asarray(frame["day"].unique())).astype("datetime64[ns]").astype("int64")
    closed = np.zeros((len(members), len(days)))
    float_end = np.zeros_like(closed)
    opened = np.zeros(closed.shape, dtype=np.int64)
    for i, identity in enumerate(members):
        rows = cast(pd.DataFrame, frame[frame["identity"] == identity])
        pos = np.searchsorted(days, rows["day"].to_numpy().astype("datetime64[ns]").astype("int64"))
        closed[i, pos] = rows["closed"].to_numpy() * factors[identity]
        opened[i, pos] = rows["opened"].to_numpy()
        level = np.full(len(days), np.nan)
        level[pos] = rows["float_end"].to_numpy() * factors[identity]
        float_end[i] = pd.Series(level).ffill().fillna(0.0).to_numpy()
    return {"days": days, "closed": closed, "float_end": float_end, "opened": opened}


def _shared(rows: int, columns: int) -> np.ndarray:
    """A float32 matrix a forked worker can write and the parent then reads (anonymous shared map)."""
    buffer = mmap.mmap(-1, max(rows * columns * 4, 1))
    return np.frombuffer(buffer, dtype=np.float32, count=rows * columns).reshape(rows, columns)


def _member(row: int) -> Unit:
    """One member, in a worker: its minute path built once, written to the shared rows, never returned.

    Returns:
        Its trade units (megabytes); the minute arrays stay in `_STATE["low1"]`/`["high1"]`.
    """
    identity = _STATE["members"][row]
    s, factor = _STATE["sources"][identity], _STATE["factors"][identity]
    bars = _STATE["bars"][s["feed"]]
    s = {**s, "trades": stopexit.retime(s["trades"], bars, s["timeframe"])}
    path = paths.minute_path(s["trades"], bars, s["point_value"], universe._commission(s))
    got = blocks.blocks(path, s["clock"], _STATE["zone"], _STATE["grid"])
    _STATE["low1"][row] = got["low"][_STATE["keep"]] * factor
    _STATE["high1"][row] = got["high"][_STATE["keep"]] * factor
    cut = bars.loc[_STATE["cut"][0]:_STATE["cut"][1]]
    where = units.slots(cut.index.to_numpy(), s["clock"], _STATE["zone"], _STATE["days"],
                        _STATE["minutes"])
    return units.units(s["trades"], cut, where, s["point_value"], factor)


def prepare(sources: dict[str, dict], bars: dict[str, pd.DataFrame], day_table: pd.DataFrame,
            zone: str, span: tuple, factors: dict[str, float], min_size: dict[str, float],
            cfg: dict) -> StageBData:
    """Everything stage B sums over combinations of, for the members given, on one stretch.

    Args:
        sources: identity -> `inputs.source.load()`'s dict (`trades`, `feed`, `clock`,
            `point_value`).
        bars: feed -> its M1 bars (High, Low, Close).
        day_table: The firm clock's long day table.
        zone: The firm's server clock.
        span: (first, last) server day of the stretch, both inclusive.
        factors, min_size: Each member's fixed-risk factor and smallest lot.
        cfg: The construct config (`equity.block_minutes`, `compute.max_ram_gb`,
            `stageb.worker_ram_gb`).

    Returns:
        `day_arrays()`'s keys, plus `identities`, `low1`, `high1` (float32 [N, M]: each
        member's worst and best equity per minute of the stretch against its own day's
        opening equity, one UTC grid for all), `minute_day` (int32 [M], index into `days`),
        `units` (one `mc.units.units()` dict per member) and `lot_unit` (float64 [N]).
    """
    members = list(sources)
    out = day_arrays(day_table, members, span, factors)
    days = out["days"]
    # Two days past the end: `blocks.blocks` drops every later minute of a path into the
    # grid's last block, which must therefore sit outside the stretch.
    grid = blocks.grid(cast(pd.Timestamp, pd.Timestamp(days[0]) - pd.Timedelta(days=1)),
                       cast(pd.Timestamp, pd.Timestamp(days[-1]) + pd.Timedelta(days=3)), 1)
    grid_day = blocks.block_days(grid, zone)
    keep = np.isin(grid_day, days)
    low1, high1 = _shared(len(members), int(keep.sum())), _shared(len(members), int(keep.sum()))
    _STATE.update(members=members, sources=sources, factors=factors, bars=bars, zone=zone,
                  grid=grid, keep=keep, days=days, low1=low1, high1=high1,
                  minutes=cfg["equity"]["block_minutes"],
                  cut=(pd.Timestamp(days[0]) - pd.Timedelta(days=3),
                       pd.Timestamp(days[-1]) + pd.Timedelta(days=3)))
    held = (sum(b.memory_usage(deep=True).sum() for b in bars.values()) + 2 * low1.nbytes) / 1e9
    workers = max(1, int((cfg["compute"]["max_ram_gb"] - held) / cfg["stageb"]["worker_ram_gb"]))
    costs = {row: len(sources[m]["trades"]) for row, m in enumerate(members)}
    got = dict(fanout.run(_member, costs, workers))
    _STATE.clear()
    return {**out, "identities": np.array(members), "low1": low1, "high1": high1,
            "minute_day": np.searchsorted(days, grid_day[keep]).astype(np.int32),
            "units": [got[row] for row in range(len(members))],
            "lot_unit": np.array([min_size[m] * factors[m] for m in members])}


def joint(data: StageBData, idxs: np.ndarray) -> dict[str, np.ndarray]:
    """One combination's joint server days, its intraday low and high exact from the minutes.

    Args:
        data: `prepare()` output.
        idxs: The combination's member rows.

    Returns:
        `closed`, `float_end`, `low`, `high` (float64 [D]) and `opened` (int64 [D]) — the
        server-day table D of the combination, at unit risk.
    """
    idxs = np.asarray(idxs, dtype=np.int64)
    low, high = np.zeros(len(data["days"])), np.zeros(len(data["days"]))
    _fold(data["low1"], data["high1"], idxs, data["minute_day"], low, high)
    return {"closed": data["closed"][idxs].sum(axis=0), "float_end": data["float_end"][idxs].sum(axis=0),
            "low": low, "high": high, "opened": data["opened"][idxs].sum(axis=0)}


@numba.njit(cache=True)
def _fold(low1: np.ndarray, high1: np.ndarray, idxs: np.ndarray, minute_day: np.ndarray,
          low: np.ndarray, high: np.ndarray) -> None:
    """Per day, the min and max over its minutes of the members' sum."""
    seen = np.zeros(low.shape[0], dtype=np.bool_)
    for m in range(minute_day.shape[0]):
        lo = 0.0
        hi = 0.0
        for i in idxs:
            lo += low1[i, m]
            hi += high1[i, m]
        d = minute_day[m]
        if not seen[d]:
            low[d], high[d], seen[d] = lo, hi, True
        else:
            low[d] = min(low[d], lo)
            high[d] = max(high[d], hi)
