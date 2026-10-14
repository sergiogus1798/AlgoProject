"""The windowed monkey as a table: where every candidate trade sits in it, and the draws that index it."""

from typing import TypedDict

import numpy as np
import pandas as pd
from numba import njit

from engines.nulls import pcg

# Values of the (draws, trades) matrix filled per pass before numpy averages its rows. Cache
# only: a draw reads the same random numbers whatever the pass.
PASS = 65_536


class Grid(TypedDict):
    """What windowed.grid() shares across a run."""

    bars: pd.DataFrame
    time: np.ndarray
    atr: np.ndarray
    eligible: np.ndarray
    hour: np.ndarray
    by_hour: dict[int, np.ndarray]
    bounds: dict[object, tuple[int, int]]
    last: int


class Located(TypedDict):
    """One strategy's trades on the grid (windowed.located)."""

    entry: np.ndarray
    hold: np.ndarray
    size: np.ndarray
    side: np.ndarray
    hour: np.ndarray
    lo: np.ndarray
    hi: np.ndarray


class Table(TypedDict):
    """windowed.priced()'s table of candidate P/L values."""

    value: np.ndarray
    redraw: bool
    off: np.ndarray
    room: np.ndarray
    hid: np.ndarray


class Layout(TypedDict):
    """layout() — every candidate trade a draw can produce."""

    enter: np.ndarray
    leave: np.ndarray
    side: np.ndarray
    off: np.ndarray
    room: np.ndarray
    hid: np.ndarray


def layout(shared: Grid, mine: Located, redraw: bool) -> Layout:
    """Every trade a draw of one strategy can produce, each listed once.

    Args:
        shared: What windowed.grid() returned.
        mine: What windowed.located() returned.
        redraw: The hold is redrawn from the strategy's own (windowed.REDRAWS).

    Returns:
        `enter`, `leave`, `side`: one row per candidate — an eligible bar of a (window, hour,
        side) at one clipped hold — shared by every trade of that window, hour and side, which
        is what keeps the table small (2 MB where one segment per trade took 59). `off` and
        `room`, (trades, holds): where trade k's candidates under hold j start and how many
        there are; `hid`: the column of each trade's own hold (all 0 when holds are not
        redrawn: one column, the trade's own). The arithmetic is windowed.draw()'s.
    """
    n, last = mine["entry"].size, shared["last"]
    pool, hid = (np.unique(mine["hold"], return_inverse=True) if redraw
                 else (np.empty(0, np.int64), np.zeros(n, np.int64)))
    off, room = (np.empty((n, pool.size if redraw else 1), np.int64) for _ in range(2))
    enter, leave, side, seen, used = [], [], [], {}, 0
    for k in range(n):
        hour, low, top = int(mine["hour"][k]), int(mine["lo"][k]), int(mine["hi"][k])
        key = (hour, low, top, float(mine["side"][k]), None if redraw else int(mine["hold"][k]))
        if key not in seen:
            at_hour = shared["by_hour"][hour]
            if not at_hour.size:
                raise IndexError(f"no eligible bar at hour {hour}: trade {k} entered on a bar "
                                 "the grid never draws (no usable ATR, or outside the session)")
            holds = np.minimum(pool if redraw else mine["hold"][k:k + 1], last - low)
            first = np.searchsorted(at_hour, low)
            rooms = np.maximum(np.searchsorted(at_hour, np.minimum(top, last - holds),
                                               side="right") - first, 1)
            start = np.cumsum(rooms) - rooms
            bar = at_hour[np.minimum(first + np.arange(rooms.sum()) - np.repeat(start, rooms),
                                     at_hour.size - 1)]
            enter.append(bar)
            leave.append(np.minimum(bar + np.repeat(holds, rooms), last))
            side.append(np.full(bar.size, key[3]))
            seen[key] = (used + start, rooms)
            used += bar.size
        off[k], room[k] = seen[key]
    return {"enter": np.concatenate(enter), "leave": np.concatenate(leave),
            "side": np.concatenate(side), "off": off, "room": room, "hid": hid.astype(np.int64)}


# No cache=True: this inlines pcg.py, and numba does not invalidate a disk cache when only that file changes.
@njit(nogil=True)
def _fill(value: np.ndarray, off: np.ndarray, room: np.ndarray, hid: np.ndarray,
          redraw: bool, state: np.ndarray, one: np.ndarray, row: np.ndarray,
          out: np.ndarray) -> None:
    """out[s, k] = the table value draw s gives trade k, on the uniforms numpy would have drawn.

    Draw s reads `rng.random((2, n))`: n uniforms for the entries, then n for the holds, whatever
    the rung (the four share one stream). The second chain starts `row` (n draws) ahead so both
    are read in one pass; a rung that keeps its holds skips the second layer.
    """
    count, n = out.shape
    high, low = state[0], state[1]
    for s in range(count):
        if redraw:
            far, near = pcg.step(high, low, row)
            for k in range(n):
                high, low = pcg.step(high, low, one)
                far, near = pcg.step(far, near, one)
                j = hid[np.int64(pcg.uniform(far, near) * n)]
                out[s, k] = value[off[k, j] + np.int64(pcg.uniform(high, low) * room[k, j])]
            high, low = far, near
        else:
            for k in range(n):
                high, low = pcg.step(high, low, one)
                out[s, k] = value[off[k, 0] + np.int64(pcg.uniform(high, low) * room[k, 0])]
            high, low = pcg.step(high, low, row)
    state[0], state[1] = high, low


def warm() -> None:
    """Compile `_fill` here, once, before a study forks: a fork child that compiles its own took the pool down."""
    one = np.zeros((1, 1), np.int64)
    means({"value": np.zeros(1), "off": one, "room": one + 1, "hid": one[0], "redraw": False}, 1,
          np.random.default_rng(0))


def means(table: Table, draws: int, rng: np.random.Generator) -> np.ndarray:
    """The mean P/L per trade of `draws` monkeys read off a priced table.

    Args:
        table: What windowed.priced() returned; only read, so forked workers can share one.
        draws: How many monkeys.
        rng: Seeded PCG64 generator; left exactly where `rng.random` would have left it.

    Returns:
        One mean per monkey, each the numpy mean of its row, as when every draw was priced.
    """
    n = table["hid"].size
    state, inc = pcg.load(rng)
    one, row = pcg.jump(inc, 1), pcg.jump(inc, n)
    out, held = np.empty(draws), np.empty((max(1, PASS // n), n))
    for done in range(0, draws, len(held)):
        part = held[:draws - done]
        _fill(table["value"], table["off"], table["room"], table["hid"], table["redraw"],
              state, one, row, part)
        out[done:done + len(part)] = part.mean(axis=1)
    pcg.store(rng, state)
    return out
