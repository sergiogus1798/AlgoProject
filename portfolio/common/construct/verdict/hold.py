"""Did the diversification hold: the chosen members' pair measures re-read on the judging stretch."""

import numpy as np
import pandas as pd

from ..pairs import stress

KEYS = ("pearson", "spearman", "co_loss", "tail")


def threshold_key(measure: str) -> str | None:
    """The config threshold a measure of the pairs table is held to; None for the reported ones."""
    if measure.startswith("rolling_"):
        return "rolling_" + measure.rsplit("_", 1)[1]
    return next((k for k in KEYS if measure.startswith(k)), None)


def held(pairs: pd.DataFrame, identities: list[str], cfg: dict) -> dict:
    """Each pair of the chosen combination against the thresholds it was admitted under.

    It chooses nothing and removes nothing: the combination was fixed before this ran.

    Args:
        pairs: `pairs.table.table()` on the judging stretch, the chosen members only.
        identities: The chosen members.
        cfg: The construct config (`pairs`: thresholds, `sign`, `one_sided`,
            `min_overlap_months`, `rolling_months`).

    Returns:
        `over` (one dict per pair and measure past its threshold: `i`, `j`, `measure`,
        `value`, `threshold`), `short` (pairs under the minimum overlap, not judged),
        `n_pairs`, `n_pairs_over`, `held` (no pair over) and `effective_n` (both formulas on
        the monthly Pearson matrix).
    """
    pc = cfg["pairs"]
    over, short = [], set()
    corr = np.eye(len(identities))
    index = {name: k for k, name in enumerate(identities)}
    for row in pairs.itertuples():
        if row.measure == "pearson_monthly" and np.isfinite(row.value):
            corr[index[row.i], index[row.j]] = corr[index[row.j], index[row.i]] = row.value
        key = threshold_key(row.measure)
        if row.n_overlap_months < pc["min_overlap_months"]:
            short.add((row.i, row.j))
            continue
        if key is None or not np.isfinite(row.value) or (
                row.measure.startswith("rolling_") and row.n_overlap_months < pc["rolling_months"]):
            continue
        two_sided = pc["sign"] == "abs" and row.measure not in pc["one_sided"]
        if (abs(row.value) if two_sided else row.value) > pc[key]:
            over.append({"i": row.i, "j": row.j, "measure": row.measure,
                         "value": float(row.value), "threshold": float(pc[key])})
    n_pairs = len(identities) * (len(identities) - 1) // 2
    n_over = len({(o["i"], o["j"]) for o in over})
    return {"over": over, "short": sorted(short), "n_pairs": n_pairs, "n_pairs_over": n_over,
            "held": n_over == 0,
            "effective_n": stress.effective_n(corr) if len(identities) > 1 else None}
