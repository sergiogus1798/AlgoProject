#!/usr/bin/env python3
"""core.significance's benchmark argument (OPEN.md #71): psr() and min_track_record() must
read a non-zero benchmark as the harder bar it is, and agree with each other at benchmark=0."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.significance import min_track_record, moments, psr

SEED = 7


def returns(n: int = 500, mean: float = 0.02, std: float = 0.10) -> np.ndarray:
    """Synthetic i.i.d. normal per-trade returns with a known Sharpe.

    Args:
        n: Observations.
        mean: True mean.
        std: True standard deviation.

    Returns:
        One draw, fixed seed, so its own sample Sharpe is known by construction.
    """
    return np.random.default_rng(SEED).normal(mean, std, n)


def test_psr_benchmark_raises_the_bar() -> None:
    """A higher benchmark can only lower the probability the edge clears it."""
    r = returns()
    zero = psr(r, 0.0)["psr"]
    sample_sharpe = moments(r)[0]
    half = psr(r, sample_sharpe / 2)["psr"]
    at_sharpe = psr(r, sample_sharpe)["psr"]
    assert zero > half > at_sharpe
    # Benchmarked at its own observed Sharpe, the z-score is exactly 0: psr reads 0.5.
    assert abs(at_sharpe - 0.5) < 1e-9


def test_min_track_record_benchmark_zero_matches_old_formula() -> None:
    """benchmark=0 must reproduce the pre-#71 formula exactly -- no drift for existing callers
    that have not been switched to a realistic benchmark yet (mcRetest, OPEN.md #71)."""
    r = returns()
    sharpe, skew, kurtosis = moments(r)
    old = 1 + (1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe ** 2) * (1.6448536269514722
                                                                        / sharpe) ** 2
    got = min_track_record(r, alpha=0.05)
    assert abs(got["needed"] - old) < 1e-6


def test_min_track_record_needs_more_against_a_realistic_benchmark() -> None:
    """A benchmark below the observed Sharpe but above zero asks for more track record, not
    less: the closer the bar sits to the observed Sharpe, the harder it is to clear."""
    r = returns()
    sample_sharpe = moments(r)[0]
    zero = min_track_record(r, benchmark=0.0)["needed"]
    quarter = min_track_record(r, benchmark=sample_sharpe / 4)["needed"]
    half = min_track_record(r, benchmark=sample_sharpe / 2)["needed"]
    assert zero < quarter < half


if __name__ == "__main__":
    test_psr_benchmark_raises_the_bar()
    test_min_track_record_benchmark_zero_matches_old_formula()
    test_min_track_record_needs_more_against_a_realistic_benchmark()
    print("ok")
