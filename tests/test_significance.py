#!/usr/bin/env python3
"""core.significance's benchmark argument (OPEN.md #71): psr() and min_track_record() must
read a non-zero benchmark as the harder bar it is, and agree with each other at benchmark=0.
Also footprint() itself (fixed 2026-09-29): the version this replaced gave the random trader
no market noise, only the dispersion of holding time, and scored it a Sharpe near the
market's own (~+2 on USDJPY) instead of near zero."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.significance import footprint, min_track_record, moments, psr

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
    """benchmark=0 must reproduce the pre-#71 formula exactly -- no drift for any caller that
    passes 0.0 explicitly."""
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


def test_footprint_zero_noise_reproduces_the_no_noise_value() -> None:
    """sigma=0 collapses `mean(var_i)` to 0, so SR_b is exactly `moments()` of the per-trade
    means -- the known-answer case every caller's own footprint() reduces to when the market
    is modelled as noiseless (the bug this replaces treated every case that way)."""
    rng = np.random.default_rng(11)
    n = 300
    h = rng.uniform(1, 20, n)          # bars held
    d = rng.choice([1.0, -1.0], n)
    s = rng.uniform(0.5, 2.0, n)
    c = rng.uniform(0, 3, n)
    mu, pv = 0.02, 1.3
    got = footprint(h, d, s, c, mu, 0.0, pv)
    want = moments(d * mu * h * s * pv - c)[0]
    assert abs(got - want) < 1e-9


def test_footprint_zero_drift_and_cost_gives_zero() -> None:
    """A synthetic random walk (mu=0) with no cost: every hypothetical trade's mean P/L is
    exactly 0 whatever its hold, direction or size, so SR_b is exactly 0 -- the honest
    "no edge, no cost" null the old formula could never reach because it had no noise term
    to divide by 0 mean sensibly."""
    rng = np.random.default_rng(3)
    n = 400
    h = rng.uniform(1, 30, n)
    d = rng.choice([1.0, -1.0], n)
    s = rng.uniform(0.5, 3.0, n)
    c = np.zeros(n)
    got = footprint(h, d, s, c, 0.0, 1.7, 1.0)
    assert abs(got) < 1e-12


def test_footprint_realistic_gold_numbers_are_small_and_below_buy_and_hold() -> None:
    """mu, sigma from real XAUUSD M30 bars 2018-2022 (`core.barstore`), a typical 8-bar hold:
    the random trader's Sharpe is small (|SR_b| < 0.1, reported below) and below the Sharpe of
    holding the whole window once -- the fix's whole point is that noise, not just occupancy,
    sets the random trader's dispersion, so a short, noisy hold does not inherit a
    buy-and-hold-sized Sharpe."""
    from core import barstore
    bars = barstore.read("XAUUSD_DukasM1_Infinox", "M30").loc["2018-01-01":"2022-12-31"]
    diffs = bars["Close"].diff().dropna().to_numpy()
    mu, sigma = float(diffs.mean()), float(diffs.std(ddof=1))
    rng = np.random.default_rng(5)
    n = 300
    h = np.full(n, 8.0)
    d = rng.choice([1.0, -1.0], n)
    s = np.ones(n)
    c = np.full(n, 0.02)
    sr_b = footprint(h, d, s, c, mu, sigma, 1.0)
    print(f"XAUUSD M30 2018-2022: mu={mu:.4f} sigma={sigma:.4f} SR_b(hold=8)={sr_b:.4f}")
    assert abs(sr_b) < 0.1
    bars_n = len(bars) - 1
    sr_buy_and_hold = mu * np.sqrt(bars_n) / sigma        # a single hold of the whole window
    assert abs(sr_b) < abs(sr_buy_and_hold)


def test_footprint_as_benchmark_reproduces_openmd71() -> None:
    """Fed into psr() as `benchmark`, a footprint() a random trader would have paid more cost
    for is an easier bar to clear -- the same property test_psr_benchmark_raises_the_bar
    checks for a hand-picked benchmark, now checked for one footprint() actually computed."""
    r = returns()
    rng = np.random.default_rng(5)
    n = 500
    h = np.ones(n)   # constant hold: every trade's footprint moves only with cost
    d = np.ones(n)
    s = np.ones(n)
    cheap = footprint(h, d, s, rng.normal(0.0, 1.0, n), 0.0, 1.0, 1.0)
    costly = footprint(h, d, s, rng.normal(0.3, 1.0, n), 0.0, 1.0, 1.0)
    assert cheap > costly       # more cost -> a smaller footprint to beat
    assert psr(r, cheap)["psr"] < psr(r, costly)["psr"]


if __name__ == "__main__":
    test_psr_benchmark_raises_the_bar()
    test_min_track_record_benchmark_zero_matches_old_formula()
    test_min_track_record_needs_more_against_a_realistic_benchmark()
    test_footprint_zero_noise_reproduces_the_no_noise_value()
    test_footprint_zero_drift_and_cost_gives_zero()
    test_footprint_realistic_gold_numbers_are_small_and_below_buy_and_hold()
    test_footprint_as_benchmark_reproduces_openmd71()
    print("ok")
