"""A1: where the chosen point sits among the tuples that surround it."""

import numpy as np

from core.surface import plateau


def near(step_matrix: np.ndarray, origin_row: int, radius: int) -> np.ndarray:
    """Which tuples count as the origin's neighbourhood.

    Args:
        step_matrix: What `space.steps` returned.
        origin_row: Row index of theta-zero.
        radius: How many level steps away a tuple may sit, on every parameter at once.

    Returns:
        A boolean mask, the origin included. The distance is Chebyshev in level steps: a
        tuple qualifies only if **no** parameter moved further than `radius`, so the
        neighbourhood is a box around theta-zero and not a shell of far-away tuples that
        happen to average close.
    """
    return (np.abs(step_matrix - step_matrix[origin_row]) <= radius).all(axis=1)


def reading(values: np.ndarray, mask: np.ndarray, origin_row: int,
            delta: float) -> dict:
    """The three A1 numbers, over one neighbourhood and over the whole cloud.

    Args:
        values: The metric, one per row.
        mask: What `near` returned.
        origin_row: Row index of theta-zero.
        delta: Relative shortfall still counted as company, for the plateau fraction.

    Returns:
        `n`, the rank `q`, the plateau fraction `pi` and the shrunk expectation, for the
        neighbourhood and for the cloud entire. Read together: a rank near 1 is only
        alarming when `pi` is small, which is the shape of a point picked off a noise
        peak rather than one sitting on a plateau.
    """
    reference = float(values[origin_row])
    out = {"original": reference, "delta": delta}
    for name, subset in (("near", values[mask]), ("cloud", values)):
        out[name] = {"n": int(subset.size), "q": plateau.rank_of(subset, reference),
                     "pi": plateau.plateau_fraction(subset, reference, delta),
                     "shrunk": plateau.shrunk(subset)}
    return out
