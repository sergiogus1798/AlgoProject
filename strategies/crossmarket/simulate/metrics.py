"""The statistics of a whole backtest, computed on thousands of random runs at once."""

import numpy as np

# Every statistic the study reports for a run, and whether more of it is better. The
# direction is not decoration: for `dd` and `losing_run` a real run sitting high in its null
# means it drew down worse than chance, which reads the opposite way round from `net`.
HIGHER_IS_BETTER = {"net": True, "return_pct": True, "dd": False, "dd_pct": False,
                    "ret_dd": True, "sharpe": True, "pf": True, "losing_run": False,
                    "trades": True, "mean_r": True}
NAMES = tuple(HIGHER_IS_BETTER)
# What the metric table shows. `trades` is computed because the statistics need the count,
# but every shipped model draws the real number of trades, so its "distribution" is one value
# and any pass/fail colouring on it would be noise. The real count is in the checks table.
TABLED = tuple(n for n in NAMES if n != "trades")
# The statistics keep their industry names in English, the way a reader of any backtesting
# report expects them; the sentences around them are Spanish because the owner reads those.
LABELS = {"net": "Net profit", "return_pct": "Return on account",
          "dd": "Max drawdown", "dd_pct": "Max drawdown %",
          "ret_dd": "Return/DD", "sharpe": "Sharpe per trade",
          "pf": "Profit factor", "losing_run": "Longest losing run",
          "trades": "Trades", "mean_r": "Mean return per trade (ATR units)"}
UNITS = {"net": "$", "dd": "$", "return_pct": "%", "dd_pct": "%", "ret_dd": "",
         "sharpe": "", "pf": "", "losing_run": "ops", "trades": "ops", "mean_r": ""}


def _losing_run(pnl: np.ndarray, live: np.ndarray) -> np.ndarray:
    """Longest run of consecutive losing trades, per path.

    Args:
        pnl: One row per path, one column per trade, in USD.
        live: Same shape, False where that column is not a trade of that path.

    Returns:
        One length per path. The loop is over trades, not over paths: each step is one
        vector operation across every run at once.
    """
    run = np.zeros(pnl.shape[0])
    best = np.zeros(pnl.shape[0])
    for j in range(pnl.shape[1]):
        run = (run + 1) * (pnl[:, j] < 0) * live[:, j]
        best = np.maximum(best, run)
    return best


def paths(pnl: np.ndarray, live: np.ndarray, equity0: float) -> dict:
    """Every statistic of a batch of runs.

    Args:
        pnl: One row per run, one column per trade, in USD, zero where not a trade.
        live: Same shape, False where that column is not a trade of that run — the renewal
            model gives each run its own trade count, and the Friday close cuts a few holds
            to nothing under every model.
        equity0: Starting account in USD.

    Returns:
        One array per statistic, all of length len(pnl). ret_dd and pf are NaN for a run
        with no drawdown or no losing trade — an undefined ratio, never a large number
        standing in for one. The equity path is a cumulative sum: fixed sizing came from
        the real trades, so it is additive and never compounded.
    """
    equity = equity0 + np.cumsum(pnl, axis=1)
    peak = np.maximum.accumulate(equity, axis=1)
    drop = peak - equity
    dd = drop.max(axis=1)
    net = pnl.sum(axis=1)
    count = live.sum(axis=1)
    wins = np.where(pnl > 0, pnl, 0.0).sum(axis=1)
    loss = np.where(pnl < 0, -pnl, 0.0).sum(axis=1)
    mean = net / np.where(count > 0, count, 1)
    var = ((pnl ** 2).sum(axis=1) - count * mean ** 2) / np.where(count > 1, count - 1, 1)
    return {"net": net, "return_pct": net / equity0,
            "dd": dd, "dd_pct": (drop / peak).max(axis=1),
            "ret_dd": np.where(dd > 0, net / np.where(dd > 0, dd, 1.0), np.nan),
            "sharpe": mean / np.sqrt(np.maximum(var, 1e-30)),
            "pf": np.where(loss > 0, wins / np.where(loss > 0, loss, 1.0), np.nan),
            "losing_run": _losing_run(pnl, live), "trades": count.astype(float)}


