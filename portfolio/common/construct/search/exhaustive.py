"""Every admissible combination of a small pool: all cliques of the graph, up to a limit."""

import numpy as np


def cliques(graph: np.ndarray, limit: int) -> np.ndarray | None:
    """Enumerate every clique of every size, the single strategies included.

    Args:
        graph: N x N bool admissible adjacency, symmetric, diagonal False.
        limit: The most combinations worth enumerating (`search.exhaustive_max`).

    Returns:
        bool [C, N] membership, or None as soon as there are more than `limit` -- the
        space is then the genetic search's.
    """
    n = graph.shape[0]
    found: list[np.ndarray] = []
    stack = [(np.empty(0, dtype=np.int32), np.arange(n, dtype=np.int32))]
    while stack:
        members, candidates = stack.pop()
        for pos, node in enumerate(candidates):
            grown = np.append(members, node)
            found.append(grown)
            if len(found) > limit:
                return None
            later = candidates[pos + 1:]
            stack.append((grown, later[graph[node, later]]))
    out = np.zeros((len(found), n), dtype=bool)
    for row, clique in enumerate(found):
        out[row, clique] = True
    return out
