"""The real path's null (Q11 d; owner 2026-10-05, R6): random admissible combinations of one size."""

import numpy as np

from portfolio.common.construct.search import exhaustive, greedy, objective


def draw(graph: np.ndarray, k: int, n: int, limit: int, rng: np.random.Generator) -> dict:
    """`n` random cliques of size `k`, with replacement — no search per draw.

    Args:
        graph: N x N bool admissible adjacency.
        k: Members per combination: the chosen portfolio's size.
        n: Draws.
        limit: Up to this many admissible combinations the space is enumerated and the draw is
            uniform over its size-`k` ones (`real.exhaustive_max`).
        rng: Source of randomness.

    Returns:
        `members` (bool [U, N], the distinct combinations drawn), `index` (int [n], each
        draw's row of `members`) and `n_space` (how many size-`k` admissible combinations
        exist; None when the space was too large to count).
    """
    space = exhaustive.cliques(graph, limit)
    if space is not None:
        of_k = space[space.sum(axis=1) == k]
        if not len(of_k):
            return {"members": of_k, "index": np.empty(0, dtype=np.int64), "n_space": 0}
        used, index = np.unique(rng.integers(0, len(of_k), n), return_inverse=True)
        return {"members": of_k[used], "index": index, "n_space": len(of_k)}
    # ponytail: above the limit a draw is a random subset of a shuffled-greedy maximal clique
    # -- admissible, not uniform over the size-k cliques; a clique sampler if a verdict on a
    # large pool ever sits near the bar
    rows = []
    for _ in range(50 * n):
        clique = greedy.seeds(graph, 1, rng)[0]
        if clique.size >= k:
            rows.append(np.sort(rng.choice(clique, size=k, replace=False)))
        if len(rows) == n:
            break
    if len(rows) < n:
        raise ValueError(f"random_k: {len(rows)} de {n} extracciones de tamaño {k} en {50 * n} intentos")
    distinct, index = np.unique(np.array(rows, dtype=np.int32), axis=0, return_inverse=True)
    return {"members": objective.masks(distinct, graph.shape[0]), "index": index.ravel(),
            "n_space": None}
