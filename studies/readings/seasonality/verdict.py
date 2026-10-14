"""Which calendar cells stand out after Benjamini-Hochberg, and whether the result leans on one."""

from typing import TypedDict

import numpy as np
import pandas as pd
from scipy import stats

from engines.inference import fdr

# Verdict words, worst first: verdict.csv carries them, a block carries their state.
STATES = {
    "fragil": "fail",
    "concentrado": "watch",
    "repartido": "pass",
    "sin_datos": "none",
}


class Call(TypedDict):
    """One strategy's reading: its word, the cell it rests on (if any) and what is left without it."""

    verdict: str
    cell: str
    rest_pnl: float


def judge(cells: pd.DataFrame, min_trades: int, q_max: float) -> pd.DataFrame:
    """Each cell's BH q and whether it is a discovery; the family is every tested cell at once.

    Args:
        cells: One row per cell with `key` (unique name), `n`, `p` (NaN when untested).
        min_trades: Below it a cell is «sin datos suficientes» and joins no family (D-3).
        q_max: The FDR held across the strategy's whole family of tested cells.

    Returns:
        `cells` with `tested`, `q` (NaN when untested) and `discovery`.
    """
    out = cells.copy()
    out["tested"] = out["n"] >= min_trades
    family = [
        {"metric": k, "p": p}
        for k, p, t in zip(out["key"], out["p"], out["tested"], strict=True)
        if t
    ]
    q = fdr.adjusted(family) if family else {}
    out["q"] = pd.Series(out["key"]).map(pd.Series(q, dtype=float)).astype(float)
    out["discovery"] = out["q"] <= q_max
    return out


def call(judged: pd.DataFrame, total_pnl: float) -> Call:
    """The word for one strategy.

    Args:
        judged: `judge()`'s output, with `pnl` (account currency) and `excess` (cell mean per
            lot minus the rest's) per cell.
        total_pnl: The strategy's whole oos1 net, account currency.

    Returns:
        fragil — a cell that pays more than the rest is a discovery and without its trades the
        oos1 net is zero or less: the result is that cell; concentrado — some cell is a
        discovery but the rest still earns; repartido — no discovery; sin_datos — no
        dimension has two cells with enough trades to compare.
    """
    if judged["tested"].sum() < 2:
        return {"verdict": "sin_datos", "cell": "", "rest_pnl": float("nan")}
    found = judged[judged["discovery"]]
    if found.empty:
        return {"verdict": "repartido", "cell": "", "rest_pnl": float("nan")}
    good = pd.DataFrame(found[found["excess"] > 0]).assign(
        rest=lambda f: total_pnl - f["pnl"]
    )
    if not good.empty and (good["rest"] <= 0).any():
        worst = good.loc[good["rest"].idxmin()]
        return {
            "verdict": "fragil",
            "cell": str(worst["key"]),
            "rest_pnl": float(worst["rest"]),
        }
    top = found.loc[pd.Series(found["q"]).idxmin()]
    rest = float(total_pnl - top["pnl"])
    return {"verdict": "concentrado", "cell": str(top["key"]), "rest_pnl": rest}


def beyond_chance(found: int, total: int, q_max: float) -> float:
    """One-sided binomial p that `found` strategies with any discovery is more than chance.

    Args:
        found: Strategies with at least one discovered cell.
        total: Strategies with at least two tested cells.
        q_max: The per-strategy FDR; under no calendar effect at all, BH names something in a
            strategy with probability at most q_max, so q_max * total is the ceiling of chance.

    Returns:
        P(X >= found), X ~ Binomial(total, q_max); 1.0 for an empty population.
    """
    if total == 0:
        return 1.0
    return float(stats.binom.sf(found - 1, total, q_max))


def recurring(discoveries: pd.DataFrame) -> pd.Series:
    """How many strategies found each cell paying more than the rest, most first.

    Args:
        discoveries: One row per (strategy, discovered cell) with `key` and `excess`.

    Returns:
        Count per cell key, descending; empty when nothing was found.
    """
    good = pd.DataFrame(discoveries[np.asarray(discoveries["excess"] > 0)])
    return good["key"].value_counts()
