"""The core statistics of an equity path, computed on thousands of paths at once."""

import numpy as np

NAMES = ("net", "return_pct", "dd", "dd_pct", "ret_dd", "sharpe", "pf", "losing_run")


def _losing_run(pnl: np.ndarray) -> np.ndarray:
    """Longest run of consecutive losing trades, per path.

    Args:
        pnl: One row per path, one column per trade.

    Returns:
        One length per path. The loop is over trades, not over paths: each step is one
        vector operation across every simulation at once.
    """
    run = np.zeros(pnl.shape[0])
    best = np.zeros(pnl.shape[0])
    for j in range(pnl.shape[1]):
        run = (run + 1) * (pnl[:, j] < 0)
        best = np.maximum(best, run)
    return best


def paths(pnl: np.ndarray, equity0: float) -> dict[str, np.ndarray]:
    """Every core statistic of section 2.2, for a batch of simulated paths.

    Args:
        pnl: One row per path, one column per trade, in USD. Additive fixed-risk sizing:
            the equity path is a cumulative sum, never a product.
        equity0: Starting account in USD.

    Returns:
        One array per statistic, all of length len(pnl). ret_dd and pf are NaN for a path
        with no drawdown or no losing trade — an undefined ratio, never a large number
        standing in for one.
    """
    equity = equity0 + np.cumsum(pnl, axis=1)
    peak = np.maximum.accumulate(equity, axis=1)
    drop = peak - equity
    dd = drop.max(axis=1)
    net = pnl.sum(axis=1)
    wins = np.where(pnl > 0, pnl, 0.0).sum(axis=1)
    loss = np.where(pnl < 0, -pnl, 0.0).sum(axis=1)
    return {"net": net, "return_pct": net / equity0,
            "dd": dd, "dd_pct": (drop / peak).max(axis=1),
            "ret_dd": np.where(dd > 0, net / np.where(dd > 0, dd, 1.0), np.nan),
            "sharpe": pnl.mean(axis=1) / pnl.std(axis=1, ddof=1),
            "pf": np.where(loss > 0, wins / np.where(loss > 0, loss, 1.0), np.nan),
            "losing_run": _losing_run(pnl)}


def observed(pnl: np.ndarray, equity0: float) -> dict[str, float]:
    """The same statistics for the one real backtest.

    Args:
        pnl: Net USD per trade, in the order they happened.
        equity0: Starting account in USD.

    Returns:
        One number per statistic.
    """
    return {k: float(v[0]) for k, v in paths(pnl[None, :], equity0).items()}


def summarise(values: np.ndarray, seen: float, qs: list[int]) -> dict:
    """One simulated distribution reduced to the numbers the report prints.

    Args:
        values: One statistic, one entry per simulation.
        seen: The observed backtest's value of that statistic.
        qs: Percentiles to report.

    Returns:
        Each requested percentile, the mean and median, and where the observed value ranks
        inside the distribution. A high rank on a good-side statistic is what a lucky
        backtest looks like: most simulations did worse than the one that was run.
    """
    clean = values[np.isfinite(values)]
    std = float(clean.std(ddof=1))
    kurt = float(((clean - clean.mean()) ** 4).mean() / std ** 4 - 3.0) if std else 0.0
    return {"p": {q: float(np.percentile(clean, q)) for q in qs},
            "mean": float(clean.mean()), "median": float(np.median(clean)), "std": std,
            "kurtosis": kurt, "observed": float(seen), "rank": float(np.mean(clean <= seen)),
            "n": int(clean.size)}


def shape(values: np.ndarray, seen: float, q: int, bins: int = 60) -> dict:
    """A distribution reduced to something a chart can draw.

    Args:
        values: One statistic, one entry per simulation.
        seen: The observed backtest's value.
        q: The percentile every histogram marks alongside the backtest and the median —
            cfg["global"]["report_percentile"], so the mark on the picture is always the
            same number the tables read.
        bins: Histogram bins.

    Returns:
        Bin counts and the range they cover, widened to include the observed value so it is
        always on the axis. Kept instead of the raw draws: a databank's draws are gigabytes
        and a histogram is a few hundred bytes.
    """
    clean = values[np.isfinite(values)]
    lo, hi = min(float(clean.min()), seen), max(float(clean.max()), seen)
    # A statistic the model preserves — net profit under a reordering — has a range of
    # zero, or of a few float wobbles around a large number, which no histogram can bin.
    # It is still drawn, as one bar where the backtest sits.
    floor = max(abs(lo), abs(hi), 1.0) * 1e-9 * bins
    if hi - lo < floor:
        middle = (lo + hi) / 2
        lo, hi = middle - floor / 2, middle + floor / 2
    counts, edges = np.histogram(clean, bins=bins, range=(lo, hi))
    return {"counts": counts.tolist(), "lo": float(edges[0]), "hi": float(edges[-1]),
            "observed": float(seen), "median": float(np.median(clean)),
            "p_report": float(np.percentile(clean, q))}


def table(stats: dict[str, np.ndarray], seen: dict[str, float], qs: list[int]) -> dict:
    """Every statistic of one sub-run, against what the backtest actually did.

    Args:
        stats: One array per statistic, from a simulated sub-run.
        seen: The observed backtest's statistics.
        qs: Percentiles to report.

    Returns:
        {statistic: what summarise() returned}.
    """
    return {k: summarise(v, seen[k], qs) for k, v in stats.items()}


def shapes(stats: dict[str, np.ndarray], seen: dict[str, float], q: int) -> dict:
    """A drawable histogram of every statistic of one sub-run.

    Args:
        stats: One array per statistic, from a simulated sub-run.
        seen: The observed backtest's statistics.
        q: The percentile every histogram marks; see shape().

    Returns:
        {statistic: what shape() returned}. Kept for every sub-run so the panel can draw
        any of them without simulating again: a few hundred bytes each against the
        gigabytes the raw draws would be.
    """
    return {k: shape(v, seen[k], q) for k, v in stats.items()}
