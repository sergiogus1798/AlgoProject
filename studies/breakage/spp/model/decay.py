"""The criteria metrics of an SPP: the original against its own grid, and IS against OOS1 as two unpaired samples."""

from typing import TypedDict, cast

import numpy as np
import pandas as pd
from scipy.stats import norm, wasserstein_distance

from studies.breakage.spp.model import combine


class Distance(TypedDict):
    """One metric's gap between the original and its grid: percent, IQRs, and the grid's own 5-95 band."""

    rel: float | None
    iqr: float
    null: list[float]


class Compared(TypedDict):
    """One time-free metric, IS against OOS1: ratio of medians, effect size, distance, zero-edge null."""

    ratio: float | None
    a: float
    w: float
    null: dict[str, list[float] | None] | None


class Measured(TypedDict):
    """`measure`: per metric the original's distance on each side, and the IS-OOS1 comparison."""

    original: dict[str, dict[str, Distance]]
    decay: dict[str, Compared]


LEVELS = (5, 25, 50, 75, 95)
# The path noise of a whole grid is swept at these quantiles of a standard normal.
Z = norm.ppf(np.arange(0.5, 100.0) / 100.0)


def distance(values: np.ndarray, original: float, floor: float) -> Distance:
    """How far the original backtest sits from the median of its own permutations.

    Args:
        values: One metric over the grid, the original left out.
        original: The same metric of the original backtest.
        floor: `rel` is published only when |median| is at least this many IQRs: a median
            near zero turns a share of it into an explosion.

    Returns:
        `rel` — (original − median) / |median| in percent, signed, None under the floor;
        `iqr` — the same gap in IQRs of the grid; `null` — the 5th and 95th percentile of
        that IQR distance over the grid's own members: what a backtest drawn at random from
        the grid reads.
    """
    q1, median, q3 = np.percentile(values, [25, 50, 75])
    spread = q3 - q1
    lo, hi = (np.percentile(values, [5, 95]) - median) / spread
    return {
        "rel": float(100 * (original - median) / abs(median))
        if abs(median) >= floor * spread
        else None,
        "iqr": float((original - median) / spread),
        "null": [float(lo), float(hi)],
    }


def superiority(a: np.ndarray, b: np.ndarray) -> float:
    """Vargha–Delaney A of `b` over `a`: P(b > a) + ½·P(b = a), an effect size, never a p."""
    a = np.sort(a)
    below, upto = np.searchsorted(a, b, "left"), np.searchsorted(a, b, "right")
    return float((below + upto).mean() / (2 * a.size))


def wasserstein(a: np.ndarray, b: np.ndarray) -> float:
    """W₁(a, b) in IQRs of `a`: how far one distribution must be moved onto the other. Two-sided."""
    q1, q3 = np.percentile(a, [25, 75])
    return float(wasserstein_distance(a, b) / (q3 - q1))


def ratio(a: np.ndarray, b: np.ndarray, floor: float) -> float | None:
    """median(b) / median(a) — a ratio of medians, the only one two unpaired samples allow.

    Returns:
        None when median(a) is not above `floor`: there is nothing to decay from, and the
        ratio flips sign or explodes.
    """
    base = float(np.median(a))
    return float(np.median(b)) / base if base > floor else None


def profit_factor(k: np.ndarray) -> np.ndarray:
    """The Profit Factor of normal per-trade returns whose mean is `k` standard deviations."""
    return (norm.pdf(k) + k * norm.cdf(k)) / (norm.pdf(k) - k * norm.cdf(-k))


