"""The haircut h: a path set with a fraction of its edge taken away, and the h at which the bank breaks even."""

import numpy as np


def edge(paths: dict[str, np.ndarray]) -> float:
    """The path set's edge: mean closed P&L over the days that closed any, unit risk."""
    closed = paths["closed"]
    if not closed.any():
        raise ValueError(
            "haircut.edge: no day of the path set closes any P&L — there is no edge to cut"
        )
    return float(closed.sum() / np.count_nonzero(closed))


def apply(paths: dict[str, np.ndarray], h: float) -> dict[str, np.ndarray]:
    """The same paths with `h` of the edge removed from every day that closed P&L.

    Args:
        paths: `closed`, `float_end`, `low`, `high`, `opened`, each [n_paths, horizon].
        h: Fraction of the edge taken away; 0 leaves the paths, 1 leaves none.

    Returns:
        A path set sharing every untouched array. The cut comes off `closed`; the day's `low` is
        lowered only where the new close falls below it (a day's worst equity cannot sit above
        its own end), and `high` stays, which keeps a trailing floor where it was.
    """
    if h == 0:
        return paths
    closed = paths["closed"] - h * edge(paths) * (paths["closed"] != 0)
    day_end = closed + np.diff(paths["float_end"], axis=1, prepend=0.0)
    return {**paths, "closed": closed, "low": np.minimum(paths["low"], day_end)}


def breakeven(hs: list[float], evs: list[float]) -> float | None:
    """The haircut at which the bank's EV crosses zero, read off the curve.

    Args:
        hs: Haircuts, ascending.
        evs: EV of the bank at each.

    Returns:
        The first crossing, linear between the two haircuts around it; `None` when the curve
        never crosses inside `hs` (the caller says which side it stays on).
    """
    for (h0, v0), (h1, v1) in zip(zip(hs, evs), zip(hs[1:], evs[1:])):
        if v0 > 0 >= v1:
            return float(h0 + (h1 - h0) * v0 / (v0 - v1))
    return None
