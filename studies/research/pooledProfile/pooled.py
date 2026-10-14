"""The group statistic: every asset's standardised measure added up, real and under the null."""

from typing import TypedDict

import numpy as np


class Against(TypedDict):
    """The pooled statistic against its null: statistic, p, assets counted per test, placebo p-values."""

    stat: np.ndarray
    p: np.ndarray
    assets: np.ndarray
    placebo_p: np.ndarray


def standardised(sims: np.ndarray) -> np.ndarray:
    """Each asset's null draws centred and scaled by their own mean and spread.

    Args:
        sims: assets x draws x tests.

    Returns:
        The same shape; a test whose draws do not move is 0 everywhere.
    """
    centre, spread = sims.mean(axis=1, keepdims=True), sims.std(axis=1, ddof=1, keepdims=True)
    return np.divide(sims - centre, spread, out=np.zeros_like(sims), where=spread > 0)


def combined(z: np.ndarray, tested: np.ndarray) -> np.ndarray:
    """Stouffer's sum over the assets that have the test: sum of z over the root of their count.

    Args:
        z: assets x ... x tests.
        tested: assets x tests, True where the asset has enough trades for the test.

    Returns:
        ... x tests. No correlation between assets is assumed here: the null it is compared
        with is the same sum on jointly resampled draws, which carries whatever they share.
    """
    mask = tested.reshape(tested.shape[0], *([1] * (z.ndim - 2)), tested.shape[1])
    count = np.maximum(tested.sum(axis=0), 1)
    return (z * mask).sum(axis=0) / np.sqrt(count)


def against_null(z_real: np.ndarray, sims: np.ndarray, tested: np.ndarray,
                 placebos: int) -> Against:
    """The group's statistic, its p, and the p of null draws judged as if they were real.

    Args:
        z_real: assets x tests, each asset's z against its own draws.
        sims: assets x draws x tests, the jointly resampled null statistics.
        tested: assets x tests.
        placebos: How many draws to judge as placebo worlds.

    Returns:
        `stat` and `p` per test (share of draws at or above the real sum, the real one
        counted in), `assets` (how many entered each test) and `placebo_p`, placebos x tests:
        the share of draws at or above each of the first draws.
    """
    null = combined(standardised(sims), tested)
    stat = combined(z_real, tested)
    order = np.argsort(np.argsort(-null, axis=0, kind="stable"), axis=0)
    return {"stat": stat, "p": (1 + (null >= stat).sum(axis=0)) / (null.shape[0] + 1),
            "assets": tested.sum(axis=0), "placebo_p": (order[:placebos] + 1) / null.shape[0]}
