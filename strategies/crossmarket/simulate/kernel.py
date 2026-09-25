"""A batch of random runs priced, measured and drawn as equity in one compiled pass."""

import numpy as np
from numba import njit


@njit(cache=True, nogil=True)
def batch(entries: np.ndarray, holds: np.ndarray, leave_px: np.ndarray, enter_px: np.ndarray,
          size: np.ndarray, charged: np.ndarray, cost: float, scale: float, equity0: float,
          n_bars: int, stats: np.ndarray, curves: np.ndarray) -> None:
    """What `backtest.price`, `metrics.paths`, the mean return and `equity.path` produce.

    Args:
        entries, holds: (runs, columns) of entry bar and bars held, after the Friday cut.
        leave_px, enter_px: The fill prices of the market's convention, one per bar.
        size, charged: Per real trade; column k reuses trade k modulo their count.
        cost: The cost rate inside the log return.
        scale: The market's unit, dividing the mean return.
        equity0: Starting account.
        n_bars: Bars in the market, for the time step of each exit.
        stats: (runs, len(metrics.NAMES)), filled in that order.
        curves: (runs, steps), zero on entry; each row becomes that run's equity path.

    Returns:
        Nothing; `stats` and `curves` are written. Each trade's P&L is the numpy one operand
        for operand, the equity path and the drawdown come from the same sequential sums, and
        only the plain totals -- net, wins, losses, squares, log returns -- are added in trade
        order where numpy adds pairwise: they can differ in the last bits.
    """
    runs, cols = entries.shape
    steps, m, last = curves.shape[1], size.size, leave_px.size
    for s in range(runs):
        net = wins = loss = squares = logret = 0.0
        count = 0
        cum = peak = dd = dd_pct = run = worst_run = 0.0
        for k in range(cols):
            e, out, a = entries[s, k], entries[s, k] + holds[s, k], k % m
            live = out < last and holds[s, k] > 0
            safe = out if live else 0
            p = 0.0
            if live:
                p = (leave_px[safe] - enter_px[e]) * size[a] - charged[a]
                logret += np.log(leave_px[safe] / enter_px[e]) - cost
                count += 1
            net += p
            squares += p ** 2
            if p > 0.0:
                wins += p
            elif p < 0.0:
                loss -= p
            cum += p
            equity = equity0 + cum
            peak = equity if k == 0 or equity > peak else peak
            dd = max(dd, peak - equity)
            dd_pct = max(dd_pct, (peak - equity) / peak)
            run = run + 1.0 if (p < 0.0 and live) else 0.0
            worst_run = max(worst_run, run)
            curves[s, min((safe * steps) // n_bars, steps - 1)] += p
        mean = net / (count if count > 0 else 1)
        var = (squares - count * mean ** 2) / (count - 1 if count > 1 else 1)
        stats[s, 0] = net
        stats[s, 1] = net / equity0
        stats[s, 2] = dd
        stats[s, 3] = dd_pct
        stats[s, 4] = net / dd if dd > 0.0 else np.nan
        stats[s, 5] = mean / np.sqrt(max(var, 1e-30))
        stats[s, 6] = wins / loss if loss > 0.0 else np.nan
        stats[s, 7] = worst_run
        stats[s, 8] = count
        stats[s, 9] = logret / max(count, 1) / scale
        total = 0.0
        for j in range(steps):
            total += curves[s, j]
            curves[s, j] = equity0 + total
