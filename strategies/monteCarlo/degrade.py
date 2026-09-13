"""Whether each family's headline statistic degrades from in-sample to out-of-sample."""

import numpy as np

from strategies.monteCarlo import confidence, engine, metrics, stream, stress


def scope_shape(source: dict, positions: np.ndarray, kind: str, model: str, block: int,
                metric: str, cfg: dict) -> dict | None:
    """One family's headline statistic, resampled on just one IS/OOS scope's trades.

    Args:
        source: What stream.build() returned.
        positions: Trades to keep — an IS or OOS subset from stream.samples().
        kind: "draw" or "stress".
        model: Key of draws.DRAWS or stress.STRESS.
        block: Block length, ignored by the models that have none.
        metric: Key of metrics.NAMES to reduce the simulated paths to.
        cfg: What config.load() returned.

    Returns:
        What metrics.shape() returns plus "n", the trades in this scope, or None when the
        scope has too few trades to resample — an IS or OOS split that is mostly gaps is
        not a distribution.
    """
    if positions.size < confidence.MEAN_PROVISIONAL:
        return None
    cut = stream.restrict(source, positions)
    got = engine.sequential(engine.payload(cut), kind, model, block,
                            cfg["global"]["n_sims"], cfg)
    seen = metrics.observed(cut["pnl"], cfg["global"]["starting_equity"])
    shape = metrics.shape(got[metric], seen[metric], cfg["global"]["report_percentile"])
    return {**shape, "n": int(positions.size)}


def overlay(source: dict, cfg: dict) -> dict:
    """The IS/OOS pair of every family that gets a degradation check.

    Args:
        source: What stream.build() returned.
        cfg: What config.load() returned.

    Returns:
        {family: {"IS": shape|None, "OOS": shape|None, "metric": name}}. Keyed "A"
        (drawdown under the headline reordering), "B" and "D" (net profit under the same
        i.i.d. bootstrap — the same numbers, since both ask the identical composition
        question), and "C.<test>" for each of Family C's four stress tests' net profit.
        None where a scope did not have enough trades to resample at all.

        Every (family, scope) pair is its own full-n_sims resampling, same cost as one
        Family B sample — fourteen of them for A, B, C's four tests and D. Run one at a
        time they would add minutes per strategy, so they are dispatched to the same
        process pool stability.py uses, not looped in this one process.
    """
    samples = stream.samples(source)
    block = cfg["blocks"]["block_min"]
    spec = {"A": ("draw", "stationary", block, "dd_pct"),
            "B": ("draw", "iid_bootstrap", 0, "net"),
            "D": ("draw", "iid_bootstrap", 0, "net"),
            **{f"C.{name}": ("stress", name, 0, "net") for name in stress.STRESS}}
    keys, jobs = [], []
    for fam, (kind, model, blk, metric) in spec.items():
        for scope, positions in samples.items():
            keys.append((fam, scope))
            jobs.append((source, positions, kind, model, blk, metric, cfg))
    shapes = engine.pool(cfg).map(scope_shape, *zip(*jobs)) if jobs else []
    out = {fam: {"metric": spec[fam][3]} for fam in spec}
    for (fam, scope), shape in zip(keys, shapes):
        out[fam][scope] = shape
    return out
