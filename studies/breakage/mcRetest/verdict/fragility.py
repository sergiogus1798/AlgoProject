"""Question 1 — how much does it hurt? The tail, how well it is known, and the fall behind it."""

import numpy as np
from scipy import stats


def tail(values: np.ndarray, quantile: float, cfg: dict) -> dict:
    """One tail quantile with an exact interval around it.

    Args:
        values: One value per simulation, of any metric.
        quantile: Percent, e.g. 5 for the 5th percentile.
        cfg: What inputs.config.load() returned.

    Returns:
        The point and the two order statistics that bracket it at the configured
        confidence. The count of sample points below the true quantile is binomial, so its
        bounds give the ranks directly: nothing is resampled, the coverage is exact rather
        than asymptotic, and it cannot fail.

        **This deliberately does not use BCa, which the first draft did.** BCa is built for
        a smooth statistic; a quantile is an order statistic, and its bootstrap replicates
        are heavily tied because they can only ever land on a handful of neighbouring
        sample values. The bias-correction term then reads a replicate fraction of 0 or 1,
        z0 goes infinite and the interval comes back NaN -- measured on 5 of the 8 tasks
        here at the 5th percentile, not merely in the far tail where it was expected.
        `bootstrap_mean` below keeps BCa for the statistics it actually suits.
    """
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    n, q = ordered.size, quantile / 100.0
    alpha = 1 - cfg["fragility"]["confidence"]
    clamp = (lambda i: ordered[max(0, min(n - 1, int(i)))])
    return {"point": float(np.percentile(ordered, quantile)),
            "lo": float(clamp(stats.binom.ppf(alpha / 2, n, q))),
            "hi": float(clamp(stats.binom.ppf(1 - alpha / 2, n, q))),
            "method": "order statistics"}


def bootstrap_mean(values: np.ndarray, cfg: dict) -> dict:
    """A BCa interval for a smooth statistic, where BCa belongs.

    Args:
        values: One value per simulation.
        cfg: What inputs.config.load() returned.

    Returns:
        The mean and its bias-corrected accelerated interval. Used for means and Sharpe
        analogues, never for a quantile -- see tail().
    """
    got = stats.bootstrap((np.asarray(values, dtype=np.float64),), np.mean, method="BCa",
                          vectorized=True, n_resamples=cfg["fragility"]["n_resamples"],
                          confidence_level=cfg["fragility"]["confidence"])
    return {"point": float(np.mean(values)), "lo": float(got.confidence_interval.low),
            "hi": float(got.confidence_interval.high), "method": "BCa"}


def conditional_drawdown(values: np.ndarray, cfg: dict) -> dict:
    """The average of the worst drawdowns, not merely the edge of them.

    Args:
        values: DrawdownPct of every simulation.
        cfg: What inputs.config.load() returned.

    Returns:
        The conditional mean of the worst `cvar_alpha` share, the plain quantile beside it,
        and how much deeper the tail runs than its own edge. This is the number the gate
        reads: it is coherent, it is subadditive, and unlike a percentile it moves when the
        tail is heavy or has two modes -- which is exactly when a percentile stops meaning
        what it appears to mean.
    """
    alpha = cfg["fragility"]["cvar_alpha"]
    edge = float(np.quantile(values, 1 - alpha))
    beyond = values[values >= edge]
    return {"cvar": float(beyond.mean()), "quantile": edge,
            "excess": float(beyond.mean() - edge), "n_tail": int(beyond.size)}


def underwater(pnl: np.ndarray, offsets: np.ndarray) -> np.ndarray:
    """What share of its trades each simulation spent below its own equity high.

    Args:
        pnl: Every simulation's P/L concatenated, USD.
        offsets: Where each simulation starts, length sims + 1.

    Returns:
        A fraction per simulation. **Trades, never time** -- a simulation file carries no
        dates, so there is no such thing as days under water here, and using the word would
        guarantee someone eventually reports one number as the other.
    """
    out = np.empty(offsets.size - 1)
    for k, (start, stop) in enumerate(zip(offsets[:-1], offsets[1:])):
        equity = np.cumsum(pnl[start:stop])
        out[k] = float(np.mean(equity < np.maximum.accumulate(equity)))
    return out


def fan(pnl: np.ndarray, offsets: np.ndarray, cfg: dict) -> dict:
    """The envelope every simulated equity curve ran inside, and a sample of the curves themselves.

    Args:
        pnl: Every simulation's P/L concatenated, USD.
        offsets: Where each simulation starts, length sims + 1.
        cfg: What inputs.config.load() returned.

    Returns:
        The configured percentiles of equity at each point of normalised progress, plus
        `sample`: up to `fragility.fan_sample` individual curves, on the same grid. The
        x-axis is progress from 0 to 1 and **not the trade index**: simulations differ in
        length -- 676 to 2,031 measured -- so there is no common trade number to align them
        on, and interpolating each curve onto a shared grid is the only honest way to stack
        them. The sample is spread evenly across simulations **ordered by their own final
        equity** (2026-09-30, feedback §6: "enough to see the distribution") rather than
        left in simulation order, so a thin sample still shows the full spread from the worst
        run to the best one instead of whatever 100 happened to be drawn first.
    """
    points = cfg["fragility"]["fan_points"]
    grid = np.linspace(0.0, 1.0, points)
    curves = np.empty((offsets.size - 1, points))
    for k, (start, stop) in enumerate(zip(offsets[:-1], offsets[1:])):
        equity = np.cumsum(pnl[start:stop])
        curves[k] = np.interp(grid, np.linspace(0.0, 1.0, equity.size), equity)
    order = np.argsort(curves[:, -1])
    take = min(cfg["fragility"]["fan_sample"], len(order))
    keep = order[np.linspace(0, len(order) - 1, take).astype(int)]
    return {"progress": grid,
            "bands": {level: np.percentile(curves, level, axis=0)
                      for level in cfg["fragility"]["band_levels"]},
            "sample": curves[keep]}


def describe(metrics: dict, pnl: np.ndarray, offsets: np.ndarray, cfg: dict) -> dict:
    """Everything question 1 asks of one strategy under one task.

    Args:
        metrics: The reconstructed metrics of that task, one array per name.
        pnl: That task's P/L, concatenated, USD.
        offsets: Where each simulation starts.
        cfg: What inputs.config.load() returned.

    Returns:
        The 5th percentile of net profit with its interval, the same for profit factor, the
        conditional drawdown, and how long a simulation typically spent under water.
    """
    return {"net_p5": tail(metrics["NetProfit"], 5.0, cfg),
            "pf_p5": tail(metrics["ProfitFactor"], 5.0, cfg),
            "drawdown": conditional_drawdown(metrics["DrawdownPct"], cfg),
            "underwater_median": float(np.median(underwater(pnl, offsets))),
            "positive_share": float(np.mean(metrics["NetProfit"] > 0))}
