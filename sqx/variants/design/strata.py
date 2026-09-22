"""The three ways a tuple gets into the design. One signature, one registry, one table each."""

import itertools
import math

import numpy as np
from scipy.stats import qmc


def _spread(values: list[float], count: int) -> list[float]:
    """A coarse subset of one parameter's levels, both ends kept.

    Args:
        values: The levels, ascending.
        count: How many to keep.

    Returns:
        Evenly spaced levels including the first and the last. Both ends are kept because
        a factorial that never visits the edge of a span cannot show that the span is
        too narrow.
    """
    idx = np.unique(np.round(np.linspace(0, len(values) - 1, count)).astype(int))
    return [values[i] for i in idx]


def _draw(points: list[tuple], budget: int, rng: np.random.Generator) -> list[tuple]:
    """Cut an enumerated set down to the budget, without replacement.

    Args:
        points: Index tuples.
        budget: How many are wanted.
        rng: The design's generator.

    Returns:
        All of them when they fit, otherwise a uniform sample of that size.
    """
    if len(points) <= budget:
        return points
    return [points[i] for i in rng.choice(len(points), budget, replace=False)]


def neighbourhood(levels: dict[str, list[float]], budget: int,
                  context: dict) -> list[dict[str, float]]:
    """Every tuple within a few level steps of the centre.

    Args:
        levels: Parameter name to its levels.
        budget: Maximum tuples to return.
        context: Needs `centre` (name to level index), `radius` and `rng`.

    Returns:
        The full lattice ball of that Manhattan radius around the centre tuple, sampled
        down if it overruns the budget. This is the stratum that measures how steep the
        plateau is right where the strategy would be deployed; nothing else in the design
        resolves distance 1.
    """
    names = sorted(levels)
    start = tuple(context["centre"][n] for n in names)
    seen, frontier = {start}, {start}
    for _ in range(context["radius"]):
        grown = set()
        for point in frontier:
            for i, name in enumerate(names):
                for step in (-1, 1):
                    move = list(point)
                    move[i] += step
                    if 0 <= move[i] < len(levels[name]) and tuple(move) not in seen:
                        seen.add(tuple(move))
                        grown.add(tuple(move))
        frontier = grown
    points = _draw(sorted(seen), budget, context["rng"])
    return [{n: levels[n][p[i]] for i, n in enumerate(names)} for p in points]


def factorial(levels: dict[str, list[float]], budget: int,
              context: dict) -> list[dict[str, float]]:
    """A complete grid over a coarsened set of levels, as fine as the budget allows.

    Args:
        levels: Parameter name to its levels.
        budget: Maximum tuples to return.
        context: Needs `weights` (name to eta-squared), `min_levels` and `rng`.

    Returns:
        The Cartesian product of a subset of each parameter's levels. The subsets start at
        `min_levels` and grow one parameter at a time, most influential first, for as long
        as the product still fits. Saturating the budget this way keeps the grid complete
        -- every combination of the levels it does use is present -- which is what makes
        an interaction between two parameters visible at all.

        When even the minimum product overruns the budget the grid is sampled instead, and
        it stops being complete. That is reported, not hidden.
    """
    names = sorted(levels)
    counts = {n: min(context["min_levels"], len(levels[n])) for n in names}
    product = math.prod(counts.values())
    while True:
        grow = [n for n in names if counts[n] < len(levels[n])
                and product // counts[n] * (counts[n] + 1) <= budget]
        if not grow:
            break
        best = max(grow, key=lambda n: context["weights"].get(n, 0.0))
        counts[best] += 1
        product = math.prod(counts.values())
    coarse = [_spread(levels[n], counts[n]) for n in names]
    points = _draw(list(itertools.product(*coarse)), budget, context["rng"])
    return [dict(zip(names, p)) for p in points]


def coverage(levels: dict[str, list[float]], budget: int,
             context: dict) -> list[dict[str, float]]:
    """A low-discrepancy sweep of the whole space, frozen parameters included.

    Args:
        levels: Parameter name to its levels -- here every parameter, not only the live ones.
        budget: Maximum tuples to return.
        context: Needs `seed`.

    Returns:
        Sobol points mapped onto the level lists. Two jobs: reach the corners the dense and
        the coarse strata never visit, and vary the parameters the brief froze, so the
        freezing decision is tested by the same run instead of being assumed.

        Sobol is drawn in a power-of-two block and then cut, because its balance properties
        hold on those block sizes and on no other.
    """
    names = sorted(levels)
    size = 2 ** math.ceil(math.log2(max(budget, 2)))
    unit = qmc.Sobol(d=len(names), scramble=True, seed=context["seed"]).random(size)[:budget]
    return [{n: levels[n][min(int(row[i] * len(levels[n])), len(levels[n]) - 1)]
             for i, n in enumerate(names)} for row in unit]


# Every stratum takes (levels, budget, context) and returns tuples. What each one holds
# fixed and what it varies is the table in README.md; adding a fourth is a function and
# a row, and nothing else changes.
STRATA = {"neighbourhood": neighbourhood, "factorial": factorial, "coverage": coverage}
