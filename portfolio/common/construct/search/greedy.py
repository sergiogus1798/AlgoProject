"""Shuffled greedy maximal cliques: the genetic algorithm's seed population (AF genetic.py:416-554)."""

import numba
import numpy as np


def seeds(graph: np.ndarray, n: int, rng: np.random.Generator) -> list[np.ndarray]:
    """Build `n` shuffled-greedy maximal cliques over the admissible graph.

    Args:
        graph: N x N bool adjacency, symmetric, diagonal False.
        n: How many seeds to build; a fresh shuffle each time, so two can coincide.
        rng: Source of randomness.

    Returns:
        `n` sorted int32 arrays, each a maximal clique under its own shuffle order (size 1
        when a node has no admissible partner).
    """
    order = np.arange(graph.shape[0])
    out = []
    for _ in range(n):
        rng.shuffle(order)
        out.append(np.sort(grow(graph, order)))
    return out


@numba.njit(cache=True)
def grow(graph: np.ndarray, order: np.ndarray) -> np.ndarray:
    """Walk `order`, keeping a node only while it is compatible with everything already kept."""
    picked = np.empty(order.size, dtype=np.int32)
    kept = 0
    for node in order:
        fits = True
        for j in range(kept):
            if not graph[node, picked[j]]:
                fits = False
                break
        if fits:
            picked[kept] = node
            kept += 1
    return picked[:kept]
