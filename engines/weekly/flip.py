"""The weekly shared-sign flip null: one sign per week for every unit, and where a statistic falls in it."""

from collections.abc import Iterator
from typing import TypedDict

import numpy as np
from scipy.stats import rankdata


def signs(seed: int | np.random.SeedSequence, draws: int, weeks: int,
          block_weeks: int = 1) -> np.ndarray:
    """The null's sign vectors: +1 or -1 per week, consecutive weeks of a block sharing one.

    Args:
        seed: The run's root seed, or one child of its `SeedSequence.spawn`.
        draws: B, the number of sign vectors.
        weeks: W, the rows of the weekly panel.
        block_weeks: Weeks per block, counted from the panel's first week: 1, or 2 when too
            many trades straddle a weekend.

    Returns:
        draws x weeks of +-1.0, so `signs @ panel` (weeks x units) is draws x units: every
        unit's flipped total in every draw. The same seed gives the same matrix; cut it with
        chunks() and the draws do not change.
    """
    blocks = -(-weeks // block_weeks)
    coin = np.random.default_rng(seed).integers(0, 2, (draws, blocks), dtype=np.int8)
    # int8 until the last step, then in place: the float64 result is the only draws x weeks
    # matrix ever held (it was three: two temporaries and the repeat's copy)
    out = np.repeat(coin, block_weeks, axis=1)[:, :weeks].astype(np.float64)
    out *= 2.0
    out -= 1.0
    return out


def chunks(flips: np.ndarray, size: int) -> Iterator[np.ndarray]:
    """signs()'s matrix a few draws at a time, to bound what `chunk @ panel` and its ranks hold.

    Args:
        flips: What signs() returned.
        size: Draws per piece.

    Returns:
        Consecutive row slices (views) that concatenate back to `flips`.
    """
    return (flips[start:start + size] for start in range(0, len(flips), size))


class Tails(TypedDict):
    """tails() — one-sided p-values and the null's 5th/95th percentiles."""

    p_mas: float
    p_menos: float
    nulo_p5: float
    nulo_p95: float


def tails(observed: float, null: np.ndarray) -> Tails:
    """Where the observed statistic falls among the null's draws.

    Args:
        observed: The statistic on the real panel.
        null: The same statistic, one per draw.

    Returns:
        `p_mas` = (1 + #{null >= observed}) / (1 + B) and `p_menos` with <=: the two
        one-sided p-values, the observed one counted among the draws; and the null's 5th and
        95th percentiles, `nulo_p5` and `nulo_p95`.
    """
    lo, hi = np.percentile(null, [5, 95])
    return {"p_mas": float((1 + (null >= observed).sum()) / (1 + len(null))),
            "p_menos": float((1 + (null <= observed).sum()) / (1 + len(null))),
            "nulo_p5": float(lo), "nulo_p95": float(hi)}


def spearman(fixed: np.ndarray, redrawn: np.ndarray) -> np.ndarray:
    """Rank correlation of one fixed vector with another, or with every row of many.

    Args:
        fixed: One value per unit.
        redrawn: The same units, or draws x units.

    Returns:
        One rho, or one per draw; ties take their mean rank. NaN where a side is constant.
    """
    x = rankdata(fixed)
    y = rankdata(redrawn, axis=-1)
    x, y = x - x.mean(), y - y.mean(axis=-1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (y @ x) / np.sqrt((x @ x) * (y * y).sum(axis=-1))
