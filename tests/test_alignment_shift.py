#!/usr/bin/env python3
"""One-bar-shift cases for the aligners: a spike at bar i must not show in bar i's own decision (encargo 68 F22)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.nulls import inputs
from studies.research.marketProfile import higher, series
from studies.research.marketProfile.measure import trades


def test_closed_reads_the_day_before() -> None:
    """A spike on day 1 shows from day 2's bars on; day 1's own bars and day 0's never see it."""
    values = np.array([0.0, 100.0, 0.0])
    got = higher.closed(values, {"day": np.array([0, 0, 1, 1, 2, 2])})
    assert (
        np.isnan(got[:2]).all()
        and list(got[2:4]) == [0.0, 0.0]
        and list(got[4:]) == [100.0, 100.0]
    )


def test_lag_is_the_previous_bar() -> None:
    """Element i is bar i-1's value: a spike at i first appears at i+1."""
    a = np.array([1.0, 2.0, 99.0, 4.0])
    got = series._lag(a)
    assert np.isnan(got[0]) and list(got[1:]) == [1.0, 2.0, 99.0] and got[2] != 99.0


def test_after_enters_on_the_next_bar() -> None:
    """A signal on bar 2 enters at bar 3 and leaves `hold` bars later, never on its own bar."""
    mask = np.zeros(10, dtype=bool)
    mask[2] = True
    entry, leave = trades.after(mask, 3)
    assert list(entry) == [3] and list(leave) == [6]


def test_on_grid_puts_an_off_grid_stamp_on_the_next_bar() -> None:
    """Pinned, not endorsed: a 02:30 stamp on an hourly grid falls on bar 3 (reprice.located's own bar is 2)."""
    index = pd.date_range("2024-01-01", periods=10, freq="h")
    frame = pd.DataFrame(
        {
            "Open time": [index[2] + pd.Timedelta("30min")],
            "Close time": [index[5]],
            "Size": 1.0,
        }
    )
    got = inputs.on_grid(frame, index, 10)
    assert list(got["entry"]) == [3] and list(got["hold"]) == [2]


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
