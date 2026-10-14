#!/usr/bin/env python3
"""A mother whose excess is zero up to float noise is flat, not a huge Sharpe (encargo 68 D22)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_blindjoint as base
from studies.closing.blindJoint import measure


def test_near_flat_excess_is_flat() -> None:
    """m0's benchmark equals her day to 1e-14: she is kept out of the test, like an exact zero."""
    data = base.market(1, None)
    noise = np.random.default_rng(0).normal(0, 1e-14, len(data["panel"]))
    data["benchmark"]["m0"] = data["panel"]["m0"] - noise
    passing = base.mothers({f"m{i}": ["pass"] * 4 for i in range(base.K)})
    got = measure.run({"population": passing, **data}, base.CFG)
    assert got["flat"] == ["m0"]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
