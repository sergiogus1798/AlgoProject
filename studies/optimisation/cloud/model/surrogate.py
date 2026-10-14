"""The smooth model of the surface: a full quadratic over the live parameters, and how much it explains."""

from typing import TypedDict

import numpy as np


def coefficients(k: int) -> int:
    """How many coefficients the quadratic has over `k` parameters: 1 + 2k + k(k-1)/2."""
    return 1 + 2 * k + k * (k - 1) // 2


def terms(unit: np.ndarray) -> np.ndarray:
    """The full second-order design matrix of a set of tuples.

    Args:
        unit: Rows by parameters, on [0, 1].

    Returns:
        Intercept, every linear term, every square and every pairwise product, in that
        order. Quadratic and not a Gaussian process on purpose: it needs no hyperparameter
        fitted to the same data it is judged on.
    """
    n, k = unit.shape
    cross = [unit[:, i] * unit[:, j] for i in range(k) for j in range(i + 1, k)]
    return np.column_stack([np.ones(n), unit, unit**2] + cross)


def solve(matrix: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray | float]:
    """Least squares and the adjusted R² of the fit, for one metric or for many at once.

    Args:
        matrix: What `terms` returned.
        y: The metric, one per row — or rows by draws, each column fitted on its own.

    Returns:
        (the coefficients, the adjusted R²: one per column of `y`). The degrees of freedom
        are the matrix's rank, not its width: a parameter with two values makes its square a
        copy of itself, and counting both would charge the fit a coefficient it does not have.
    """
    coef, _, rank, _ = np.linalg.lstsq(matrix, y, rcond=None)
    n = len(y)
    r2 = 1.0 - (y - matrix @ coef).var(axis=0) / y.var(axis=0)
    return coef, 1.0 - (1.0 - r2) * (n - 1) / (n - rank)


class Fit(TypedDict):
    """A fitted smooth surface: its coefficients, parameter count, points and adjusted R²."""

    coef: np.ndarray
    k: int
    n: int
    r2_adj: float


def fit(unit: np.ndarray, y: np.ndarray) -> Fit:
    """The surface fitted to one metric.

    Args:
        unit: Rows by parameters, on [0, 1].
        y: The metric, one per row.

    Returns:
        `coef`, `k`, `n` and `r2_adj`, the share of the metric's variance that is a smooth
        function of the parameters, charged for the coefficients spent on it.
    """
    coef, r2_adj = solve(terms(unit), y)
    return {"coef": coef, "k": unit.shape[1], "n": int(y.size), "r2_adj": float(r2_adj)}


def predict(model: Fit, unit: np.ndarray) -> np.ndarray:
    """The smooth model's value at any set of tuples.

    Args:
        model: What `fit` returned.
        unit: Rows by parameters, on [0, 1].

    Returns:
        One prediction per row.
    """
    return terms(unit) @ model["coef"]
