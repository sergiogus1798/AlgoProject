#!/usr/bin/env python3
"""Known-answer test: the SPP `combinado` Sharpe is on weekdays, as SQX's and `annual_sharpe` are."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import significance
from studies.breakage.spp.model import combine


def test_sharpe_is_on_weekdays() -> None:
    """One trade per weekday for 52 weeks: mean/sd*sqrt(252) of that series (calendar days gave x0.845)."""
    days = pd.bdate_range("2024-01-01", periods=260)
    pnl = np.random.default_rng(0).normal(10, 100, days.size)
    got = combine.real_from_trades(
        pd.DataFrame({"Close time": days, "Profit/Loss": pnl})
    )
    expected = pnl.mean() / pnl.std(ddof=1) * np.sqrt(252)
    assert abs(got["SharpeRatio"] - expected) < 1e-9, (got, expected)
    assert (
        abs(got["SharpeRatio"] - significance.annual_sharpe(pnl, days.to_numpy()))
        < 1e-9
    )


if __name__ == "__main__":
    test_sharpe_is_on_weekdays()
    print("ok")
