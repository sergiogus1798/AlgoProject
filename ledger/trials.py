"""How much was really tried, across every search of a study rather than inside the last one."""

import numpy as np
import pandas as pd

from core.significance import moments
from core.surface import plateau, trials


def accumulated(frame: pd.DataFrame) -> dict:
    """The number of trials and the spread of their scores, over the whole study.

    Args:
        frame: What `study.read` returned.

    Returns:
        `n` candidates ever scored, `sigma` their pooled standard deviation with ddof=1,
        and the searches behind both. The pooling is **exact**: each search's stored
        `ddof=1` spread is converted back to its population form, the mixture variance is
        `sum n_i(sigma_i^2 + mu_i^2)/N - grand^2`, and the result is converted back. No
        search has to keep its candidates around to be counted later, and the answer is
        the same as if it had.

        This is the number the deflated Sharpe should have been eating all along. Today it
        is fed the spread inside one mother's variant batch, which is narrower than the
        spread across every build, retest and screen the study ever ran, and narrower in
        the direction that makes a result look better.

    Raises:
        ValueError: The searches disagree about the unit their scores were in. Pooling an
            annualised Sharpe with a per-observation one produces a plausible number that
            means nothing, and that is the one failure this module must not commit.
    """
    scored = frame[frame["n_scored"].notna()] if len(frame) else frame
    if not len(scored):
        return {"n": 0, "sigma": float("nan"), "searches": 0}
    units = set(scored["score_unit"].dropna())
    if len(units) > 1:
        raise ValueError(f"ledger: las búsquedas mezclan unidades de score {units}; "
                         "un Sharpe anualizado y uno por observación no se agrupan")
    n = scored["n_scored"].to_numpy(float)
    mean, sd = scored["sharpe_mean"].to_numpy(float), scored["sharpe_std"].to_numpy(float)
    total = n.sum()
    grand = float((n * mean).sum() / total)
    population = sd ** 2 * (n - 1) / n
    variance = float((n * (population + mean ** 2)).sum() / total - grand ** 2)
    unbiased = variance * total / (total - 1)
    return {"n": int(total), "sigma": float(np.sqrt(max(unbiased, 0.0))),
            "mean": grand, "searches": int(len(scored)), "unit": units.pop()}


def population_n_eff(panel: pd.DataFrame, k_max: int) -> dict:
    """How many independent things a whole surviving population really is.

    Args:
        panel: Periods down, strategies across -- the same shape `gate/collect.py`
            harvests, not one mother's variants.
        k_max: Largest cluster count to consider.

    Returns:
        What `core.surface.trials.independent` returns, applied to the population instead
        of to a variant batch. Strategies that earn the same way week after week are one
        trial wearing several names, however different their rule trees look.
    """
    return trials.independent(panel, k_max)


def deflated(returns: np.ndarray, sigma: float, n_eff: int) -> dict:
    """The deflated Sharpe of one survivor, against everything the study ever tried.

    Args:
        returns: That strategy's per-period returns.
        sigma: The pooled spread from `accumulated`, in the same unit as those returns.
        n_eff: Independent trials, from `population_n_eff` or from `accumulated["n"]`.

    Returns:
        What `core.surface.plateau.deflated_sharpe` returns. Feed it `accumulated["n"]`
        and it asks "given everything ever tried"; feed it the clustered count and it asks
        "given everything ever tried that was actually different". Report both -- the raw
        count overstates the penalty and the clustered one understates it.
    """
    sharpe, skew, kurtosis = moments(returns)
    return plateau.deflated_sharpe(sharpe, sigma, n_eff, len(returns), skew, kurtosis)
