#!/usr/bin/env python3
"""mcRetest's footprint benchmark (OPEN.md #71): the same law-of-total-variance recipe the
portfolio Monte Carlo and crossmarket use (`core.significance.footprint`), computed from a
strategy's own harvested trades and its window's daily bars, and run.benchmarks()'s
per-strategy dict built on top of it. Fixed 2026-09-29: the version this replaced weighted the
window's whole move by each trade's share of it, with no market noise around that move."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.mcRetest import run as study
from studies.breakage.mcRetest.verdict import evidence


def day() -> pd.DataFrame:
    """Four daily candles: diffs [0, 5, 5], a known mean and std."""
    return pd.DataFrame({"Close": [100.0, 100.0, 105.0, 110.0]},
                        index=pd.date_range("2020-01-01", periods=4, freq="D"))


def trades() -> pd.DataFrame:
    """Two trades of one strategy, one long and one short, each holding a known number of
    days -- long/short both exercised, since mcRetest (unlike crossmarket) is not long-only."""
    return pd.DataFrame({
        "strategy": ["A", "A"],
        "Type": ["Buy", "Sell"],
        "Open time": pd.to_datetime(["2020-01-01 00:00", "2020-01-02 12:00"]),
        "Close time": pd.to_datetime(["2020-01-02 00:00", "2020-01-03 00:00"]),
        "Size": [1.0, 2.0],
        "cost": [0.5, 1.0]})


def test_footprint_matches_hand_computation() -> None:
    """mean_i = d*mu*h*s*pv - c, var_i = sigma**2*h*(s*pv)**2, then the law of total variance
    -- worked out by hand against `day()`/`trades()`, with one long and one short trade."""
    d, t, point_value = day(), trades(), 3.0
    diffs = d["Close"].diff().dropna().to_numpy()
    mu, sigma = diffs.mean(), diffs.std(ddof=1)
    hold = np.array([1.0, 0.5])                 # (Close - Open) in days
    direction = np.array([1.0, -1.0])            # Buy, Sell
    size = t["Size"].to_numpy()
    cost = t["cost"].to_numpy()
    mean_i = direction * mu * hold * size * point_value - cost
    var_i = sigma ** 2 * hold * (size * point_value) ** 2
    want = mean_i.mean() / np.sqrt(var_i.mean() + mean_i.var(ddof=1))
    got = evidence.footprint(t, d, point_value)
    assert abs(got - want) < 1e-9


def test_benchmarks_reads_none_as_no_footprint() -> None:
    """An ingest written before 2026-09-29 (OPEN.md #71) carries no trades or asset; the
    battery reads that as "nothing to benchmark against", not a crash."""
    assert study.benchmarks(None, None) == {}
    assert study.benchmarks(pd.DataFrame(columns=trades().columns), {"feed": "x",
                                                                     "point_value": 1.0}) == {}


def test_benchmarks_groups_by_strategy() -> None:
    """One benchmark per strategy, `core.barstore.read()` called once and sliced to each
    strategy's own window rather than the whole feed's history."""
    calls = []

    def fake_read(feed: str, timeframe: str) -> pd.DataFrame:
        """Stand in for core.barstore.read(): always the same four candles, calls recorded."""
        calls.append((feed, timeframe))
        return day()

    real_read, study.barstore.read = study.barstore.read, fake_read
    try:
        two = pd.concat([trades(), trades().assign(strategy="B")], ignore_index=True)
        got = study.benchmarks(two, {"feed": "USDJPY_M1", "point_value": 3.0})
    finally:
        study.barstore.read = real_read
    assert set(got) == {"A", "B"}
    assert abs(got["A"] - got["B"]) < 1e-12          # same trades, same benchmark
    assert calls == [("USDJPY_M1", "D1")]


if __name__ == "__main__":
    test_footprint_matches_hand_computation()
    test_benchmarks_reads_none_as_no_footprint()
    test_benchmarks_groups_by_strategy()
    print("ok")
