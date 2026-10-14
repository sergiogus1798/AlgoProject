"""The monkey's path set: the same days, frequency, holding and risk with no edge — what the plan is worth as a lottery."""

from collections.abc import Callable

import numpy as np

from portfolio.funded.sim import haircut


def demean(paths: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """The whole edge taken off every closing day: the strategy's own days and excursions, zero drift."""
    return haircut.apply(paths, 1.0)


# name -> (model, what it holds fixed, what it removes). A path set of real random entries with
# costs, built elsewhere, replaces any of these through the command's `--monkey`.
MODELS: dict[str, tuple[Callable[[dict], dict], str, str]] = {
    "demean": (
        demean,
        "trading days, intraday excursions, volatility and its clustering",
        "the mean closed P&L per closing day (costs included: this monkey pays none)",
    ),
}


def zero_edge(paths: dict[str, np.ndarray], model: str) -> dict[str, np.ndarray]:
    """The zero-edge twin of a path set under one of `MODELS`."""
    return MODELS[model][0](paths)
