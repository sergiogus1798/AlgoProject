"""How much was really tried, across every search of a study rather than inside the last one."""

import numpy as np
import pandas as pd

from core.significance import moments
from core.surface import plateau

SHARPE_UNITS = ("per_period", "annualised")   # the only score units that are a Sharpe
YEAR = 252      # trading days a year, for converting SQX's annualised Sharpes


def accumulated(frame: pd.DataFrame, extra: int | None = 0) -> dict:
    """The number of trials and the spread of their scores, over the whole study.

    Args:
        frame: What `study.read` returned.
        extra: Looks at the data that left no search row -- the hypotheses the research
            memory counts for this study. The caller passes them; this module reads no memory.

    Returns:
        `n` trials (`searched` candidates ever scored plus `extra`), `sigma` the candidates'
        pooled standard deviation with ddof=1, and the searches behind both. `extra` raises
        N and leaves sigma alone: a hypothesis has no Sharpe to pool. The pooling is **exact**: each search's stored
        `ddof=1` spread is converted back to its population form, the mixture variance is
        `sum n_i(sigma_i^2 + mu_i^2)/N - grand^2`, and the result is converted back. No
        search has to keep its candidates around to be counted later, and the answer is
        the same as if it had.

        This is the number the deflated Sharpe should have been eating all along. Today it
        is fed the spread inside one mother's variant batch, which is narrower than the
        spread across every build, retest and screen the study ever ran, and narrower in
        the direction that makes a result look better.

    Only rows whose `score_unit` is a Sharpe are pooled into sigma, annualised ones converted
    to the per-period scale by 1/sqrt(252) (`unit` is always "per_period"). A row of any other
    unit (`p_pass`, `ev_bank_usd`) still adds its `n_scored` to N, since those are looks, but
    its scores are not Sharpes and never reach sigma.
    """
    extra = extra or 0
    scored = frame[frame["n_scored"].notna()] if len(frame) else frame
    if not len(scored):
        return {"n": 0, "sigma": float("nan"), "searches": 0}
    searched = int(scored["n_scored"].sum())
    scored = scored[scored["score_unit"].isin(SHARPE_UNITS) | scored["score_unit"].isna()]
    if not len(scored):
        return {"n": searched + extra, "searched": searched, "extra": extra,
                "sigma": float("nan"), "mean": float("nan"), "searches": 0, "unit": "per_period"}
    # annualised rows come to the per-day scale here, once, so no caller has to
    scale = np.where(scored["score_unit"] == "annualised", 1 / np.sqrt(YEAR), 1.0)
    n = scored["n_scored"].to_numpy(float)
    mean = scored["sharpe_mean"].to_numpy(float) * scale
    sd = scored["sharpe_std"].to_numpy(float) * scale
    total = n.sum()
    grand = float((n * mean).sum() / total)
    population = np.where(n > 1, sd ** 2 * (n - 1) / n, 0.0)
    variance = float((n * (population + mean ** 2)).sum() / total - grand ** 2)
    unbiased = variance * total / (total - 1)
    return {"n": searched + extra, "searched": searched, "extra": extra, "sigma": float(np.sqrt(max(unbiased, 0.0))),
            "mean": grand, "searches": int(len(scored)), "unit": "per_period"}


def overall(frames: list[pd.DataFrame]) -> dict:
    """N across every study: what the whole project has ever looked at, not one asset's share.

    Args:
        frames: One `study.read` frame per study (all of `study.studies()`).

    Returns:
        `accumulated` over their concatenation, plus `studies` that carry rows. Per-study N
        stays the one the deflated Sharpe uses; this is the larger bound, the honest count of
        how many ideas had a chance to look good by luck anywhere.
    """
    held = [f for f in frames if len(f)]
    return {**accumulated(pd.concat(held, ignore_index=True) if held else pd.DataFrame()),
            "studies": len(held)}


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
