"""The build score of a combination (Q10 a): signed ranks of four path metrics, shifted minimum."""

import numpy as np
import pandas as pd

from portfolio.common.construct import weights
from portfolio.common.construct.verdict import metrics

SHIFT_MINIMUM = ("metric",)      # owner 2026-10-05: the only reading (`real.shift_minimum`)


def masks(combos: np.ndarray, n: int) -> np.ndarray:
    """Padded int32 [P, K_max] member indices (-1 padding) -> bool [P, N] membership."""
    out = np.zeros((combos.shape[0], n), dtype=bool)
    rows, cols = np.nonzero(combos >= 0)
    out[rows, combos[rows, cols]] = True
    return out


def shifted(paths: np.ndarray, dates: pd.DatetimeIndex, cfg: dict) -> list[dict[str, np.ndarray]]:
    """`metrics.table` of daily P&L paths on a window with its start shifted 0..n months.

    A metric of one fixed window moves with where the window is cut (Faith: 10-15 % from a
    few months); the window is read from several starts (owner, 2026-10-05, R3).

    Args:
        paths: [P, D] daily P&L.
        dates: The D days.
        cfg: The construct config (`real.losing_year`, `real.shift_months`).

    Returns:
        One `metrics.table` dict (each [P]) per shift: [0] is the whole window, [m] the
        window that starts m calendar months later.
    """
    tables = []
    for months in range(cfg["real"]["shift_months"] + 1):
        first = dates.searchsorted(dates[0] + pd.DateOffset(months=months))
        tables.append(metrics.table(paths[:, first:], pd.DatetimeIndex(dates[first:]), cfg["real"]["losing_year"]))
    return tables


def measure(unit: np.ndarray, dates: pd.DatetimeIndex, members: np.ndarray,
            cfg: dict) -> list[dict[str, np.ndarray]]:
    """`shifted()` of each combination's path on build, the weights set once on the whole of it.

    Args:
        unit: [N, D] each member's daily P&L per unit of risk, 0 where it has no history.
        dates: The D build days.
        members: bool [P, N], at least one member per row.
        cfg: The construct config (`weights.method`, `real.losing_year`, `real.shift_months`).

    Returns:
        `shifted()`'s list for the P combinations.
    """
    return shifted(weights.matrix(pd.DataFrame(unit.T, index=dates), members, cfg) @ unit, dates, cfg)


def percentile(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Share of `reference` at or below each value, ties counted half."""
    ordered = np.sort(reference)
    return (np.searchsorted(ordered, values, "left")
            + np.searchsorted(ordered, values, "right")) / (2 * ordered.size)


def rank_score(table: dict[str, np.ndarray], reference: dict[str, np.ndarray]) -> np.ndarray:
    """The score: the mean over the four metrics of each one's signed rank in the reference.

    A rank needs a set to be a rank in. `reference` is that set, fixed for the whole run, so
    two combinations scored generations apart are comparable -- AlphaForge renormalised
    inside each generation and they were not.

    Args:
        table: `measure()` of the combinations to score.
        reference: `measure()` of the reference combinations.

    Returns:
        [P] in 0..1; 1 = best on every metric (P(losing year) ranked downwards).
    """
    parts = []
    for name in metrics.NAMES:
        pct = percentile(table[name], reference[name])
        parts.append(pct if metrics.SIGN[name] > 0 else 1.0 - pct)
    return np.mean(parts, axis=0)


def worst(tables: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    """Each ranked metric at its worst over the shifted windows; the Sharpe of the whole one.

    A window with no drawdown (NaN in R-cubed and gain-to-pain) is skipped, not read as worst.
    """
    out = {}
    for name in metrics.NAMES:
        pick = np.fmin if metrics.SIGN[name] > 0 else np.fmax
        out[name] = pick.reduce([t[name] for t in tables])
    return {**out, "sharpe": tables[0]["sharpe"]}


def score(tables: list[dict], reference: list[dict]) -> tuple[np.ndarray, dict]:
    """The shifted minimum of the rank score (owner, 2026-10-05, `real.shift_minimum: metric`).

    Each metric takes its worst value over the shifted windows and the ranks are taken once,
    on those.

    Args:
        tables: `measure()` of the combinations to score.
        reference: `measure()` of the reference combinations.

    Returns:
        The score [P], and the table it stands on: the worst metrics.
    """
    table = worst(tables)
    return rank_score(table, worst(reference)), table
