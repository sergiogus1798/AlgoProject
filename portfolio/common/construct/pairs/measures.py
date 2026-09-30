"""Pairwise correlation measures on aligned P&L series, signed, pairwise-finite."""

from typing import Callable

import numpy as np
from scipy.stats import pearsonr, spearmanr

MIN_FINITE = 3


def _aligned(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rows where both series are finite."""
    mask = np.isfinite(a) & np.isfinite(b)
    return a[mask], b[mask]


def overlap(a: np.ndarray, b: np.ndarray) -> int:
    """Count of rows where both series are finite."""
    return int((np.isfinite(a) & np.isfinite(b)).sum())


def pearson(a: np.ndarray, b: np.ndarray, cfg: dict) -> float:
    """Signed Pearson correlation on the rows where both are finite.

    Args:
        a, b: Aligned P&L series (monthly or daily), NaN where outside history.
        cfg: Unused; kept for the shared MEASURES signature.

    Returns:
        NaN below MIN_FINITE overlapping rows.
    """
    a2, b2 = _aligned(a, b)
    if a2.size < MIN_FINITE:
        return float("nan")
    return float(pearsonr(a2, b2)[0])


def spearman(a: np.ndarray, b: np.ndarray, cfg: dict) -> float:
    """Signed Spearman correlation on the rows where both are finite."""
    a2, b2 = _aligned(a, b)
    if a2.size < MIN_FINITE:
        return float("nan")
    return float(spearmanr(a2, b2)[0])


def co_loss(a: np.ndarray, b: np.ndarray, cfg: dict) -> float:
    """Share of overlapping rows where both series lose (< 0)."""
    a2, b2 = _aligned(a, b)
    if a2.size < MIN_FINITE:
        return float("nan")
    return float(((a2 < 0) & (b2 < 0)).sum() / a2.size)


def tail(a: np.ndarray, b: np.ndarray, cfg: dict) -> float:
    """Pearson on the rows where either series is at or below its own tail quantile.

    Args:
        a, b: Aligned P&L series.
        cfg: `tail_quantile`, e.g. 0.30.

    Returns:
        NaN below MIN_FINITE tail rows.
    """
    a2, b2 = _aligned(a, b)
    if a2.size < MIN_FINITE:
        return float("nan")
    q = cfg["tail_quantile"]
    tail_mask = (a2 <= np.quantile(a2, q)) | (b2 <= np.quantile(b2, q))
    if tail_mask.sum() < MIN_FINITE:
        return float("nan")
    return float(pearsonr(a2[tail_mask], b2[tail_mask])[0])


MEASURES: dict[str, Callable[[np.ndarray, np.ndarray, dict], float]] = {
    "pearson": pearson,
    "spearman": spearman,
    "co_loss": co_loss,
    "tail": tail,
}
