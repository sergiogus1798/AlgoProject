#!/usr/bin/env python3
"""Known answers for engines.inference.localfdr: a mixture with a known share of planted z."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.inference import localfdr

NULL, PLANTED = 9000, 1000


def mixture() -> np.ndarray:
    """9,000 N(0.5, 0.5) and 1,000 shifted by +3 sigma, fixed seed."""
    rng = np.random.default_rng(1)
    return np.r_[rng.normal(0.5, 0.5, NULL), rng.normal(0.5 + 3 * 0.5, 0.5, PLANTED)]


def test_recovers_the_null_and_its_share() -> None:
    """The empirical null lands on the generating N(0.5, 0.5) and pi0 within 0.08 of 0.90 (it reads high by design: the central range
    of the mixture is not the null's, so the planted tail leaks in; 0.97 on this seed)."""
    got = localfdr.fit(mixture())
    assert 0 <= got["pi0"] - 0.90 < 0.08 and abs(got["delta0"] - 0.5) < 0.05
    assert abs(got["sigma0"] - 0.5) < 0.05


def test_p_is_monotone_and_keeps_the_planted() -> None:
    """p never falls as z rises, is 0 at or left of delta0, and p >= 0.15 keeps >= 800 of the
    planted 1,000 while letting through under 5 % of the nulls."""
    z = mixture()
    got = localfdr.fit(z)
    p = got["p"][np.argsort(z)]
    assert (np.diff(p) >= -1e-12).all() and (got["p"][z <= got["delta0"]] == 0).all()
    assert (got["p"][NULL:] >= 0.15).sum() >= 800 and (got["p"][:NULL] >= 0.15).mean() < 0.05


def test_a_light_tail_gets_zero() -> None:
    """A peaked, light-tailed lot (uniform on [-1, 2]) has no one standing out: p = 0 above
    delta0 + sigma0."""
    z = np.random.default_rng(2).uniform(-1, 2, 5000)
    got = localfdr.fit(z)
    assert (got["p"][z > got["delta0"] + got["sigma0"]] == 0).all()


def test_too_few_z_returns_empties() -> None:
    """Under MIN_Z z: no p, no figures, and the reason."""
    got = localfdr.fit(mixture()[:localfdr.MIN_Z - 1])
    assert got["p"] is None and got["delta0"] is None and got["reason"]


if __name__ == "__main__":
    test_recovers_the_null_and_its_share()
    test_p_is_monotone_and_keeps_the_planted()
    test_a_light_tail_gets_zero()
    test_too_few_z_returns_empties()
    print("ok")
