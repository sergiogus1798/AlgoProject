#!/usr/bin/env python3
"""Known answers for the WFM's «Contra el activo»: the daily marks of a held trade, and a
strategy that is the asset itself scoring a zero Sharpe gap, and the three calls."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.wfm.measure import benchmark

DAYS = pd.bdate_range("2024-01-01", periods=6)


def test_marks() -> None:
    """A long of 2 lots at 100, held three days, closed with costs: marks, then the rest."""
    close = pd.Series([101.0, 103.0, 102.0, 104.0, 104.0, 104.0], index=DAYS)
    trade = pd.DataFrame({"Type": ["Buy"], "Open time": [DAYS[0] + pd.Timedelta(hours=10)],
                          "Open price": [100.0], "Size": [2.0],
                          "Close time": [DAYS[3] + pd.Timedelta(hours=12)],
                          "Close price": [103.5], "Profit/Loss": [690.0]})
    got = benchmark.daily_pnl(trade, close, 100.0).to_numpy()
    # 2 lots x 100 $: +200 day 0, +400 day 1, -200 day 2, the rest (690 - 400) on exit day 3.
    assert np.allclose(got, [200, 400, -200, 290, 0, 0])


def test_asset_itself() -> None:
    """A strategy that is the asset scaled down has the asset's Sharpe and a beta of its size."""
    rng = np.random.default_rng(1)
    days = pd.bdate_range("2020-01-01", periods=600)
    close = pd.Series(1000 * np.cumprod(1 + rng.normal(0.0004, 0.01, 600)), index=days)
    pnl = close.pct_change().fillna(0.0) * 0.1 * 100_000
    got = benchmark.compare(pnl, close, 100_000.0,
                            {"n_resamples": 200, "block_days": 20, "confidence": 0.95, "seed": 0})
    assert abs(got["difference"]) < 1e-9 and abs(got["beta"] - 0.1) < 1e-9
    assert got["difference_band"][0] <= 0 <= got["difference_band"][1]
    assert benchmark.call(got) == "watch"
    assert benchmark.call(got | {"difference_band": [-1.0, -0.1]}) == "fail"
    assert benchmark.call(got | {"difference_band": [0.1, 1.0]}) == "pass"


if __name__ == "__main__":
    test_marks()
    test_asset_itself()
    print("ok")
