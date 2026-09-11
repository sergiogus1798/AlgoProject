"""Whether the simulation count is high enough: the same gate numbers, computed again."""

import numpy as np

from strategies.monteCarlo import engine, stress, sweeps

# The percentiles a gate is read from. Nothing else is repeated: the point is to price the
# noise in the numbers that decide, not to run the whole study eight times.
DRIVERS = (("dd_pct", 95), ("dd_pct", 99), ("net", 5), ("pf", 5))


def _once(data: dict, cfg: dict, sims: int) -> dict[str, float]:
    """One independent recomputation of every gate-driving percentile.

    Args:
        data: What engine.payload() returned.
        cfg: What config.load() returned.
        sims: Simulations per sub-test.

    Returns:
        {name: value} for the headline reordering run, the composition baseline and each
        execution stress. Fresh entropy, like every other run in the module.
    """
    block = cfg["blocks"]["block_min"]
    got = {sweeps.HEADLINE: engine.single(data, "draw", "stationary", block, sims, cfg),
           sweeps.BASELINE: engine.single(data, "draw", "iid_bootstrap", 0, sims, cfg)}
    got.update({k: engine.single(data, "stress", k, 0, sims, cfg) for k in stress.STRESS})
    return {f"{label}.{metric}.{q}": float(np.nanpercentile(arr[metric], q))
            for label, arr in got.items() for metric, q in DRIVERS}


def spread(source: dict, cfg: dict) -> dict:
    """How much each gate-driving number moves between independent runs.

    Args:
        source: What stream.build() returned.
        cfg: What config.load() returned.

    Returns:
        Per number: its mean across the repeats and the spread as a fraction of that mean,
        plus whether any of them exceeds the tolerance. Runs are unseeded by design, so
        this is what replaces reproducibility: it does not promise the same number twice,
        it measures how far from the same it is, and says to raise n_sims when that is too
        far to decide on.
    """
    cfgs = cfg["stability"]
    data = engine.payload(source)
    sims = cfg["global"]["n_sims"]
    repeats = cfgs["n_stability_runs"]
    runs = list(engine.pool(cfg).map(_once, [data] * repeats, [cfg] * repeats,
                                     [sims] * repeats))
    out = {}
    for key in runs[0]:
        values = np.array([r[key] for r in runs])
        scale = abs(values.mean()) or 1.0
        out[key] = {"mean": float(values.mean()),
                    "spread": float((values.max() - values.min()) / scale)}
    worst = max(out, key=lambda k: out[k]["spread"])
    return {"runs": cfgs["n_stability_runs"], "by_number": out, "worst": worst,
            "worst_spread": out[worst]["spread"],
            "unstable": bool(out[worst]["spread"] > cfgs["stability_tol"])}
