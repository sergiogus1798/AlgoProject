"""Stress-day selection, stress-day correlation, and effective N of a candidate set."""

import numpy as np
import pandas as pd

from .measures import pearson


def stress_days(build_daily: pd.DataFrame, quantile: float) -> pd.DatetimeIndex:
    """The worst `quantile` share of days of the equal-weighted pool.

    Args:
        build_daily: One column per member, daily P&L, NaN where a member has no history yet.
        quantile: e.g. 0.05 for the worst 5 %.

    Returns:
        The days at or below that quantile of the row-mean over the members available that day.
    """
    pool = build_daily.mean(axis=1, skipna=True)
    threshold = pool.quantile(quantile)
    return pool.index[pool <= threshold]


def stress_corr(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float:
    """Pearson correlation restricted to the rows `mask` selects (the stress days)."""
    a, b = np.asarray(a), np.asarray(b)
    return pearson(a[mask], b[mask], {})


def effective_n(corr: np.ndarray) -> dict:
    """Effective number of independent bets in a correlation matrix, both formulas.

    Args:
        corr: Symmetric KxK correlation matrix.

    Returns:
        `participation`: (Sigma lambda)^2 / Sigma lambda^2 of its eigenvalues.
        `average`: K / (1 + (K-1) * mean off-diagonal rho).
    """
    k = corr.shape[0]
    eigvals = np.linalg.eigvalsh(corr)
    participation = float(eigvals.sum() ** 2 / (eigvals**2).sum())
    off_diag = corr[~np.eye(k, dtype=bool)]
    average = float(k / (1 + (k - 1) * off_diag.mean()))
    return {"participation": participation, "average": average}
