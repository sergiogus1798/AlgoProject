#!/usr/bin/env python3
"""studies.breakage.mcRetest.model.retention from its definition: runs [2, 4, 6, -1] against an
original of 4 keep 0.75 at the median and three in four are positive; an original at zero has no
retention but still a positive share; no runs gives nothing."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.mcRetest.model.retention import retention

RUNS = np.array([2.0, 4.0, 6.0, -1.0])  # median 3, 5th percentile -0.55


def test_known_answer() -> None:
    """Median 3 over 4, percentile 5 by linear interpolation, three positives of four."""
    got = retention(RUNS, 4.0)
    assert got["ret_med"] == 0.75 and got["f_pos"] == 0.75 and got["n"] == 4
    assert np.isclose(got["ret_p5"], -0.55 / 4)


def test_original_not_positive() -> None:
    """No retention of zero or of a loss; the positive share does not need the original."""
    for original in (0.0, -3.0):
        got = retention(RUNS, original)
        assert (
            np.isnan(got["ret_med"])
            and np.isnan(got["ret_p5"])
            and got["f_pos"] == 0.75
        )


def test_no_runs() -> None:
    """Nothing to measure."""
    got = retention(np.array([]), 4.0)
    assert got["n"] == 0 and all(
        np.isnan(got[k]) for k in ("ret_med", "ret_p5", "f_pos")
    )
