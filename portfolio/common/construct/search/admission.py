"""Admission of a candidate to a fixed base (Q16 c): pair filters against each member, and Sharpe."""

import numpy as np
import pandas as pd

INCREMENTS = ("finite", "marginal")


def _sharpe(path: np.ndarray) -> float:
    """Daily Sharpe, not annualised."""
    return float(path.mean() / path.std(ddof=1))


def increment(base: np.ndarray, candidate: np.ndarray, how: str) -> float:
    """What the candidate adds to the base's build Sharpe.

    Args:
        base: [K, D] the members' daily P&L per unit of risk on build.
        candidate: [D] the candidate's.
        how: "finite" -- the Sharpe of the K+1 at equal weight minus the Sharpe of the K;
            "marginal" -- the Euler derivative at zero weight, `SR_c - rho(c, base) * SR_base`,
            positive exactly when a small allocation to the candidate raises the Sharpe.

    Returns:
        The increment, in daily Sharpe.
    """
    book = base.mean(axis=0)
    if how == "finite":
        return _sharpe(np.vstack([base, candidate]).mean(axis=0)) - _sharpe(book)
    return _sharpe(candidate) - float(np.corrcoef(candidate, book)[0, 1]) * _sharpe(book)


def judge(unit: np.ndarray, graph: np.ndarray, base: np.ndarray, candidates: np.ndarray,
          how: str) -> pd.DataFrame:
    """Each candidate against the same fixed base; none is added, so the order does not matter.

    Args:
        unit: [N, D] every strategy's daily P&L per unit of risk on build, 0 outside history.
        graph: N x N bool admissible adjacency.
        base: The base portfolio's member indices.
        candidates: Indices to judge, none of them in the base.
        how: As `increment`.

    Returns:
        One row per candidate: `candidate`, `blocked_by` (base members it has no admissible
        pair with), `increment` (written here, on build, before any verdict reads a later
        stretch) and `enters` (no member blocks it and the increment is above 0).
    """
    rows = []
    for c in candidates:
        blocked = base[~graph[c, base]]
        gain = increment(unit[base], unit[c], how)
        rows.append({"candidate": int(c), "blocked_by": blocked.tolist(), "increment": gain,
                     "enters": blocked.size == 0 and gain > 0})
    return pd.DataFrame(rows)
