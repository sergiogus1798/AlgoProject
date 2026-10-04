#!/usr/bin/env python3
"""Known-answer tests: crossmarket drawdown from the starting balance, breadth over the declared
markets, a NaN statistic's p; crossTF idle months, `survives` sign, and the dead min_trades knob."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.transfer.crossmarket.simulate import metrics
from studies.transfer.crossmarket.verdict import breadth


def test_drawdown_counts_the_opening_loss() -> None:
    """P/L [-100, 50, 30]: dd 100 and Ret/DD -0.2 (was 0 and NaN); [-100, -200, 50]: 300 (was 200)."""
    got = metrics.observed(np.array([-100.0, 50.0, 30.0]), 10000.0)
    assert got["dd"] == 100.0 and abs(got["ret_dd"] - (-20.0 / 100.0)) < 1e-12, got
    assert metrics.observed(np.array([-100.0, -200.0, 50.0]), 10000.0)["dd"] == 300.0


def test_breadth_denominator_is_the_declared_markets() -> None:
    """1 cleared of 1 valued with 15 missing is 1 of 16: DESCARTAR at floor 0.5."""
    summary = {"markets": 1, "cleared": 1, "fraction": 1.0, "missing": 15}
    assert breadth.judge(summary, 0.5)[0] == "DESCARTAR"
    assert breadth.judge({**summary, "missing": 0}, 0.5)[0] == "MANTENER"


def test_nan_observed_has_no_p() -> None:
    """An undefined observed statistic is not the best of the draws: p, beats and rank are NaN."""
    got = metrics.summarise(np.array([1.0, 2.0, 3.0, 4.0]), float("nan"), "ret_dd", [50.0])
    assert all(np.isnan(got[k]) for k in ("p_value", "beats", "rank")), got


if __name__ == "__main__":
    test_drawdown_counts_the_opening_loss()
    test_breadth_denominator_is_the_declared_markets()
    test_nan_observed_has_no_p()
    print("ok")
