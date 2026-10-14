#!/usr/bin/env python3
"""A constant ordering gives no Kendall tau: it is not «measurable» (encargo 68 D22)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.mcRetest.verdict import evidence

CFG = {"evidence": {"ranks_min_strategies": 5}}
NAMES = list("abcdefg")


def test_constant_list_is_not_measurable() -> None:
    """Every stressed value equal: tau is NaN, so the answer is a refusal that says why."""
    got = evidence.rank_stability(
        {n: float(i) for i, n in enumerate(NAMES)}, {n: 1.0 for n in NAMES}, CFG
    )
    assert got["measurable"] is False and got["constant"] is True


def test_varied_lists_have_a_tau() -> None:
    """Same order twice: tau is 1."""
    got = evidence.rank_stability(
        {n: float(i) for i, n in enumerate(NAMES)},
        {n: float(i) * 2 for i, n in enumerate(NAMES)},
        CFG,
    )
    assert got["measurable"] is True and abs(got["tau"] - 1.0) < 1e-12


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
