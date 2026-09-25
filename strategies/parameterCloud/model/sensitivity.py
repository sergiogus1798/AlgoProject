"""A2: how the metric's variance splits between parameters, computed on the surrogate."""

import numpy as np
from scipy.stats import qmc

from strategies.parameterCloud.model import surrogate


def sobol(model: dict, power: int, seed: int) -> dict:
    """First-order and total Sobol indices of the smooth model.

    Args:
        model: What `surrogate.fit` returned.
        power: Base sample size as a power of two; the cost is 2**power * (k + 2)
            surrogate evaluations, which are arithmetic and not SQX runs.
        seed: Scrambling seed, so the indices are reproducible.

    Returns:
        `first` and `total`, one per parameter, and the variance they decompose.

        Saltelli's own estimator for the first order and Jansen's for the total, over a
        **uniform** cube: the indices therefore answer "if every parameter were dialled
        anywhere in its explored range, who would move the result", which is the design
        question. They do not describe the distribution of tuples the batch happened to
        contain, and reading them as if they did is the one way to misuse them.

        The design this project fabricates is not a Saltelli design, so these cannot be
        estimated on the runs directly -- that would cost N(k+2) fresh backtests. Running
        them on the surrogate costs nothing and inherits the surrogate's roughness: an
        index from a model with a low r2 describes a shape the data only half supports.
    """
    k = model["k"]
    n = 2 ** power
    draw = qmc.Sobol(d=2 * k, scramble=True, seed=seed).random(n)
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
    return {"first": np.array(first), "total": np.array(total), "variance": variance,
            "n": n}
