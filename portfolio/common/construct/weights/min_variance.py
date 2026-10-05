"""Minimum variance, long only, on a Ledoit-Wolf shrunk covariance (AlphaForge's had no shrinkage)."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def shrunk(x: np.ndarray) -> tuple[np.ndarray, float]:
    """Ledoit and Wolf's (2004) covariance: the sample one pulled towards a scaled identity.

    Args:
        x: [days, K] daily P&L.

    Returns:
        The [K, K] covariance and the shrinkage intensity in [0, 1] the data asked for.
    """
    n, k = x.shape
    x = x - x.mean(axis=0)
    sample = x.T @ x / n
    mu = np.trace(sample) / k
    delta = ((sample - mu * np.eye(k)) ** 2).sum() / k
    beta = min((((x ** 2).T @ (x ** 2)).sum() / n - (sample ** 2).sum()) / (n * k), delta)
    intensity = 0.0 if delta == 0 else float(beta / delta)
    return (1 - intensity) * sample + intensity * mu * np.eye(k), intensity


def solve(cov: np.ndarray) -> np.ndarray:
    """The non-negative weights summing to 1 of least variance under `cov`.

    Raises:
        ValueError: The optimiser did not converge; no other method is substituted
            (AlphaForge fell back to risk parity in silence).
    """
    k = len(cov)
    scaled = cov / np.trace(cov) * k
    got = minimize(lambda w: w @ scaled @ w, np.full(k, 1 / k), jac=lambda w: 2 * scaled @ w,
                   method="SLSQP", bounds=[(0.0, 1.0)] * k, options={"ftol": 1e-12, "maxiter": 500},
                   constraints={"type": "eq", "fun": lambda w: w.sum() - 1, "jac": lambda w: np.ones(k)})
    if not got.success:
        raise ValueError(f"mínima varianza no converge: {got.message}")
    w = np.clip(got.x, 0.0, None)
    return w / w.sum()


def weights(build_daily: pd.DataFrame, cfg: dict) -> dict:
    """Least-variance weights; estimates the whole covariance, shrunk, and no mean.

    Args:
        build_daily: estimation days x the combination's members, P&L per unit of risk.
        cfg: The construct config (unused: the shrinkage intensity is the data's).

    Returns:
        Column label -> weight.

    Raises:
        ValueError: No member varies on the estimation days, or the optimiser fails.
    """
    if build_daily.shape[1] == 1:
        return {build_daily.columns[0]: 1.0}
    cov, _ = shrunk(build_daily.to_numpy(dtype=float))
    if not np.trace(cov) > 0:
        raise ValueError("sin varianza en los días de estimación")
    return dict(zip(build_daily.columns, solve(cov).tolist()))
