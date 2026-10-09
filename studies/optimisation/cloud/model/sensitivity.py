"""How the surface's variance splits between parameters: first-order and total Sobol indices."""

import numpy as np
from scipy.stats import qmc

from studies.optimisation.cloud.model import surrogate


def sobol(model: dict, power: int, seed: int) -> dict:
    """First-order and total Sobol indices of the smooth model.

    Args:
        model: What `surrogate.fit` returned.
        power: Base sample size as a power of two; the cost is 2**power * (k + 2)
            surrogate evaluations, which are arithmetic and not SQX runs.
        seed: Scrambling seed, so the indices are reproducible.

    Returns:
        `first` and `total`, one per parameter.

        Saltelli's estimator for the first order and Jansen's for the total, over a
        **uniform** cube: "if every live parameter were dialled anywhere in its plateau, who
        would move the result". They are indices of the fitted surface, not of the data: a
        surface that explains nothing still hands out a ranking, which is why
        `measure.reference` says whether it may be read.
    """
    k = model["k"]
    draw = qmc.Sobol(d=2 * k, scramble=True, seed=seed).random(2 ** power)
    a, b = draw[:, :k], draw[:, k:]
    ya, yb = surrogate.predict(model, a), surrogate.predict(model, b)
    variance = float(np.var(np.concatenate([ya, yb])))
    first, total = [], []
    for i in range(k):
        ab = a.copy()
        ab[:, i] = b[:, i]
        yab = surrogate.predict(model, ab)
        first.append(float(np.mean(yb * (yab - ya)) / variance))
        total.append(float(np.mean((ya - yab) ** 2) / (2 * variance)))
    return {"first": np.array(first), "total": np.array(total)}
