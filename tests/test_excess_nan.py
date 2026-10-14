#!/usr/bin/env python3
"""NaN p-values are left out of the family's n, and counted apart (encargo 68 D22)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.inference import excess


def test_nan_p_does_not_inflate_n() -> None:
    """Ten measurable tests plus five NaN: n is 10, unmeasured 5, expected_all_null from 10."""
    p = np.array([0.01, 0.02, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.4, 0.3] + [np.nan] * 5)
    got = excess.excess(p, 0.05)
    assert got["n"] == 10 and got["unmeasured"] == 5 and got["observed"] == 2
    assert got["expected_all_null"] == 0.5


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
