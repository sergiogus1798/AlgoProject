"""Wald's sequential test on a funded account's per-trade results in R."""

from typing import TypedDict


class Verdict(TypedDict):
    """The SPRT's reading after `n` trades: continue, raise or retire, with the statistic and its bounds."""

    verdict: str
    n: int
    stat: float
    drift: float
    lower: float
    upper: float


def boundaries(sprt: dict) -> tuple[float, float, float]:
    """The drift and the two limits of S_n - drift*n, derived from the test's parameters.

    Args:
        sprt: mu0, mu1 (R per trade), sigma (R), ln_a, ln_b.

    Returns:
        (drift, lower, upper): drift = (mu0 + mu1) / 2; limit = ln * sigma^2 / (mu1 - mu0).
    """
    gap = sprt["mu1"] - sprt["mu0"]
    scale = sprt["sigma"] ** 2 / gap
    return (sprt["mu0"] + sprt["mu1"]) / 2, sprt["ln_b"] * scale, sprt["ln_a"] * scale


def run(results_r: list[float], sprt: dict) -> Verdict:
    """Walk the trades in order and stop at the first boundary crossed.

    Args:
        results_r: Result of each closed trade, in R, oldest first.
        sprt: As `boundaries`.

    Returns:
        {"verdict": "raise" | "retire" | "continue", "n": trades read up to the crossing (all
        when none), "stat": S_n - drift*n there, "drift", "lower", "upper"}.
    """
    drift, lower, upper = boundaries(sprt)
    total, stat = 0.0, 0.0
    for n, r in enumerate(results_r, 1):
        total += r
        stat = total - drift * n
        if stat >= upper:
            return {"verdict": "raise", "n": n, "stat": stat, "drift": drift, "lower": lower, "upper": upper}
        if stat <= lower:
            return {"verdict": "retire", "n": n, "stat": stat, "drift": drift, "lower": lower, "upper": upper}
    return {"verdict": "continue", "n": len(results_r), "stat": stat, "drift": drift, "lower": lower,
            "upper": upper}
