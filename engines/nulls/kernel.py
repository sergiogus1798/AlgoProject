"""The null runs priced and measured in one compiled pass: no (runs x trades) temporaries."""

import numpy as np
from numba import njit

# Column order of what runs() fills; stats.GOOD_HIGH names the same five.
NAMES = ("net", "sharpe", "pf", "retdd", "dd")


@njit(cache=True, nogil=True, inline="always")
def _drawdown(
    pnl: np.ndarray,
    leave: np.ndarray,
    start: np.ndarray,
    key: np.ndarray,
    val: np.ndarray,
) -> float:
    """The deepest drawdown of one run's curve, its trades added in exit order.

    Args:
        pnl: P/L of each trade, in trade order.
        leave: Exit bar of each trade.
        start: Scratch, at least trades + 1 int64.
        key, val: Scratch, one int64 and one float64 per trade.

    Returns:
        What summing `pnl[np.argsort(leave, kind="mergesort")]` gives, without the sort: the
        exits are integers spread over a window, so a stable count into at most `trades`
        buckets and an insertion pass that only moves what shares a bucket orders them in
        O(trades). Ties keep trade order in both, so the curve is the same sum, bit for bit.
    """
    n = pnl.size
    if n == 0:
        return 0.0
    lo = hi = leave[0]
    for k in range(1, n):
        lo, hi = min(lo, leave[k]), max(hi, leave[k])
    shift = 0
    while (hi - lo) >> shift >= n:
        shift += 1
    buckets = ((hi - lo) >> shift) + 1  # never more than n
    start[: buckets + 1] = 0
    for k in range(n):
        start[((leave[k] - lo) >> shift) + 1] += 1
    for b in range(1, buckets):
        start[b] += start[b - 1]  # trades in the buckets before b
    for k in range(n):  # ascending k: stable
        b = (leave[k] - lo) >> shift
        j = start[b]
        start[b] = j + 1
        key[j], val[j] = leave[k], pnl[k]
    # ponytail: exits piled in a few buckets (one far outlier) make this pass quadratic;
    # the ladder draws them uniform, so it is linear there. A second count level if not.
    for i in range(1, n):
        at, moved, j = key[i], val[i], i - 1
        while j >= 0 and key[j] > at:
            key[j + 1], val[j + 1] = key[j], val[j]
            j -= 1
        key[j + 1], val[j + 1] = at, moved
    curve = peak = dd = 0.0
    for k in range(n):
        curve += val[k]
        peak = max(peak, curve)
        dd = max(dd, peak - curve)
    return dd


@njit(cache=True, nogil=True, error_model="numpy", inline="always")
def _write(
    pnl: np.ndarray, net: float, gain: float, loss: float, dd: float, row: np.ndarray
) -> None:
    """One run's five statistics into its row of `out`, in NAMES order."""
    n = pnl.size
    mean = net / n
    var = 0.0
    for k in range(n):
        var += (pnl[k] - mean) ** 2
    row[0] = net
    row[1] = mean / np.sqrt(var / (n - 1))
    row[2] = gain / loss if loss > 0.0 else np.inf
    row[3] = net / dd if dd > 0.0 else 0.0
    row[4] = dd


