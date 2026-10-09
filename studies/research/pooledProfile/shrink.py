"""Random effects: each asset's effect pulled towards its group's mean by how noisy it is."""

import numpy as np


def random_effects(effect: np.ndarray, se: np.ndarray) -> dict:
    """DerSimonian-Laird's random-effects mean and the empirical-Bayes estimate of each asset.

    Args:
        effect: One estimate per asset.
        se: Its standard error.

    Returns:
        `mean` (the group's), `tau` (the spread of the true effects between assets, 0 when
        the estimates differ no more than their errors explain), `i2` (the share of their
        spread that is real difference) and `shrunk`: each asset's effect moved towards the
        mean by se^2 / (se^2 + tau^2). With tau 0 every asset reads the group's mean.
    """
    w = 1 / se ** 2
    fixed = (w * effect).sum() / w.sum()
    q = (w * (effect - fixed) ** 2).sum()
    spare = effect.size - 1
    tau2 = max(0.0, (q - spare) / (w.sum() - (w ** 2).sum() / w.sum())) if spare else 0.0
    wide = 1 / (se ** 2 + tau2)
    mean = (wide * effect).sum() / wide.sum()
    return {"mean": mean, "tau": np.sqrt(tau2), "i2": max(0.0, (q - spare) / q) if q > 0 else 0.0,
            "shrunk": mean + tau2 / (tau2 + se ** 2) * (effect - mean)}
