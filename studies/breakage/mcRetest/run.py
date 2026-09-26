"""Puts one strategy through the four questions and returns the single result everything reads."""

import numpy as np
import pandas as pd

from core import fanout

from studies.breakage.mcRetest.inputs import tasks
from studies.breakage.mcRetest.measure import store
from studies.breakage.mcRetest.verdict import (attribution, evidence, fragility, gates, modes,
                                               scoring)

# Columns the questions actually read. Loading thirty when four are wanted costs nothing at
# five strategies and a great deal at seven hundred.
NEEDED = ("NetProfit", "ProfitFactor", "DrawdownPct", "NumberOfTrades", "AvgTrade", "StandardDev")

# 🔬 2026-09-26: a worker keeps ~0.3 GB resident once it has read one strategy's seven P&L
# partitions (0.45 GB with its imports), and a strategy takes about a second. 48 of them on 500
# strategies would be ~21 GB for no wall clock worth having; 16 keep it near 7 GB.
WORKERS = 16
# What the per-strategy workers read, set before the fork.
_SHARED: dict = {}


def _arrays(sims: pd.DataFrame, task: str, strategy: str) -> dict:
    """One task's metrics for one strategy, as plain arrays.

    Args:
        sims: What store.load_sims() returned.
        task: One task key.
        strategy: One strategy id.

    Returns:
        {metric: one value per simulation}.
    """
    rows = sims[(sims["task"] == task) & (sims["strategy"] == strategy)]
    return {name: rows[name].to_numpy(dtype=np.float64) for name in NEEDED}


def per_task(keys: dict, sims: pd.DataFrame, original: pd.DataFrame, strategy: str,
             cfg: dict) -> dict:
    """Questions 1 and 2 for every task of one strategy.

    Args:
        keys: project, databank and day, for reading the raw P/L.
        sims: What store.load_sims() returned.
        original: What store.load_original() returned.
        strategy: One strategy id.
        cfg: What inputs.config.load() returned.

    Returns:
        {task: fragility, modes, evidence and the original it was perturbed from}.
    """
    out = {}
    for task in tasks.TASKS:
        metrics = _arrays(sims, task, strategy)
        if not metrics["NetProfit"].size:
            continue
        row = original[(original["task"] == task) & (original["strategy"] == strategy)]
        pnl = store.load_pnl(**keys, task=task, strategy=strategy)
        counts = pnl.groupby("sim", observed=True).size().to_numpy()
        offsets = np.concatenate([[0], np.cumsum(counts)])
        out[task] = {
            "fragility": fragility.describe(metrics, pnl["pnl"].to_numpy(), offsets, cfg),
            "modes": modes.describe(metrics, float(row["NumberOfTrades"].iloc[0]), cfg),
            "evidence": evidence.empirical_sharpe(metrics, cfg),
            "original_net": float(row["NetProfit"].iloc[0]),
            # Kept so the figures can draw the outcome itself, not only its summary. The
            # renderer must never reach back into the parquet: one source per number.
            "_net": metrics["NetProfit"],
            "fan": fragility.fan(pnl["pnl"].to_numpy(), offsets, cfg)}
    return out


def one(keys: dict, sims: pd.DataFrame, original: pd.DataFrame, provenance: dict,
        strategy: str, cfg: dict) -> dict:
    """Everything the study concludes about one strategy.

    Args:
        keys: project, databank and day.
        sims: What store.load_sims() returned.
        original: What store.load_original() returned.
        provenance: The manifest's entries for this strategy, keyed by task.
        strategy: One strategy id.
        cfg: What inputs.config.load() returned.

    Returns:
        The four questions, the flags and the verdict. Produces numbers and judges none of
        them: `gates` owns every threshold and computes nothing, and this owns the
        computation and decides nothing.
    """
    by_task = per_task(keys, sims, original, strategy, cfg)
    pnl = store.load_pnl(**keys, task="stress", strategy=strategy)
    body = {**by_task,
            "psr": evidence.analytic_sharpe(pnl.groupby("sim", observed=True)["pnl"].sum().to_numpy(), cfg),
            "attribution": attribution.describe(
                {task: _arrays(sims, task, strategy)["NetProfit"] for task in by_task}, cfg)}
    flags = gates.check(body, provenance, cfg)
    scores = scoring.subscores(body, cfg)
    return {"strategy": strategy, **body, "flags": flags,
            "verdict": scoring.verdict(scores, flags, cfg)}


def _one(name: str) -> dict:
    """one() for one strategy, in a worker that inherited the ingest's tables by fork."""
    got = _SHARED
    return one(got["keys"], got["sims"], got["original"],
               {task: got["provenance"][f"{task}/{name}"] for task in tasks.TASKS
                if f"{task}/{name}" in got["provenance"]}, name, got["cfg"])


def battery(keys: dict, provenance: dict, cfg: dict) -> dict:
    """Every strategy of one ingest, plus what can only be said across them.

    Args:
        keys: project, databank and day.
        provenance: The manifest's task entries, keyed by "task/strategy".
        cfg: What inputs.config.load() returned.

    Returns:
        One entry per strategy, the effective number of independent bets, the multiplicity
        correction over the whole pool, and whether the ranking survived. The last three
        are cross-strategy facts and cannot be computed one strategy at a time -- which is
        why they live here and not in one().
    """
    sims = store.load_sims(**keys)
    original = store.load_original(**keys)
    # The eight tasks read one databank, so a strategy normally appears in all of them. One
    # that does not was curated out between two tasks, and it has no production run to be
    # read against -- reporting it would mean answering "what breaks it?" without the task
    # that answers it. It is named and dropped, not half-reported.
    ran = {t for t in tasks.TASKS if (sims["task"] == t).any()}
    present = {name: {t for t in ran if not sims[(sims["strategy"] == name)
                                                 & (sims["task"] == t)].empty}
               for name in sorted(sims["strategy"].unique())}
    partial = {n: sorted(ran - got) for n, got in present.items() if ran - got}
    for name, short in partial.items():
        print(f"fuera del informe, le faltan tareas: {name} — sin {', '.join(short)}")
    names = [n for n in present if n not in partial]
    # One strategy per process, the one with most simulations first: each reads its own
    # P&L partitions and nothing crosses between them until the pool below.
    _SHARED.update(keys=keys, sims=sims, original=original, provenance=provenance, cfg=cfg)
    got = dict(fanout.run(_one, {n: int((sims["strategy"] == n).sum()) for n in names},
                          WORKERS))
    per = {name: got[name] for name in names}

    pool = {f"{task}/{name}": got[task]["modes"]["bimodality"]["p"]
            for name, got in per.items() for task in tasks.TASKS
            if task in got and got[task]["modes"]["discriminated"]}
    base = original[original["task"] == "bar"].set_index("strategy")["NetProfit"].to_dict()
    tail = {name: got["stress"]["fragility"]["net_p5"]["point"] for name, got in per.items()}
    return {"strategies": per,
            "effective_bets": evidence.effective_bets(store.load_returns(**keys)),
            "multiplicity": evidence.corrected(pool, cfg),
            "rank_stability": evidence.rank_stability(base, tail, cfg)}
