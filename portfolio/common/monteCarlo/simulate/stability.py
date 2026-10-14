"""Whether the simulation count is high enough: the same gate numbers, computed again."""

from typing import TypedDict

import numpy as np

from portfolio.common.monteCarlo.inputs import config
from portfolio.common.monteCarlo.model import stress
from portfolio.common.monteCarlo.simulate import engine


class Stability(TypedDict):
    """How much each gate-driving number moves between independent runs."""

    runs: int
    seeds: list[int]
    by_number: dict[str, dict[str, float]]
    worst: str
    worst_spread: float
    unstable: bool


# The percentiles a gate is read from. Nothing else is repeated: the point is to price the
# noise in the numbers that decide, not to run the whole study eight times.
DRIVERS = (("dd_pct", 95), ("dd_pct", 99), ("net", 5), ("pf", 5))


def _once(data: dict, cfg: dict, sims: int, seed: int) -> dict[str, float]:
    """One independent recomputation of every gate-driving percentile.

    Args:
        data: What engine.payload() returned.
        cfg: What config.load() returned.
        sims: Simulations per sub-test.

    Returns:
        {name: value} for the headline reordering run, the composition baseline and each
        execution stress. Seeded by `seed`.
    """
    block = cfg["blocks"]["block_min"]
    got = {config.HEADLINE: engine.sequential(data, "draw", "stationary", block, sims, cfg, seed),
           config.BASELINE: engine.sequential(data, "draw", "iid_bootstrap", 0, sims, cfg, seed)}
    got.update({k: engine.sequential(data, "stress", k, 0, sims, cfg, seed) for k in stress.STRESS})
    return {f"{label}.{metric}.{q}": float(np.nanpercentile(arr[metric], q))
            for label, arr in got.items() for metric, q in DRIVERS}


def spread(source: dict, cfg: dict) -> Stability:
    """How much each gate-driving number moves between independent runs.

    Args:
        source: What stream.build() returned.
        cfg: What config.load() returned.

    Returns:
        Per number: its mean across the repeats and the spread as a fraction of that mean,
        plus whether any of them exceeds the tolerance, and the `seeds` used. Every repeat
        draws from its own seed (`seed + 1 + i`, the run's own `seed` being the main run's),
        so the repeats are independent and the whole measurement reruns to the same numbers.
        It measures how far two independent runs are from each other, and says to raise
        n_sims when that is too far to decide on.
    """
    cfgs = cfg["stability"]
    data = engine.payload(source)
    sims = cfg["global"]["n_sims"]
    repeats = cfgs["n_stability_runs"]
    seeds = [config.seed(cfg) + 1 + i for i in range(repeats)]
    runs = list(engine.pool(cfg).map(_once, [data] * repeats, [cfg] * repeats,
                                     [sims] * repeats, seeds))
    out: dict[str, dict[str, float]] = {}
    for key in runs[0]:
        values = np.array([r[key] for r in runs])
        scale = abs(values.mean()) or 1.0
        out[key] = {"mean": float(values.mean()),
                    "spread": float((values.max() - values.min()) / scale)}
    worst = max(out, key=lambda k: out[k]["spread"])
    return {"runs": cfgs["n_stability_runs"], "seeds": seeds, "by_number": out, "worst": worst,
            "worst_spread": out[worst]["spread"],
            "unstable": bool(out[worst]["spread"] > cfgs["stability_tol"])}
