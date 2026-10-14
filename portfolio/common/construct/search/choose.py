"""The search by ranks (M3): every admissible combination when they are few, the GA otherwise."""

from typing import Any

import numpy as np
import pandas as pd

from portfolio.common.construct.search import exhaustive, genetic, greedy, objective


def choose(
    unit: np.ndarray,
    dates: pd.DatetimeIndex,
    graph: np.ndarray,
    cfg: dict,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Score the admissible combinations on build and name the best.

    Exhaustive: every clique is scored and the ranks are taken in that whole space. GA: the
    ranks are taken in a reference fixed before the first generation (`real.rank_reference`:
    "seeds", the greedy starting cliques), so a score means the same in every generation.
    Either way the score is the shifted minimum (`objective.score`).

    Args:
        unit: [N, D] each member's build daily P&L per unit of risk, 0 where it has no history.
        dates: The D build days.
        graph: N x N bool admissible adjacency.
        cfg: The construct config (`real`, `search`, `weights`).
        rng: Source of randomness (the GA only).

    Returns:
        `mode` ("exhaustive" or "ga"), `members` (bool [E, N], one row per evaluation),
        `table` (`objective.score`'s, of them), `score` ([E]), `best` (row of the highest
        score), `n_reference` (combinations the ranks were taken in).
    """
    real = cfg["real"]
    space = exhaustive.cliques(graph, real["exhaustive_max"])
    if space is not None:
        tables = objective.measure(unit, dates, space, cfg)
        score, table = objective.score(tables, tables)
        return {
            "mode": "exhaustive",
            "members": space,
            "table": table,
            "score": score,
            "best": int(np.argmax(score)),
            "n_reference": len(space),
        }

    if real["rank_reference"] != "seeds":
        raise SystemExit(
            "real.rank_reference no tiene valor: el GA puntúa por rangos contra "
            "un conjunto fijo y hay que decir cuál (hoy sólo «seeds»)"
        )
    n = graph.shape[0]
    seeds = greedy.seeds(graph, cfg["search"]["seeds"], rng)
    start = np.zeros((len(seeds), n), dtype=bool)
    for row, clique in enumerate(seeds):
        start[row, clique] = True
    reference = objective.measure(unit, dates, start, cfg)
    seen: list[tuple[np.ndarray, dict]] = []

    def score_batch(combos: np.ndarray) -> np.ndarray:
        """One generation's rank scores against the fixed reference; keeps what it measured."""
        members = objective.masks(combos, n)
        score, table = objective.score(
            objective.measure(unit, dates, members, cfg), reference
        )
        seen.append((members, table))
        return score

    run = genetic.run(graph, score_batch, seeds, cfg["search"]["ga"], rng)
    table = {k: np.concatenate([t[k] for _, t in seen]) for k in seen[0][1]}
    return {
        "mode": "ga",
        "members": np.vstack([m for m, _ in seen]),
        "table": table,
        "score": run["score"],
        "best": int(np.argmax(run["score"])),
        "n_reference": len(seeds),
    }