@njit(cache=True, nogil=True, error_model="numpy")
def runs(
    entries: np.ndarray,
    holds: np.ndarray,
    sizes: np.ndarray,
    enter_px: np.ndarray,
    leave_px: np.ndarray,
    cost: np.ndarray,
    value: float,
    out: np.ndarray,
) -> None:
    """Price every run of a batch on its time barrier and write its five statistics.

    Args:
        entries, holds, sizes: (runs, trades), as a rung draws them; a row may be a
            broadcast view, since nothing here writes to them.
        enter_px, leave_px: The bar prices an entry and an exit fill at, one per bar.
        cost: What each real trade was charged, reused by the trade in its column.
        value: Account currency per 1.0 of price per lot.
        out: (runs, 5), filled in NAMES order.

    Returns:
        Nothing; `out` is written. Each trade is priced as `barrier.pnl` prices it, operand
        for operand, so a single P/L is bit-identical. The sums run in trade order, where
        numpy sums pairwise: `net`, `sharpe` and `pf` can differ in the last bits, while
        `dd` comes from the same sequential cumulative sum and matches exactly. Adding 0.0
        to `gain` or `loss` for a trade on the other side leaves the sum as it was, NaN included.
    """
    n_runs, n = entries.shape
    pnl, val = np.empty(n), np.empty(n)
    leave, key, start = (
        np.empty(n, np.int64),
        np.empty(n, np.int64),
        np.empty(n + 1, np.int64),
    )
    for s in range(n_runs):
        net = gain = loss = 0.0
        for k in range(n):
            e = entries[s, k]
            leave[k] = e + holds[s, k]
            p = value * sizes[s, k] * (leave_px[leave[k]] - enter_px[e]) - cost[k]
            pnl[k] = p
            net += p
            gain += p if p > 0.0 else 0.0  # a select, not a branch that
            loss -= p if p < 0.0 else 0.0  # mispredicts on half the trades
        _write(pnl, net, gain, loss, _drawdown(pnl, leave, start, key, val), out[s])


@njit(cache=True, nogil=True, error_model="numpy")
def ladder(
    u: np.ndarray,
    holds: np.ndarray,
    sizes: np.ndarray,
    enter_px: np.ndarray,
    leave_px: np.ndarray,
    cost: np.ndarray,
    value: float,
    lo: int,
    hi: int,
    out: np.ndarray,
) -> None:
    """`runs` for a batch a rung drew, placing each trade from its uniform as it prices it.

    Args:
        u: (runs, trades) uniforms, as a rung of `model.RUNGS` returns them unplaced.
        holds, sizes: (runs, trades), as that rung returns them; broadcast views are fine.
        enter_px, leave_px, cost, value, out: As in `runs`.
        lo, hi: `located["window"]`.

    Returns:
        Nothing; `out` is written with exactly what `runs` writes for the entries
        `model._place` computes from `u` -- the same expression, operand for operand --
        without the (runs, trades) int64 matrix of entries in between.
    """
    n_runs, n = u.shape
    pnl, val = np.empty(n), np.empty(n)
    leave, key, start = (
        np.empty(n, np.int64),
        np.empty(n, np.int64),
        np.empty(n + 1, np.int64),
    )
    for s in range(n_runs):
        net = gain = loss = 0.0
        for k in range(n):
            h = holds[s, k]
            e = np.int64(lo + u[s, k] * (hi - h - lo + 1))
            leave[k] = e + h
            p = value * sizes[s, k] * (leave_px[leave[k]] - enter_px[e]) - cost[k]
            pnl[k] = p
            net += p
            gain += p if p > 0.0 else 0.0  # a select, not a branch that
            loss -= p if p < 0.0 else 0.0  # mispredicts on half the trades
        _write(pnl, net, gain, loss, _drawdown(pnl, leave, start, key, val), out[s])


@njit(cache=True, nogil=True, error_model="numpy")
def touched(
    entries: np.ndarray,
    holds: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    stop: np.ndarray,
    target: np.ndarray,
) -> tuple:
    """The first bar of each trade's life on which a price barrier is reached.

    Args:
        entries: Entry bar index of each trade.
        holds: Bars until the vertical barrier.
        low, high: Extremes of every bar.
        stop, target: Price level of each trade's lower and upper barrier.

    Returns:
        What `barrier.touched` returns, from a scan that stops at the first touch instead of
        building the (trades, max hold) matrix: the cost is the bars actually lived.
    """
    m = entries.size
    offset = np.zeros(m, np.int64)
    on_stop = np.zeros(m, np.bool_)
    on_target = np.zeros(m, np.bool_)
    for i in range(m):
        for j in range(1, holds[i] + 1):
            b = entries[i] + j
            hit_s, hit_t = low[b] <= stop[i], high[b] >= target[i]
            if hit_s or hit_t:
                offset[i], on_stop[i], on_target[i] = j, hit_s, hit_t
                break
    return offset, on_stop, on_target
