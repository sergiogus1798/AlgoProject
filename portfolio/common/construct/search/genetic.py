"""AlphaForge's genetic search over admissible cliques, rewritten as plain functions on numpy masks."""

import time
from collections.abc import Callable

import numpy as np


def is_clique(graph: np.ndarray, mask: np.ndarray) -> bool:
    """Whether every pair of members `mask` selects is an admissible edge."""
    idx = np.flatnonzero(mask)
    if idx.size <= 1:
        return True
    sub = graph[np.ix_(idx, idx)]
    return bool(sub[~np.eye(idx.size, dtype=bool)].all())


def repair(graph: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Drop members until `mask` is a clique: the least-connected member goes first each round."""
    mask = mask.copy()
    idx = np.flatnonzero(mask)
    while idx.size > 1:
        sub = graph[np.ix_(idx, idx)]
        degree = sub.sum(axis=1)
        if degree.min() == idx.size - 1:
            break
        mask[idx[int(np.argmin(degree))]] = False
        idx = np.flatnonzero(mask)
    return mask


def _pack(masks: np.ndarray) -> np.ndarray:
    """Boolean [P, N] population -> padded int32 [P, K_max] member indices, -1 padded."""
    counts = masks.sum(axis=1)
    k_max = int(counts.max()) if masks.size else 1
    out = np.full((masks.shape[0], max(k_max, 1)), -1, dtype=np.int32)
    for i, row in enumerate(masks):
        idx = np.flatnonzero(row)
        out[i, :idx.size] = idx
    return out


def _tournament(scores: np.ndarray, size: int, rng: np.random.Generator) -> int:
    """One parent index: the best of `size` random draws."""
    cand = rng.integers(0, scores.shape[0], size=size)
    return int(cand[np.argmax(scores[cand])])


def _mutate(mask: np.ndarray, rate: float, rng: np.random.Generator) -> np.ndarray:
    """Swap/add/remove one member at random, with probability `rate`."""
    if rng.random() >= rate:
        return mask
    mask = mask.copy()
    present, absent = np.flatnonzero(mask), np.flatnonzero(~mask)
    op = rng.integers(0, 3)  # 0 add, 1 remove, 2 swap
    if op in (1, 2) and present.size:
        mask[rng.choice(present)] = False
    if op in (0, 2) and absent.size:
        mask[rng.choice(absent)] = True
    return mask


def run(graph: np.ndarray, score: Callable[[np.ndarray], np.ndarray], seeds: list[np.ndarray],
        cfg: dict, rng: np.random.Generator) -> dict:
    """Tournament GA over clique masks: union crossover, swap/add/remove mutation, elitism.

    A child that is not a clique is repaired by dropping its least-connected member round by
    round (a graph-structural stand-in for AF's worst-scoring offender: repairing by score
    would cost one more batch call per child). Stops after `cfg["stagnation"]` generations
    with no rise in the best **absolute** score.

    Args:
        graph: N x N bool admissible adjacency.
        score: Scores a whole generation's population in one call -- padded int32
            [P, K_max] member indices (-1 padding) in, float64 [P] out.
        seeds: Starting cliques (`greedy.seeds`); the population is seeded round-robin from
            them, so `len(seeds) != cfg["population"]` is fine.
        cfg: `population, generations, elite, tournament, crossover, mutation, stagnation`.
        rng: Source of randomness.

    Returns:
        `members`: one int array per combination ever scored. `score`, `origin`
        ("seed" for generation 0, "ga" after), `generation`: matching arrays/lists.
        `best`: `{"members", "score"}` of the best ever seen. `generations_run`,
        `score_s` (time inside `score`), `overhead_s` (everything else: the GA's own cost).
    """
    n = graph.shape[0]
    pop = cfg["population"]
    masks = np.zeros((pop, n), dtype=bool)
    for i in range(pop):
        masks[i, seeds[i % len(seeds)]] = True

    all_members, all_scores, all_origin, all_gen = [], [], [], []
    best_score, best_mask, stagnant = -np.inf, masks[0].copy(), 0
    n_elite = max(1, int(round(cfg["elite"] * pop)))
    wall_start = time.perf_counter()
    score_time = 0.0
    gen = 0

    for gen in range(cfg["generations"]):
        combos = _pack(masks)
        t0 = time.perf_counter()
        scores = np.asarray(score(combos), dtype=float)
        score_time += time.perf_counter() - t0

        all_members += [np.flatnonzero(m) for m in masks]
        all_scores.append(scores)
        all_origin += ["seed" if gen == 0 else "ga"] * pop
        all_gen.append(np.full(pop, gen))

        top = int(scores.argmax())
        if scores[top] > best_score:
            best_score, best_mask, stagnant = float(scores[top]), masks[top].copy(), 0
        else:
            stagnant += 1
        if stagnant >= cfg["stagnation"]:
            break

        order = np.argsort(-scores)
        new_masks = [masks[i].copy() for i in order[:n_elite]]
        while len(new_masks) < pop:
            p1 = masks[_tournament(scores, cfg["tournament"], rng)]
            p2 = masks[_tournament(scores, cfg["tournament"], rng)]
            child = (p1 | p2) if rng.random() < cfg["crossover"] else p1.copy()
            child = _mutate(child, cfg["mutation"], rng)
            if not is_clique(graph, child):
                child = repair(graph, child)
            if not child.any():
                continue
            new_masks.append(child)
        masks = np.array(new_masks[:pop])

    overhead = (time.perf_counter() - wall_start) - score_time
    return {"members": all_members, "score": np.concatenate(all_scores),
            "origin": all_origin, "generation": np.concatenate(all_gen),
            "best": {"members": np.flatnonzero(best_mask), "score": best_score},
            "generations_run": gen + 1, "score_s": score_time, "overhead_s": overhead}
