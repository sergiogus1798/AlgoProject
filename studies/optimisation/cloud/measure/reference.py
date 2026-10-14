"""Whether the surface says anything: its adjusted R² against the same fit on a shuffled metric."""

from typing import TypedDict, cast

import numpy as np

from studies.optimisation.cloud.model import surrogate


def shuffled(unit: np.ndarray, y: np.ndarray, draws: int, seed: int) -> np.ndarray:
    """The adjusted R² the surface reaches when the metric is dealt to the variants at random.

    Args:
        unit: Rows by parameters, on [0, 1].
        y: The metric, one per row.
        draws: How many shuffles.
        seed: Of the shuffles.

    Returns:
        One adjusted R² per shuffle: what this many coefficients explain of this many points
        when the parameters explain nothing. It keeps the metric's own distribution, tails
        included, so nothing about its shape is assumed.
    """
    rng = np.random.default_rng(seed)
    dealt = np.column_stack([rng.permutation(y) for _ in range(draws)])
    return cast(np.ndarray, surrogate.solve(surrogate.terms(unit), dealt)[1])


class Legible(TypedDict):
    """The surface's adjusted R², the reference's percentile it must beat, and whether it does."""

    r2_adj: float
    r2_ref: float
    legible: bool


def legible(r2_adj: float, reference: np.ndarray, percentile: float) -> Legible:
    """The surface's adjusted R² beside its shuffled reference.

    Args:
        r2_adj: Of the real fit.
        reference: What `shuffled` returned.
        percentile: Of the reference the fit must beat, 0-100.

    Returns:
        `r2_adj`, `r2_ref` (that percentile of the reference) and `legible`: True only above
        it, so a cloud of pure noise is called legible about (100 - percentile) % of the time.
    """
    bar = float(np.percentile(reference, percentile))
    return {"r2_adj": r2_adj, "r2_ref": bar, "legible": bool(r2_adj > bar)}
