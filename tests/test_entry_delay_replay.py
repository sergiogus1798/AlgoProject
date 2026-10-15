#!/usr/bin/env python3
"""entryQuality delay of a stop: tier 2 replays the trade, and a stop outside a harvest is refused."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.entryQuality import delay, inputs  # noqa: E402

COSTS = {
    "point_value": 1.0,
    "spread": 0.0,
    "slippage": 0.0,
    "tick_size": 0.01,
    "tick_step": None,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "commission": 0.0,
    "commission_method": "SizeBased",
    "rounds": True,
    "triple": 2,
    "rollover": 0,
}


def test_a_delayed_long_whose_stop_moves_gives_up_what_the_walk_says() -> None:
    """Flat bars at 100, ATR 1, stop 2 ATR (level 98); bar 33 dips to 97. SQX's own trade made 0 (it
    is a fixture); entered one bar late it is stopped at 98: 2 given up."""
    n = 60
    bars = pd.DataFrame(
        {"Open": 100.0, "High": 100.5, "Low": 99.5, "Close": 100.0},
        index=pd.date_range("2024-01-01", periods=n, freq="30min"),
    )
    bars.iloc[33, bars.columns.get_loc("Low")] = 97.0
    rows = pd.DataFrame(
        {
            "enter": [30],
            "leave": [40],
            "Close type": ["Exit Signal"],
            "offset": [0.0],
            "side": [1.0],
            "coef": [2.0],
            "tick": [0.01],
            "cap": [10],
            "Size": [1.0],
            "Open price": [100.0],
            "Close price": [100.0],
            "Profit/Loss": [0.0],
        }
    )
    got = delay.replayed(bars, rows, COSTS, [1], False)
    assert got.loc[1, "entregado"] == pytest.approx(2.0)  # stopped at 98 instead of 0
    assert got.loc[1, "descartadas"] == 0


def test_stops_in_a_plain_export_are_refused(tmp_path: Path) -> None:
    """A tier 1 delay would keep the stop where it was: no harvest, no number."""
    f = tmp_path / "trades.parquet"
    pd.DataFrame({"Close type": ["SL", "Exit Signal"]}).to_parquet(f)
    with pytest.raises(ValueError, match="Stop_p90"):
        inputs.stopped(f)
    pd.DataFrame({"Close type": ["Exit Signal"]}).to_parquet(f)
    assert inputs.stopped(f) is None
