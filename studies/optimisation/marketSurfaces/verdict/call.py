"""The call of step 18.5: the class of the joint order, and PASA / LIMBO / NO PASA from the three readings."""

import numpy as np

NO_DATA = "sin_dato"
# The step's state as the contract's word, and as the facts' word.
WORD = {"pass": "pasa", "watch": "limbo", "fail": "no_pasa"}


def order(found: dict, alpha: float, min_weight: float) -> str:
    """The class of the main market's order on the other markets.

    Args:
        found: A reading's `orden`: `rho`, `p_mas`, `p_menos` and `peso`, the sum of the
            weights of the markets in the mean.
        alpha: The cut on each tail of the sign-flip null.
        min_weight: Under this sum of weights there is no call.

    Returns:
        `positivo` (the best on the main market tend to be the best elsewhere, beyond noise),
        `perverso` (they tend to be the worst), `neutro`, or `sin_dato`.
    """
    if not np.isfinite(found["rho"]) or found["peso"] < min_weight:
        return NO_DATA
    return (
        "positivo"
        if found["p_mas"] <= alpha
        else "perverso"
        if found["p_menos"] <= alpha
        else "neutro"
    )


def step(deciding: str, premium_low: bool | None, oos2: str | None) -> str:
    """The state of the step: that of its worst reading.

    Args:
        deciding: order() of the deciding reading (build+oos1 on every market).
        premium_low: Whether the joint premium is at or under the cut of its null; None
            when it could not be measured.
        oos2: order() of the oos2 reading; None when it was not run.

    Returns:
        `fail` when the deciding order is perverse; `watch` when it has no data, when the
        premium is low or when the oos2 order is perverse; else `pass`. The premium and oos2
        can only add `watch`.
    """
    if deciding == "perverso":
        return "fail"
    return (
        "watch"
        if deciding == NO_DATA or premium_low or oos2 in ("perverso", NO_DATA)
        else "pass"
    )
