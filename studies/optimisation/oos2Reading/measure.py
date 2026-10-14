"""The inference: a mother's weekly excess over her monkey, summed, against a centred sign-flip null."""

from typing import TypedDict

import numpy as np
import pandas as pd

from engines.weekly import flip


def weekly(mother: pd.Series, monkey: pd.Series) -> np.ndarray:
    """The week-by-week excess of the mother's daily P&L over the monkey's mean daily P&L.

    Args:
        mother, monkey: Daily P&L on the feed's days (`inputs.daily`, `engines.nulls.footprint`).

    Returns:
        One value per calendar week (Monday-start) of oos2: sum of the mother's days minus sum
        of the monkey's days. The total is her net P&L minus what the same footprint at random
        entries and the same hours is paid, drift included.
    """
    excess = mother.reindex(monkey.index).fillna(0.0) - monkey
    return (
        excess.groupby(pd.DatetimeIndex(excess.index).to_period("W")).sum().to_numpy()
    )


class Reading(TypedDict):
    """The sum of the weekly excess, its z, one-sided p and error, the weeks and the two flags."""

    suma: float
    z: float
    p: float
    p_error_mc: float
    semanas: int
    bajo_alfa: int
    corta: int


def read(excess: np.ndarray, cfg: dict, seed: np.random.SeedSequence) -> Reading:
    """The sum of the weekly excess and where it falls among centred sign flips of itself.

    Args:
        excess: `weekly()`.
        cfg: `null` of config.yaml: `draws`, `alpha`.
        seed: The mother's own stream.

    Returns:
        `suma`, `z` (the sum in the null's standard deviations; 0 when the series is flat),
        `p` (one-sided, `flip.tails` p_mas), `p_error_mc` (sqrt(p(1-p)/B), the Monte Carlo
        error of that p), `semanas`, `bajo_alfa` (1 when p <= alpha) and `corta` (1 when z <= 0:
        the only thing that cuts).
    """
    total = float(excess.sum())
    null = flip.signs(seed, cfg["draws"], len(excess)) @ (excess - excess.mean())
    spread = null.std(ddof=1)
    z = total / spread if spread > 0 else 0.0
    p = flip.tails(total, null)["p_mas"]
    return {
        "suma": total,
        "z": float(z),
        "p": p,
        "p_error_mc": float(np.sqrt(p * (1 - p) / cfg["draws"])),
        "semanas": len(excess),
        "bajo_alfa": int(p <= cfg["alpha"]),
        "corta": int(z <= 0),
    }
