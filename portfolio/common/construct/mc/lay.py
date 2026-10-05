"""Whole trades laid on a synthetic calendar of server days: the kernels behind T1 and T2."""

import numba
import numpy as np


def stack(members: list[dict]) -> dict[str, np.ndarray]:
    """Every member's units in flat arrays, as the kernels read them.

    Args:
        members: `units.units()` outputs, one per member of the combination.

    Returns:
        `low`, `high`, `level` (float32, all members' blocks), `start`, `n` (where each trade's
        blocks are), `pnl`, `open_day`, `open_slot` per trade, `first` (int64 [K + 1], each
        member's range of trades), `gaps` and `gap_first` (the same for its gaps).
    """
    shift = np.concatenate([[0], np.cumsum([len(m["low"]) for m in members])])
    start = np.concatenate([m["off"][:-1] + s for m, s in zip(members, shift)])
    n = np.concatenate([np.diff(m["off"]) for m in members])
    cat = {k: np.concatenate([m[k] for m in members])
           for k in ("low", "high", "level", "pnl", "open_day", "open_slot", "gaps")}
    first = np.concatenate([[0], np.cumsum([len(m["pnl"]) for m in members])])
    gap_first = np.concatenate([[0], np.cumsum([len(m["gaps"]) for m in members])])
    return {**cat, "start": start.astype(np.int64), "n": n.astype(np.int64),
            "first": first.astype(np.int64), "gap_first": gap_first.astype(np.int64)}


def by_day(flat: dict, n_days: int) -> dict[str, np.ndarray]:
    """The stacked trades sorted by the historical day they opened, with each day's range."""
    order = np.argsort(flat["open_day"], kind="stable")
    ptr = np.searchsorted(flat["open_day"][order], np.arange(n_days + 1)).astype(np.int64)
    return {**flat, **{k: flat[k][order] for k in ("start", "n", "pnl", "open_day", "open_slot")},
            "day_ptr": ptr}


@numba.njit(cache=True)
def _lay(at: int, start: int, n: int, pnl: float, low: np.ndarray, high: np.ndarray,
         level: np.ndarray, s_low: np.ndarray, s_high: np.ndarray, closed: np.ndarray,
         float_end: np.ndarray) -> None:
    """Add one whole trade from absolute block `at`; what falls past the horizon is left open.

    Each block's floating is taken against the trade's own floating at the previous midnight,
    which is what a server day's low and high are measured from (contract D).
    """
    horizon, per_day = s_low.shape
    d = at // per_day
    if d >= horizon:
        return
    carried = np.float32(0.0)
    for q in range(n):
        dq = (at + q) // per_day
        if dq != d:
            carried = level[start + q - 1]
            float_end[d] += carried
            d = dq
            if d >= horizon:
                return
        s = at + q - d * per_day
        s_low[d, s] += low[start + q] - carried
        s_high[d, s] += high[start + q] - carried
    closed[d] += pnl
    rest = np.float32(pnl) - carried
    for s in range(at + n - d * per_day, per_day):
        s_low[d, s] += rest
        s_high[d, s] += rest


@numba.njit(cache=True)
def _fold(s_low: np.ndarray, s_high: np.ndarray, low: np.ndarray, high: np.ndarray) -> None:
    """Each day's joint low and high: the extremes over its blocks of the summed members."""
    for d in range(s_low.shape[0]):
        low[d] = s_low[d].min()
        high[d] = s_high[d].max()


@numba.njit(parallel=True, cache=True)
def t1(start: np.ndarray, n: np.ndarray, pnl: np.ndarray, low: np.ndarray, high: np.ndarray,
       level: np.ndarray, first: np.ndarray, gaps: np.ndarray, gap_first: np.ndarray,
       seeds: np.ndarray, per_day: int, closed: np.ndarray, float_end: np.ndarray,
       day_low: np.ndarray, day_high: np.ndarray, opened: np.ndarray) -> None:
    """Per path and member: trades with replacement, end to end, a drawn gap after each."""
    horizon = closed.shape[1]
    for p in numba.prange(seeds.shape[0]):
        np.random.seed(seeds[p])
        s_low = np.zeros((horizon, per_day), dtype=np.float32)
        s_high = np.zeros((horizon, per_day), dtype=np.float32)
        for m in range(first.shape[0] - 1):
            n_trades = first[m + 1] - first[m]
            n_gaps = gap_first[m + 1] - gap_first[m]
            at = int(np.random.random() * (gaps[gap_first[m] + np.random.randint(0, n_gaps)] + 1))
            while at < horizon * per_day:
                i = first[m] + np.random.randint(0, n_trades)
                _lay(at, start[i], n[i], pnl[i], low, high, level, s_low, s_high, closed[p],
                     float_end[p])
                opened[p, at // per_day] += 1
                gap = gaps[gap_first[m] + np.random.randint(0, n_gaps)]
                at = max(at + n[i] - 1 + gap, at + 1)
        _fold(s_low, s_high, day_low[p], day_high[p])


@numba.njit(parallel=True, cache=True)
def t2(start: np.ndarray, n: np.ndarray, pnl: np.ndarray, open_slot: np.ndarray,
       low: np.ndarray, high: np.ndarray, level: np.ndarray, day_ptr: np.ndarray,
       seeds: np.ndarray, window: float, per_day: int, closed: np.ndarray,
       float_end: np.ndarray, day_low: np.ndarray, day_high: np.ndarray,
       opened: np.ndarray) -> None:
    """Per path: windows of history (geometric lengths), every trade opened in one laid whole."""
    horizon = closed.shape[1]
    n_days = day_ptr.shape[0] - 1
    for p in numba.prange(seeds.shape[0]):
        np.random.seed(seeds[p])
        s_low = np.zeros((horizon, per_day), dtype=np.float32)
        s_high = np.zeros((horizon, per_day), dtype=np.float32)
        cursor = 0
        while cursor < horizon:
            origin = np.random.randint(0, n_days)
            length = np.random.geometric(1.0 / window)
            for j in range(min(length, horizon - cursor)):
                day = (origin + j) % n_days
                for i in range(day_ptr[day], day_ptr[day + 1]):
                    _lay((cursor + j) * per_day + open_slot[i], start[i], n[i], pnl[i], low,
                         high, level, s_low, s_high, closed[p], float_end[p])
                    opened[p, cursor + j] += 1
            cursor += length
        _fold(s_low, s_high, day_low[p], day_high[p])


@numba.njit(cache=True)
def replay(start: np.ndarray, n: np.ndarray, pnl: np.ndarray, open_day: np.ndarray,
           open_slot: np.ndarray, low: np.ndarray, high: np.ndarray, level: np.ndarray,
           per_day: int, closed: np.ndarray, float_end: np.ndarray, day_low: np.ndarray,
           day_high: np.ndarray, opened: np.ndarray) -> None:
    """Every trade on the day and block it really opened: history itself, the laying's known answer."""
    horizon = closed.shape[0]
    s_low = np.zeros((horizon, per_day), dtype=np.float32)
    s_high = np.zeros((horizon, per_day), dtype=np.float32)
    for i in range(start.shape[0]):
        _lay(open_day[i] * per_day + open_slot[i], start[i], n[i], pnl[i], low, high, level,
             s_low, s_high, closed, float_end)
        opened[open_day[i]] += 1
    _fold(s_low, s_high, day_low, day_high)
