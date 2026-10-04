"""The build score of a combination (Q10 a): equal-weight signed ranks of four path metrics."""

import numpy as np
import pandas as pd

from portfolio.common.construct.verdict import metrics


def masks(combos: np.ndarray, n: int) -> np.ndarray:
    """Padded int32 [P, K_max] member indices (-1 padding) -> bool [P, N] membership."""
    out = np.zeros((combos.shape[0], n), dtype=bool)
    rows, cols = np.nonzero(combos >= 0)
    out[rows, combos[rows, cols]] = True
    return out


def measure(unit: np.ndarray, dates: pd.DatetimeIndex, members: np.ndarray,
            losing_year: str) -> dict[str, np.ndarray]:
    """`metrics.table` of each equal-weighted combination: the mean of its members' paths.

    Args:
        unit: [N, D] each member's daily P&L per unit of risk, 0 where it has no history.
        dates: The D build days.
        members: bool [P, N], at least one member per row.
        losing_year: As `metrics.table`.

    Returns:
        `metrics.table`'s dict, each [P].
    """
    weights = members / members.sum(axis=1, keepdims=True)
    return metrics.table(weights @ unit, dates, losing_year)


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
