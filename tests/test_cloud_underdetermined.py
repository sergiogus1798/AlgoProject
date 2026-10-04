#!/usr/bin/env python3
"""Known-answer test: the cloud study makes no plateau / smooth call from an under-determined local fit."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.cloud.model import surrogate
from studies.optimisation.cloud.verdict import call

V = {"rank_high": 0.8, "plateau_low": 0.3, "roughness_high": 0.5, "local_roughness_high": 0.5,
     "slope_high": 1.0}


def test_one_neighbour_is_no_plateau() -> None:
    """A neighbourhood of the origin alone has rank 1.0 and fraction 1.0: not 'plateau'."""
    reading = {"near": {"n": 1, "q": 1.0, "pi": 1.0}}
    assert call.point(reading, V) == "sin_dato"
    assert call.point({"near": {"n": 40, "q": 1.0, "pi": 1.0}}, V) == "plateau"


def test_twenty_points_in_seven_parameters_is_never_smooth() -> None:
    """20 noise points, 7 parameters (36 coefficients): R2 = 1.0 by interpolation, yet no 'smooth'."""
    rng = np.random.default_rng(0)
    model = surrogate.fit(rng.random((20, 7)), rng.normal(size=20))
    assert call.surface(model, 0.0, {"slope": 0.0}, V) == ["sin_dato"]
    big = surrogate.fit(rng.random((200, 7)), rng.normal(size=200))
    assert call.surface(big, 0.0, {"slope": 0.0}, V) != ["sin_dato"]


if __name__ == "__main__":
    test_one_neighbour_is_no_plateau()
    test_twenty_points_in_seven_parameters_is_never_smooth()
    print("ok")