def observed(pnl: np.ndarray, equity0: float) -> dict:
    """The same statistics for the one real backtest.

    Args:
        pnl: Net USD per real trade, in the order they happened.
        equity0: Starting account in USD.

    Returns:
        One number per statistic.
    """
    live = np.ones((1, pnl.size), dtype=bool)
    return {k: float(v[0]) for k, v in paths(pnl[None, :], live, equity0).items()}


def summarise(values: np.ndarray, seen: float, name: str, qs: list[float]) -> dict:
    """One simulated distribution reduced to the numbers the tables print.

    Args:
        values: One statistic, one entry per random run.
        seen: The real backtest's value of that statistic.
        name: Which statistic, to read its direction.
        qs: Percentiles to report.

    Returns:
        Each percentile, the mean, median and standard deviation, the raw percentile the real
        run sits at, the share of random runs it **outperforms**, and the one-sided p for that
        statistic's own good side. `beats` reads the direction so it always rises with a
        better strategy: on drawdown it counts the runs that suffered more, not the ones that
        scored higher. One is added to numerator and denominator of p so a run that beats
        every draw reports the resolution of the test rather than an impossible zero.
    """
    clean = values[np.isfinite(values)]
    better = HIGHER_IS_BETTER[name]
    beaten = np.sum(clean >= seen) if better else np.sum(clean <= seen)
    return {"p": {q: float(np.percentile(clean, q)) for q in qs},
            "mean": float(clean.mean()), "median": float(np.median(clean)),
            "std": float(clean.std(ddof=1)), "observed": float(seen),
            "rank": float(np.mean(clean <= seen)),
            "beats": float(np.mean(clean < seen) if better else np.mean(clean > seen)),
            "p_value": float((1 + beaten) / (1 + clean.size)), "n": int(clean.size)}


def shape(values: np.ndarray, seen: float, name: str, bins: int = 60) -> dict:
    """A distribution reduced to something a chart can draw.

    Args:
        values: One statistic, one entry per random run.
        seen: The real backtest's value.
        name: Which statistic, to read its direction.
        bins: Histogram bins.

    Returns:
        Bin counts and the range they cover, widened to include the real value so it is
        always on the axis, plus the median, the 2.5 and 97.5 percentiles the figure marks,
        and the share of random runs the real one outperforms. Kept instead of the raw draws: a strategy's draws are hundreds of megabytes
        and a histogram is a few hundred bytes.
    """
    clean = values[np.isfinite(values)]
    lo, hi = min(float(clean.min()), seen), max(float(clean.max()), seen)
    floor = max(abs(lo), abs(hi), 1.0) * 1e-9 * bins
    if hi - lo < floor:
        middle = (lo + hi) / 2
        lo, hi = middle - floor / 2, middle + floor / 2
    counts, edges = np.histogram(clean, bins=bins, range=(lo, hi))
    better = HIGHER_IS_BETTER[name]
    return {"counts": counts.tolist(), "lo": float(edges[0]), "hi": float(edges[-1]),
            "observed": float(seen), "median": float(np.median(clean)),
            "lo_ci": float(np.percentile(clean, 2.5)),
            "hi_ci": float(np.percentile(clean, 97.5)),
            "beats": float(np.mean(clean < seen) if better else np.mean(clean > seen)),
            "higher_is_better": bool(better)}


def table(stats: dict, seen: dict, qs: list[float]) -> dict:
    """Every statistic of one run, against what the real backtest did.

    Args:
        stats: One array per statistic, across the random runs.
        seen: The real backtest's statistics.
        qs: Percentiles to report.

    Returns:
        {statistic: what summarise() returned}.
    """
    return {k: summarise(v, seen[k], k, qs) for k, v in stats.items()}


def shapes(stats: dict, seen: dict) -> dict:
    """A drawable histogram of every statistic of one run.

    Args:
        stats: One array per statistic, across the random runs.
        seen: The real backtest's statistics.

    Returns:
        {statistic: what shape() returned}.
    """
    return {k: shape(v, seen[k], k) for k, v in stats.items()}
