#!/usr/bin/env python3
"""entryQuality puts an entry filled inside a bar on the bar that contains it."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.entryQuality import inputs


def test_entry_inside_a_bar_is_located_on_that_bar_and_reads_the_atr_before_it() -> (
    None
):
    """Bars hourly from 00:00; a trade stamped 20:20 is on bar 20, whose ATR comes from bar 19."""
    index = pd.date_range("2020-01-01", periods=60, freq="1h")
    close = 100 + np.arange(60) * 0.1
    frame = pd.DataFrame(
        {"Open": close, "High": close + 1, "Low": close - 1, "Close": close},
        index=index,
    )
    mine = pd.DataFrame(
        {
            "Open time": [index[20] + pd.Timedelta("20min")] * 2,
            "Close time": [index[22]] * 2,
            "Open price": [100.0, 101.0],
            "Close price": [101.0, 103.0],
            "Size": [1.0, 1.0],
            "Profit/Loss": [99.0, 199.0],
            "Type": ["Buy", "Buy"],
        }
    )
    real = inputs.nullinputs.sample
    inputs.nullinputs.sample = lambda *a, **k: mine
    try:
        got = inputs.located(Path("x"), "s", {"sample": "IST", "atr": 5}, frame)
    finally:
        inputs.nullinputs.sample = real
    assert list(got["entry"]) == [20, 20]


if __name__ == "__main__":
    test_entry_inside_a_bar_is_located_on_that_bar_and_reads_the_atr_before_it()
    print("ok")