def compare(
    a: np.ndarray, b: np.ndarray, floor: float, moved: list[np.ndarray] | None
) -> Compared:
    """IS against OOS1 on one time-free metric, and the same three numbers under a zero-edge OOS1.

    Args:
        a, b: The IS and the OOS1 grid of that metric, finite, the original left out.
        floor: `ratio`'s IS floor for this metric.
        moved: The OOS1 grid as a zero-edge family would have left it, one array per
            quantile of its path noise (`zero_edge`); None for a metric with no such model.

    Returns:
        `ratio`, `a`, `w` — the real values — and `null`: per name the `LEVELS` percentiles
        over `moved`, None without a model (and for a ratio under its floor).
    """
    out: Compared = {
        "ratio": ratio(a, b, floor),
        "a": superiority(a, b),
        "w": wasserstein(a, b),
        "null": None,
    }
    if moved is None:
        return out
    draws = {
        "ratio": [ratio(a, m, floor) for m in moved]
        if out["ratio"] is not None
        else None,
        "a": [superiority(a, m) for m in moved],
        "w": [wasserstein(a, m) for m in moved],
    }
    out["null"] = {
        k: None if v is None else [float(x) for x in np.percentile(v, LEVELS)]
        for k, v in draws.items()
    }
    return out


def zero_edge(oos: pd.DataFrame, years: float) -> dict[str, list[np.ndarray]]:
    """The OOS1 grid of each metric that has a noise model, as a zero-edge family would read.

    Every permutation trades the same price path, so that path's luck moves the whole grid
    at once: the grid keeps its shape and its centre is drawn. An annualised Sharpe of zero
    read over `years` years has a standard error of 1/√years (an upper bound: permutations
    correlated below 1 move less); Sortino the same in units of the grid's own Sortino/Sharpe
    spread; a Profit Factor is that of a per-trade mean drawn from N(0, 1/median trades).
    R/Edge ratio has no model, hence no null.

    Args:
        oos: The OOS1 grid, the original left out.
        years: Length of the OOS1 window.

    Returns:
        Column → one moved grid per quantile of `Z`.
    """

    def iqr(col: str) -> float:
        """Interquartile range of one column."""
        q1, q3 = np.nanpercentile(oos[col].to_numpy(float), [25, 75])
        return float(q3 - q1)

    out = {}
    for col, centres in (
        ("SharpeRatio", Z / np.sqrt(years)),
        ("SortinoRatio", Z / np.sqrt(years) * iqr("SortinoRatio") / iqr("SharpeRatio")),
        ("ProfitFactor", profit_factor(Z / np.sqrt(oos["NumberOfTrades"].median()))),
    ):
        b = oos[col].to_numpy(float)
        b, median = b[np.isfinite(b)], float(np.nanmedian(b))
        out[col] = [
            b * c / median if col == "ProfitFactor" else b - median + c for c in centres
        ]
    return out


def measure(
    is_pop: pd.DataFrame,
    oos_pop: pd.DataFrame | None,
    is_real: pd.Series,
    oos_real: pd.Series | None,
    cfg: dict,
) -> Measured:
    """Every criteria metric of one strategy's SPP.

    Args:
        is_pop, oos_pop: `export.without_original()` grids; `oos_pop` None with no OOS1 export.
        is_real, oos_real: Each window's permutation -1 row.
        cfg: `config.yaml: criteria` — `median_floor_iqr` and `is_floor` per metric.

    Returns:
        `original` — column → {"IS": `distance`, "OOS1": `distance`} over panel 1's metrics;
        `decay` — column → `compare` over the time-free metrics, {} without an OOS1 export.
    """
    sides = [("IS", is_pop, is_real)] + (
        [("OOS1", oos_pop, cast(pd.Series, oos_real))] if oos_pop is not None else []
    )
    original = {
        col: {
            side: distance(
                pop[col].to_numpy(float)[np.isfinite(pop[col].to_numpy(float))],
                float(real[col]),
                cfg["median_floor_iqr"],
            )
            for side, pop, real in sides
        }
        for col, _, _ in combine.METRICS
    }
    decay = {}
    if oos_pop is not None:
        moved = zero_edge(oos_pop, float(cast(pd.Series, oos_real)["TotalDataYears"]))
        for col, _, _ in combine.TIME_FREE:
            if col in is_pop.columns and col in oos_pop.columns:
                a, b = is_pop[col].to_numpy(float), oos_pop[col].to_numpy(float)
                decay[col] = compare(
                    a[np.isfinite(a)],
                    b[np.isfinite(b)],
                    cfg["is_floor"][col],
                    moved.get(col),
                )
    return {"original": original, "decay": decay}
