"""The weekly sign-flip null keeps its size on correlated noise, Gaussian and skewed, and is seeded."""

import numpy as np
import pytest

from engines.weekly import flip

WEEKS, UNITS, DRAWS, ALPHA = (
    143,
    30,
    199,
    0.05,
)  # (1 + #) / 200 <= 0.05: an exact 5 % test
SIMS = 2000
# 2,000 simulations: the standard error of a 5 % rate is sqrt(.05 x .95 / 2000) = 0.0049
BAND = 3 * np.sqrt(ALPHA * (1 - ALPHA) / SIMS)


def gaussian(rng: np.random.Generator) -> np.ndarray:
    """Weeks x units of mean-zero noise, the units 0.9 correlated through one weekly factor."""
    common = rng.standard_normal((WEEKS, 1))
    return np.sqrt(0.9) * common + np.sqrt(0.1) * rng.standard_normal((WEEKS, UNITS))


def skewed(rng: np.random.Generator) -> np.ndarray:
    """Mean zero, few big wins and many small losses with Student-t(3) sizes, units correlated."""

    def lottery(shape: tuple[int, int]) -> np.ndarray:
        """One week in ten wins 9, the rest lose 1, times a heavy-tailed size."""
        return np.where(rng.random(shape) < 0.1, 9.0, -1.0) * np.abs(
            rng.standard_t(3, shape)
        )

    return 0.8 * lottery((WEEKS, 1)) + 0.2 * lottery((WEEKS, UNITS))


def rates(make: callable, seed: int) -> dict:
    """Share of no-edge panels each one-sided test rejects at ALPHA, for both statistics."""
    root = np.random.SeedSequence(seed)
    hits = np.zeros(4)
    for data, coin in zip(root.spawn(SIMS), root.spawn(SIMS)):
        rng = np.random.default_rng(data)
        weekly, inside = make(rng), rng.standard_normal(UNITS)
        flipped = flip.signs(coin, DRAWS, WEEKS) @ weekly
        rho = flip.tails(
            flip.spearman(inside, weekly.sum(axis=0)), flip.spearman(inside, flipped)
        )
        mid = flip.tails(np.median(weekly.sum(axis=0)), np.median(flipped, axis=1))
        hits += [
            rho["p_mas"] <= ALPHA,
            rho["p_menos"] <= ALPHA,
            mid["p_mas"] <= ALPHA,
            mid["p_menos"] <= ALPHA,
        ]
    return dict(zip(("rho+", "rho-", "median+", "median-"), hits / SIMS))


def test_size_on_correlated_gaussian_noise() -> None:
    """Both statistics reject 5 % of pure-noise panels, within three standard errors."""
    got = rates(gaussian, 1)
    print("gaussian", got)
    assert all(abs(rate - ALPHA) < BAND for rate in got.values()), got


def test_size_on_a_skewed_heavy_tailed_panel() -> None:
    """143 weeks of lottery-like noise: the measured rate is the result; the bounds are loose.

    Measured 2026-10-07 (seed 2, 2,000 panels): rho+ 0.053, rho- 0.051, median+ 0.022,
    median- 0.133. The rank correlation keeps its size. The median of the units' totals does
    NOT: a mean-zero lottery has its median below zero and the flip null is symmetric about
    zero, so the lower tail rejects 13 % at a nominal 5 % and the upper tail 2 %.
    """
    got = rates(skewed, 2)
    print("skewed", got)
    assert abs(got["rho+"] - ALPHA) < 0.03 and abs(got["rho-"] - ALPHA) < 0.03, got
    assert got["median+"] < 0.10 and got["median-"] < 0.20, got


def test_same_seed_same_draws_whatever_the_chunk() -> None:
    """One seed, one matrix; cut in pieces of any size it is the same draws."""
    whole = flip.signs(7, 500, WEEKS)
    assert np.array_equal(whole, flip.signs(np.random.SeedSequence(7), 500, WEEKS))
    assert not np.array_equal(whole, flip.signs(8, 500, WEEKS))
    assert set(np.unique(whole)) == {-1.0, 1.0} and abs(whole.mean()) < 0.01
    panel = gaussian(np.random.default_rng(0))
    for size in (1, 64, 499, 500, 9999):
        pieces = list(flip.chunks(whole, size))
        assert np.array_equal(np.concatenate(pieces), whole)
        assert np.allclose(np.concatenate([p @ panel for p in pieces]), whole @ panel)


def test_blocks_of_two_weeks_share_a_sign() -> None:
    """Weeks 0-1, 2-3, ... flip together; an odd last week stands alone."""
    two = flip.signs(3, 200, WEEKS, block_weeks=2)
    assert two.shape == (200, WEEKS) and np.array_equal(two[:, 0:-1:2], two[:, 1::2])
    assert not np.array_equal(two[:, 1:-1:2], two[:, 2::2])


def test_spearman_in_bulk_is_scipy_row_by_row() -> None:
    """Average ranks on ties, one rho per draw; a constant side is NaN."""
    from scipy.stats import spearmanr

    rng = np.random.default_rng(5)
    fixed, many = (
        rng.integers(0, 6, 40).astype(float),
        rng.integers(0, 6, (50, 40)).astype(float),
    )
    got = flip.spearman(fixed, many)
    assert np.allclose(got, [spearmanr(fixed, row)[0] for row in many])
    assert flip.spearman(fixed, many[0]) == pytest.approx(got[0])
    assert np.isnan(flip.spearman(fixed, np.ones(40)))


def test_tails_count_the_observed_among_the_draws() -> None:
    """(1 + #) / (1 + B), both sides, and the null's 5th and 95th percentiles."""
    got = flip.tails(2.0, np.array([0.0, 1.0, 2.0, 3.0]))
    assert got["p_mas"] == pytest.approx(3 / 5) and got["p_menos"] == pytest.approx(
        4 / 5
    )
    assert got["nulo_p5"] == pytest.approx(0.15) and got["nulo_p95"] == pytest.approx(
        2.85
    )
