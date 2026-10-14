#!/usr/bin/env python3
"""studies.breakage.mcRetest.model.place from its definition: an original at the median of its
re-runs reads percentile 50 and no gap; one above every re-run reads 100; the gap is the
median's distance as a share of the original and in IQRs; a task that moved nothing has no
IQR distance; an original near zero has no percentage."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.mcRetest.model.place import place

SIMS = np.arange(1.0, 102.0)  # 1..101: median 51, quartiles 26 and 76, IQR 50


def test_original_at_the_median() -> None:
    """Percentile 50, no gap, and the grid's own 5–95 in IQRs."""
    got = place(SIMS, 51.0, 0.25)
    assert got["percentile"] == 50.0 and got["gap_pct"] == 0.0 and got["gap_iqr"] == 0.0
    assert np.allclose(got["own"], [-0.9, 0.9])


def test_original_no_rerun_reached() -> None:
    """Percentile 100 and the gap in both units."""
    got = place(SIMS, 151.0, 0.25)
    assert got["percentile"] == 100.0
    assert np.isclose(got["gap_pct"], 100 * (51 - 151) / 151) and got["gap_iqr"] == 2.0


def test_task_that_moved_nothing() -> None:
    """No spread: no IQR distance, the percentage still defined."""
    got = place(np.full(200, 7.0), 7.0, 0.25)
    assert got["percentile"] == 50.0 and got["gap_pct"] == 0.0
    assert got["gap_iqr"] is None and got["own"] is None


def test_original_near_zero_has_no_percentage() -> None:
    """Under the floor the percentage is missing, the IQR distance is not."""
    got = place(SIMS, 5.0, 0.25)  # 5 < 0.25 × 50
    assert got["gap_pct"] is None and np.isclose(got["gap_iqr"], -0.92)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
