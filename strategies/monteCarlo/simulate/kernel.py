"""The core statistics of many equity paths in one compiled pass, without the path matrix."""

import numpy as np
from numba import njit


@njit(cache=True, nogil=True, error_model="numpy")
def _row(pnl: np.ndarray, equity0: float, out: np.ndarray) -> None:
    """Every statistic of `metrics.NAMES` for one path, written into `out`."""
    n = pnl.size
    net = wins = loss = cum = peak = dd = dd_pct = run = worst = 0.0
    for k in range(n):
        p = np.float64(pnl[k])
        net += p
        if p > 0.0:
            wins += p
        elif p < 0.0:
            loss -= p
        cum += p
        equity = equity0 + cum
        peak = equity if k == 0 or equity > peak else peak
        dd = max(dd, peak - equity)
        dd_pct = max(dd_pct, (peak - equity) / peak)
        run = run + 1.0 if p < 0.0 else 0.0
        worst = max(worst, run)
    mean = net / n
    var = 0.0
    for k in range(n):
        var += (np.float64(pnl[k]) - mean) ** 2
    out[0] = net
    out[1] = net / equity0
    out[2] = dd
    out[3] = dd_pct
    out[4] = net / dd if dd > 0.0 else np.nan
    out[5] = mean / np.sqrt(var / (n - 1))
    out[6] = wins / loss if loss > 0.0 else np.nan
    out[7] = worst


@njit(cache=True, nogil=True, error_model="numpy")
def gathered(source: np.ndarray, idx: np.ndarray, equity0: float, out: np.ndarray) -> None:
    """The statistics of the paths `source[idx]`, row by row.

    Args:
        source: The real trades' P&L, float32 as `tiles.batch` casts it.
        idx: (paths, trades) positions into `source`, as a draw model returns them.
        equity0: Starting account.
        out: (paths, len(metrics.NAMES)), filled in that order.

    Returns:
        Nothing; `out` is written. What `metrics.paths(source[idx], equity0)` returns, with
        the gathered matrix never built: each path is read straight out of `source`. The
        drawdown is the same sequential sum and matches exactly; the plain totals are added
        in path order where numpy adds pairwise, and can differ in the last bits.
    """
    row = np.empty(idx.shape[1], dtype=source.dtype)
    for s in range(idx.shape[0]):
        for k in range(idx.shape[1]):
            row[k] = source[idx[s, k]]
        _row(row, equity0, out[s])


@njit(cache=True, nogil=True, error_model="numpy")
def priced(pnl: np.ndarray, equity0: float, out: np.ndarray) -> None:
    """The same statistics for paths a stress model priced whole.

    Args:
        pnl: (paths, trades), one perturbed P&L per trade.
        equity0: Starting account.
        out: (paths, len(metrics.NAMES)).

    Returns:
        Nothing; `out` is written.
    """
    for s in range(pnl.shape[0]):
        _row(pnl[s], equity0, out[s])


def prime() -> None:
    """Compile every layout the draw and stress models hand over, before a study forks.

    Returns:
        Nothing. `block_bootstrap` returns a sliced, non-contiguous index matrix and the rest
        contiguous ones, and each layout is its own compilation; built once in the parent,
        every forked worker inherits the machine code.
    """
    source, idx, out = np.zeros(4, np.float32), np.zeros((2, 6), np.int64), np.empty((2, 8))
    gathered(source, idx, 1.0, out)
    gathered(source, idx[:, :4], 1.0, out)
    priced(np.zeros((2, 4)), 1.0, out)
