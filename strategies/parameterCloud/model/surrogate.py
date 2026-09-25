"""A3: a smooth model of the surface, its residual roughness, and its curvature."""

import numpy as np
from scipy.spatial import distance


def terms(unit: np.ndarray) -> np.ndarray:
    """The full second-order design matrix of a set of tuples.

    Args:
        unit: Rows by parameters, on [0, 1].

    Returns:
        Intercept, every linear term, every square and every pairwise product, in that
        order. Quadratic and not a Gaussian process on purpose: with k parameters it has
        1 + 2k + k(k-1)/2 coefficients against thousands of points, it needs no
        hyperparameter fitted to the same data it is judged on, and its Hessian is exact
        rather than estimated. What it cannot do is report prediction uncertainty.
    """
    n, k = unit.shape
    cross = [unit[:, i] * unit[:, j] for i in range(k) for j in range(i + 1, k)]
    return np.column_stack([np.ones(n), unit, unit ** 2] + cross)


def fit(unit: np.ndarray, y: np.ndarray) -> dict:
    """Least squares, and how much of the surface the smooth model failed to catch.

    Args:
        unit: Rows by parameters, on [0, 1].
        y: The metric, one per row.

    Returns:
        `coef`, `r2`, and `roughness` = 1 - r2, the share of the variance that is not a
        smooth function of the parameters at all. High roughness is the diagnosis the
        test exists for: a surface whose neighbouring tuples disagree is one where the
        chosen point's score is mostly the draw, not the parameters.
    """
    matrix = terms(unit)
    coef = np.linalg.lstsq(matrix, y, rcond=None)[0]
    resid = y - matrix @ coef
    r2 = 1.0 - float(resid.var() / y.var())
    return {"coef": coef, "k": unit.shape[1], "n": int(y.size), "r2": r2,
            "roughness": 1.0 - r2, "rmse": float(np.sqrt((resid ** 2).mean()))}


def predict(model: dict, unit: np.ndarray) -> np.ndarray:
    """The smooth model's value at any set of tuples.

    Args:
        model: What `fit` returned.
        unit: Rows by parameters, on [0, 1].

    Returns:
        One prediction per row.
    """
    return terms(unit) @ model["coef"]


def curvature(model: dict, point: np.ndarray) -> dict:
    """The gradient and the Hessian of the smooth model at one point.

    Args:
        model: What `fit` returned.
        point: One tuple on [0, 1], the origin's.

    Returns:
        `slope` the gradient's norm, `eigenvalues` of the Hessian sorted ascending, and
        `sharpest` the most negative one. All in metric units per unit of the parameter's
        own explored range, so the eigenvalues compare across parameters.

        A quadratic has **one** Hessian everywhere, so fitting the whole cloud gives the
        shape of the bowl and fitting only the neighbourhood gives the shape at theta-zero.
        A slope far from zero says the smooth optimum is not where the strategy sits.
    """
    k, coef = model["k"], model["coef"]
    hess = np.diag(2 * coef[1 + k:1 + 2 * k])
    pairs = [(i, j) for i in range(k) for j in range(i + 1, k)]
    for (i, j), value in zip(pairs, coef[1 + 2 * k:]):
        hess[i, j] = hess[j, i] = value
    grad = coef[1:1 + k] + hess @ point
    values = np.sort(np.linalg.eigvalsh(hess))
    return {"slope": float(np.linalg.norm(grad)), "eigenvalues": values,
            "sharpest": float(values[0]), "flattest": float(values[-1])}


def local_roughness(unit: np.ndarray, y: np.ndarray, neighbours: int) -> float:
    """How much neighbouring tuples disagree, without assuming any model.

    Args:
        unit: Rows by parameters, on [0, 1].
        y: The metric, one per row.
        neighbours: How many nearest tuples each point is compared against.

    Returns:
        The median gap between a tuple and the median of its nearest neighbours, in IQRs
        of the metric. It answers the same question as `roughness` without a functional
        form: a quadratic calls everything it cannot represent noise, including a real
        ridge, and this does not.
    """
    order = np.argsort(distance.squareform(distance.pdist(unit)), axis=1)[:, 1:neighbours + 1]
    gap = np.abs(y - np.median(y[order], axis=1))
    return float(np.median(gap) / (np.quantile(y, 0.75) - np.quantile(y, 0.25)))
