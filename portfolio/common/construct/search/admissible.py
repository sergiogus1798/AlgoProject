"""The admissible graph: which pairs of a pool clear every pairwise filter."""

import numpy as np
import pandas as pd

from portfolio.common.construct.pairs import stress

MEASURE_KEY = {
    "pearson_monthly": "pearson", "pearson_daily": "pearson",
    "spearman_monthly": "spearman", "spearman_daily": "spearman",
    "co_loss": "co_loss", "tail": "tail",
    "rolling_pearson_whole": "rolling_whole", "rolling_pearson_recent": "rolling_recent",
    "rolling_spearman_whole": "rolling_whole", "rolling_spearman_recent": "rolling_recent",
    "stress": None,
}


def admissible(pairs: pd.DataFrame, identities: list[str], cfg: dict) -> dict:
    """The N x N admissible graph over `identities`, and why each failing pair fails.

    Args:
        pairs: `pairs.table.table()`'s long-form output.
        identities: Graph order.
        cfg: The engine's config (`cfg["pairs"]`: the threshold per key, `sign`,
            `min_overlap_months`) and `cfg["relaxed"]`.

    Returns:
        `graph`: N x N bool numpy array, diagonal False, symmetric, order `identities`.
        `failing`: one row per (i, j, filter) a pair fails — `overlap` when it has fewer than
        `min_overlap_months` shared months (no other filter is then checked), `undefined` for a
        NaN coefficient on a pair with enough overlap, or the measure's own name.
        `counts`: pairs failing each filter. `n_pairs`, `n_admissible_pairs`, `n_without_rolling` (pairs judged without the rolling
        filters: fewer shared months than one window). `n_in` = len
        (identities). `n_out` = identities with >= 1 admissible partner. `relaxed`: `cfg["relaxed"]`.
        `effective_n`: `{"calm": ..., "stress": ...}`, `pairs.stress.effective_n` on the pool's
        pearson_monthly matrix and on its stress matrix.
    """
    index = {name: k for k, name in enumerate(identities)}
    n = len(identities)
    pc = cfg["pairs"]
    key = pairs["measure"].map(MEASURE_KEY)
    overlap = pairs["n_overlap_months"].to_numpy()
    too_short = overlap < pc["min_overlap_months"]
    # Owner 2026-09-30: under one full rolling window the rolling filters do not apply.
    no_window = (overlap < pc["rolling_months"]) & pairs["measure"].str.startswith("rolling_").to_numpy()
    applies = key.notna().to_numpy() & ~too_short & ~no_window
    value = pairs["value"].to_numpy(dtype=float)
    threshold = key.map(lambda k: pc[k] if isinstance(k, str) else np.nan).to_numpy(dtype=float)
    two_sided = (pc["sign"] == "abs") & ~pairs["measure"].isin(pc["one_sided"]).to_numpy()
    undefined = applies & np.isnan(value)
    exceeds = applies & ~undefined & np.where(two_sided, np.abs(value) > threshold, value > threshold)
    label = np.where(too_short, "overlap", np.where(undefined, "undefined", pairs["measure"].to_numpy()))
    failing = (pd.DataFrame({"i": pairs["i"], "j": pairs["j"], "filter": label})
               [too_short | undefined | exceeds].drop_duplicates(ignore_index=True))
    every = pairs[["i", "j", "n_overlap_months"]].drop_duplicates(["i", "j"])
    no_rolling = int(((every["n_overlap_months"] >= pc["min_overlap_months"])
                      & (every["n_overlap_months"] < pc["rolling_months"])).sum())
    bad = set(zip(failing["i"], failing["j"]))
    graph = np.zeros((n, n), dtype=bool)
    for i, j in zip(every["i"], every["j"]):
        if (i, j) not in bad:
            graph[index[i], index[j]] = graph[index[j], index[i]] = True

    counts = failing["filter"].value_counts().to_dict()
    n_pairs = len(every)
    n_out = int(graph.any(axis=1).sum())
    return {
        "graph": graph,
        "failing": failing,
        "counts": counts,
        "n_pairs": n_pairs,
        "n_admissible_pairs": int(graph.sum() // 2),
        "n_without_rolling": no_rolling,
        "n_in": n,
        "n_out": n_out,
        "relaxed": cfg["relaxed"],
        "effective_n": {
            "calm": stress.effective_n(_corr_matrix(pairs, identities, "pearson_monthly")),
            "stress": stress.effective_n(_corr_matrix(pairs, identities, "stress")),
        },
    }


def _corr_matrix(pairs: pd.DataFrame, identities: list[str], measure: str) -> np.ndarray:
    """Symmetric identities x identities matrix of one measure's pair values, diagonal 1."""
    index = {name: k for k, name in enumerate(identities)}
    matrix = np.eye(len(identities))
    sub = pairs[pairs["measure"] == measure]
    for i, j, value in zip(sub["i"], sub["j"], sub["value"]):
        if pd.isna(value):
            continue
        a, b = index[i], index[j]
        matrix[a, b] = matrix[b, a] = value
    return matrix
