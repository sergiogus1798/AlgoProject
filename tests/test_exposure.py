#!/usr/bin/env python3
"""studies.closing.exposure on hand-built bars and trades: which bar a position is held on,
which move it is paired with, where a trade's profit lands, and the Sharpe's annualisation."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.closing.exposure import benchmark, inputs, occupancy, one


def test_presence_pairs_each_held_bar_with_its_own_move() -> None:
    """A long held over exactly the bars 200 and 300 of a flat market that jumps by 1 on bar
    200 captured and was aligned with ~all of the movement; paired with the next bar's move
    it read 0.0001."""
    rng = np.random.default_rng(0)
    index = pd.date_range("2020-01-01", periods=600, freq="1h")
    close = 100 + np.cumsum(rng.normal(0, 1e-4, 600))
    close[200:] += 1.0
    bars = pd.DataFrame(
        {"Open": close, "High": close, "Low": close, "Close": close}, index=index
    )
    trades = pd.DataFrame(
        {
            "Open time": [index[200], index[300]],
            "Close time": [index[201], index[301]],
            "Size": [1.0, 1.0],
            "Type": ["Buy", "Buy"],
            "Balance": [1e4, 1e4],
            "Profit/Loss": [1.0, -1.0],
            "Open price": [1.0, 1.0],
            "Close price": [2.0, 1.0],
        }
    )
    got = one.measure(trades, bars, 1.0, inputs.config([]))
    assert got["captured"] > 0.9 and got["aligned"] > 0.9
    assert "verdict" not in got and "reasons" not in got and "notes" in got


def test_overlapping_lots_closing_leave_no_float_residue_in_market() -> None:
    """0.1 and 0.2 lots open together and close together: afterwards gross must read as out."""
    index = pd.date_range("2020-01-01", periods=6, freq="1h")
    t = [index[1], index[1]]
    trades = pd.DataFrame(
        {
            "Open time": t,
            "Close time": [index[3], index[3]],
            "Size": [0.1, 0.2],
            "Type": ["Buy", "Buy"],
        }
    )
    gross = occupancy.held(trades, index)["gross"]
    assert (gross[3:] > 1e-9).sum() == 0 and (gross[1:3] > 1e-9).all()


def test_entry_inside_a_bar_belongs_to_that_bar() -> None:
    """Bars at 10:00, 11:00, 12:00; a Buy filled at 10:20 and closed at 12:00 holds bars 0-1."""
    index = pd.date_range("2020-01-01 10:00", periods=3, freq="1h")
    trades = pd.DataFrame(
        {
            "Open time": [pd.Timestamp("2020-01-01 10:20")],
            "Close time": [pd.Timestamp("2020-01-01 12:00")],
            "Size": [1.0],
            "Type": ["Buy"],
        }
    )
    assert list(occupancy.held(trades, index)["gross"]) == [1.0, 1.0, 0.0]


def test_daily_keeps_the_profit_closed_before_the_first_move() -> None:
    """Trades worth 100 (closed on the first day, which has no move) and 50: all 150 land."""
    days = pd.date_range("2020-01-02", periods=4, freq="D")
    trades = pd.DataFrame(
        {
            "Close time": [days[0] + pd.Timedelta("3h"), days[2]],
            "Profit/Loss": [100.0, 50.0],
        }
    )
    assert benchmark.daily(trades, days[1:]).sum() == 150.0


if __name__ == "__main__":
    test_presence_pairs_each_held_bar_with_its_own_move()
    test_entry_inside_a_bar_belongs_to_that_bar()
    test_daily_keeps_the_profit_closed_before_the_first_move()
    print("ok")
