"""The ways a person picks one parameter set off a surface, behind one signature."""

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

NEIGHBOUR = 1        # level steps in each parameter that still counts as next door


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
    coords = coordinates(grid)
    groups = cKDTree(coords).query_ball_point(coords, r=NEIGHBOUR, p=np.inf)
    return int(np.argmax([score[list(g)].mean() for g in groups]))


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
