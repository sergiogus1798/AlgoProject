"""The null runs priced and measured in one compiled pass: no (runs x trades) temporaries."""

import numpy as np
from numba import njit

# Column order of what runs() fills; stats.GOOD_HIGH names the same five.
NAMES = ("net", "sharpe", "pf", "retdd", "dd")


@njit(cache=True, nogil=True)
def runs(entries: np.ndarray, holds: np.ndarray, sizes: np.ndarray, enter_px: np.ndarray,
         leave_px: np.ndarray, cost: np.ndarray, value: float, out: np.ndarray) -> None:
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
        `dd` comes from the same sequential cumulative sum and matches exactly.
    """
    n_runs, n = entries.shape
    pnl = np.empty(n)
    for s in range(n_runs):
        net = gain = loss = 0.0
        curve = peak = dd = 0.0
        for k in range(n):
            e = entries[s, k]
            p = value * sizes[s, k] * (leave_px[e + holds[s, k]] - enter_px[e]) - cost[k]
            pnl[k] = p
            net += p
            if p > 0.0:
                gain += p
            elif p < 0.0:
                loss -= p
            curve += p
            peak = curve if k == 0 or curve > peak else peak
            dd = max(dd, peak - curve)
        mean = net / n
        var = 0.0
        for k in range(n):
            var += (pnl[k] - mean) ** 2
        out[s, 0] = net
        out[s, 1] = mean / np.sqrt(var / (n - 1))
        out[s, 2] = gain / loss if loss > 0.0 else np.inf
        out[s, 3] = net / dd if dd > 0.0 else 0.0
        out[s, 4] = dd


@njit(cache=True, nogil=True)
def touched(entries: np.ndarray, holds: np.ndarray, low: np.ndarray, high: np.ndarray,
            stop: np.ndarray, target: np.ndarray) -> tuple:
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
