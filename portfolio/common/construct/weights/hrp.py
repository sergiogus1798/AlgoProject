"""Hierarchical risk parity (López de Prado), with AlphaForge's label bug fixed."""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


def _cluster_variance(cov: np.ndarray, items: list[int]) -> float:
    """Variance of a cluster held at inverse-variance weights."""
    sub = cov[np.ix_(items, items)]
    w = 1.0 / np.diag(sub)
    w /= w.sum()
    return float(w @ sub @ w)


def weights(build_daily: pd.DataFrame, cfg: dict) -> dict[str, float]:
    """Ward tree on the correlation distance, then recursive bisection by cluster variance.

    Holds nothing fixed; estimates the covariance (unshrunk) and inverts none of it. Each
    weight is written at its member's own column: AlphaForge wrote it at the member's
    position in the tree's order and read it back in the original one.

    Args:
        build_daily: estimation days x the combination's members, P&L per unit of risk.
        cfg: The construct config (unused: the method has no knob).

    Returns:
        Column label -> weight.

    Raises:
        ValueError: A member does not vary on the estimation days.
    """
    k = build_daily.shape[1]
    if k == 1:
        return {str(build_daily.columns[0]): 1.0}
    cov = np.cov(build_daily.to_numpy(dtype=float), rowvar=False)
    sigma = np.sqrt(np.diag(cov))
    if not (sigma > 0).all():
        flat = [str(c)[:12] for c, s in zip(build_daily.columns, sigma) if not s > 0]
        raise ValueError(f"sin volatilidad en los días de estimación: {flat}")
    distance = np.sqrt(np.clip((1 - cov / np.outer(sigma, sigma)) / 2, 0.0, None))
    np.fill_diagonal(distance, 0.0)
    order = (
        [0, 1]
        if k == 2
        else leaves_list(linkage(squareform(distance, checks=False), "ward")).tolist()
    )
    out = np.ones(k)  # indexed by COLUMN, never by tree position
    clusters = [order]
    while clusters:
        items = clusters.pop()
        if len(items) < 2:
            continue
        left, right = items[: len(items) // 2], items[len(items) // 2 :]
        v_left, v_right = _cluster_variance(cov, left), _cluster_variance(cov, right)
        share = 1 - v_left / (v_left + v_right)
        out[left] *= share
        out[right] *= 1 - share
        clusters += [left, right]
    return dict(zip(build_daily.columns, out.tolist()))
