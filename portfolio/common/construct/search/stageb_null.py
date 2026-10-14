"""The selected null's searches: random admissible combinations put through the same selection."""

from collections.abc import Callable

import numba
import numpy as np
import pandas as pd

from portfolio.common.construct.mc import paths
from portfolio.common.construct.search import greedy, shortlist


@numba.njit(parallel=True, cache=True)
def _fill(graph: np.ndarray, sizes: np.ndarray, gens: list, out: np.ndarray) -> None:
    """Rows c, c+k, … from generator c (k = len(gens)): a shuffled-greedy clique, then a subset."""
    k = len(gens)
    for c in numba.prange(k):
        g = gens[c]
        for row in range(c, out.shape[0], k):
            clique = greedy.grow(graph, g.permutation(graph.shape[0]))
            g.shuffle(clique)
            picked = np.sort(clique[: min(sizes[row], clique.size)])
            out[row, : picked.size] = picked


def candidates(
    graph: np.ndarray, sizes: np.ndarray, n: int, rng: np.random.Generator
) -> np.ndarray:
    """Random admissible combinations, sized like the ones the real search evaluated.

    Each is a random subset of a shuffled-greedy maximal clique (any subset of a clique is
    one), its size drawn from `sizes`; a clique smaller than the size drawn is taken whole.
    Compiled, drawn from `paths.path_gens(rng)` (a fixed number of generators spawned from `rng`,
    so the result is the same whatever the thread count), since 2026-10-14 (owner, encargo 68 F5):
    the same distribution as before, other draws for the same `rng`, so a null stored before
    that date does not reproduce draw by draw.

    Args:
        graph: N x N bool admissible adjacency.
        sizes: The K of every combination the real search evaluated.
        n: Combinations to draw.
        rng: Source of randomness.

    Returns:
        int32 [n, max K], member indices padded with -1.
    """
    out = np.full((n, int(sizes.max())), -1, dtype=np.int32)
    _fill(
        np.ascontiguousarray(graph, dtype=np.bool_),
        rng.choice(sizes, size=n).astype(np.int64),
        paths.path_gens(rng),
        out,
    )
    return out


def shortlisted(
    score: Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]],
    graph: np.ndarray,
    identities: list[str],
    sizes: np.ndarray,
    n: int,
    cfg: dict,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """One null search up to its shortlist: random candidates, the search's own score and cut.

    Args:
        score: A padded batch in, each row's best P(pass) and its risk level out — the
            objective the real search ranked by.
        graph, identities: The admissible graph and its order.
        sizes, n: As `candidates()`.
        cfg: The construct config (`stageb`).

    Returns:
        `shortlist.diverse()`'s frame for this draw.
    """
    combos = candidates(graph, sizes, n, rng)
    best_p, best_r = score(combos)
    frame = pd.DataFrame(
        {
            "members": [
                "+".join(identities[i] for i in row[row >= 0]) for row in combos
            ],
            "score": best_p,
            "level": best_r,
        }
    )
    sb = cfg["stageb"]
    return shortlist.diverse(
        shortlist.ranked(frame), sb["shortlist_size"], sb["max_shared"], sb["shared_of"]
    )
