"""The ways a person picks one parameter set off a surface, behind one signature."""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

NEIGHBOUR = 1        # level steps in each parameter that still counts as next door

# One entry: the grid the neighbourhoods were built for, held so its id cannot be recycled
# under the key. Every partition and every bootstrap draw of a batch smooths over the same
# grid, and building the tree was 77% of the CSCV (🔬 2026-09-25, 26.6 s of 34.6).
_SMOOTHER: dict = {}


def coordinates(grid: pd.DataFrame) -> np.ndarray:
    """Each variant's position on the grid, counted in levels rather than in units.

    Args:
        grid: One row per variant in the panel's column order, the `param_` columns of
            contract C2.

    Returns:
        An integer array, variants down and parameters across. A parameter's levels are
        the distinct values the design actually fabricated, so "one step away" means the
        next point that exists rather than the next point somebody planned -- the
        coverage stratum varies parameters the brief pinned, and its values land between
        the brief's own levels.
    """
    return np.column_stack([pd.factorize(grid[c].to_numpy(), sort=True)[0]
                            for c in grid.columns])


def argmax(score: np.ndarray, grid: pd.DataFrame, rng: np.random.Generator) -> int:
    """Take the single best-scoring parameter set.

    Args:
        score: One in-sample score per variant.
        grid: Unused; the signature is shared so the rules are interchangeable.
        rng: Unused.

    Returns:
        Position of the maximum. This is what optimising means to most people, and it is
        the rule the CSCV was written to indict: the best point of a surface is the point
        most likely to be there by luck.
    """
    return int(np.argmax(score))


def plateau_centre(score: np.ndarray, grid: pd.DataFrame,
                   rng: np.random.Generator) -> int:
    """Take the best point of the surface after smoothing it over its neighbours.

    Args:
        score: One in-sample score per variant.
        grid: The `param_` columns, in the panel's column order.
        rng: Unused.

    Returns:
        Position of the variant whose own score and its immediate neighbours' average
        highest. A spike one step wide scores like its surroundings here and a broad
        plateau keeps its value, which is the whole difference between a parameter set
        that survives and one that was a coincidence.
    """
    sums, count = smoother(grid)
    return int(np.argmax(sums @ score / count))


def smoother(grid: pd.DataFrame) -> tuple:
    """Every variant's neighbourhood on the grid, built once per grid.

    Args:
        grid: The `param_` columns, in the panel's column order.

    Returns:
        (a sparse 0/1 matrix whose row i marks variant i's neighbours, itself included;
        the size of each neighbourhood). `sums @ score / count` is each neighbourhood's
        mean score in one sparse product.
    """
    if id(grid) not in _SMOOTHER or _SMOOTHER[id(grid)][0] is not grid:
        coords = coordinates(grid)
        groups = cKDTree(coords).query_ball_point(coords, r=NEIGHBOUR, p=np.inf)
        count = np.array([len(g) for g in groups])
        rows, cols = np.repeat(np.arange(len(groups)), count), np.concatenate(groups)
        sums = csr_matrix((np.ones(cols.size), (rows, cols)), shape=(len(groups),) * 2)
        _SMOOTHER.clear()
        _SMOOTHER[id(grid)] = (grid, sums, count)
    return _SMOOTHER[id(grid)][1:]


def random_profitable(score: np.ndarray, grid: pd.DataFrame,
                      rng: np.random.Generator) -> int:
    """Take any parameter set that made money in sample, at random.

    Args:
        score: One in-sample score per variant.
        grid: Unused.
        rng: The draw.

    Returns:
        Position of one uniformly chosen profitable variant, or of the maximum when the
        whole surface lost. It is the control the other two are worth measuring against:
        a rule that cannot beat this one is not selection, it is decoration.
    """
    winners = np.flatnonzero(score > 0)
    return int(rng.choice(winners)) if winners.size else int(np.argmax(score))


RULES = {"argmax": argmax, "plateau_centre": plateau_centre,
         "random_profitable": random_profitable}
