#!/usr/bin/env python3
"""Known answers for the gate's significance and floating-risk numbers: Lo's t on the daily
curve, the trade-level t and its drift-excess twin, and the losses in R."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.analysis import decay, floating, tradelevel


def curve(mean: float, days: int, seed: int) -> tuple[pd.Series, pd.Series]:
    """A cumulative daily curve of iid normal P&L with sd 1, and its out-of-sample days."""
    index = pd.bdate_range("2010-01-01", periods=2 * days)
    daily = pd.Series(np.random.default_rng(seed).normal(mean, 1.0, 2 * days), index=index)
    return daily.cumsum(), daily.iloc[days:]


def test_lo_t_is_the_daily_t_and_has_no_ceiling() -> None:
    """Lo (2002) on iid days: t = SR_day * sqrt(T) / sqrt(1 + SR_day**2 / 2). For a small
    Sharpe that is the plain t of the mean day; for a large one it grows past sqrt(2 * years),
    where the annualised Sharpe inside the variance term (the bug of 2026-10-02) capped it."""
    days = 1260
    for mean in (0.03, 0.08, 0.5):
        equity, after = curve(mean, days, 7)
        row = decay.diagnose(equity, after.index[0].date().isoformat(),
                             after.index[-1].date().isoformat())
        per_day = after.mean() / after.std(ddof=1)
        plain = per_day * np.sqrt(days)
        assert abs(row["t"] - plain / np.sqrt(1 + per_day ** 2 / 2)) < 1e-9
        assert abs(row["t"] - stats.ttest_1samp(after, 0.0).statistic) < 0.07 * plain
        if mean < 0.1:
            assert abs(row["t"] / plain - 1) < 0.005
    assert row["t"] > 15 > np.sqrt(2 * days / decay.YEAR)       # Sharpe ~8: the old cap was 3.16


def test_trade_t_and_its_ar1_twin() -> None:
    """`iid` is scipy's one-sample t; `ar1` shrinks it by sqrt((1 - rho) / (1 + rho)) when
    trades are positively autocorrelated and leaves it alone when rho is negative."""
    rng = np.random.default_rng(3)
    noise = rng.normal(0.0, 1.0, 400)
    sticky = np.empty(400)
    sticky[0] = noise[0]
    for i in range(1, 400):
        sticky[i] = 0.6 * sticky[i - 1] + noise[i]
    flip = np.tile([1.0, -0.8], 200) + 0.3
    trades = pd.DataFrame({"identity": ["a"] * 400 + ["b"] * 400 + ["c"] * 400,
                           "pl": np.r_[noise + 0.1, sticky + 0.1, flip]})
    got = tradelevel.t(trades, "pl")
    for name, x in (("a", noise + 0.1), ("b", sticky + 0.1), ("c", flip)):
        assert abs(got.at[name, "iid"] - stats.ttest_1samp(x, 0.0).statistic) < 1e-9
    d = sticky + 0.1 - (sticky + 0.1).mean()
    rho = (d[1:] * d[:-1]).sum() / (d * d).sum()
    assert 0.5 < rho < 0.7
    assert abs(got.at["b", "ar1"] / got.at["b", "iid"] - np.sqrt((1 - rho) / (1 + rho))) < 1e-9
    assert got.at["c", "ar1"] == got.at["c", "iid"]


def test_drift_takes_out_exactly_what_the_market_paid() -> None:
    """On a market that rises 2.0 per bar, a 1.5-lot long held 3 bars earned 3 * 2 * 1.5 * pv
    from the drift alone and a short lost the same; each sample is charged its own drift."""
    index = pd.date_range("2020-01-01", periods=48, freq="h")
    bars = pd.DataFrame({"Close": np.r_[np.arange(24) * 2.0, 46.0 - np.arange(24) * 1.0]},
                        index=index)
    move = tradelevel.mean_move(bars, {"IS": ("2020-01-01 01:00", "2020-01-01 23:00"),
                                       "OOS": ("2020-01-02 01:00", "2020-01-02 23:00")})
    assert move == {"IS": 2.0, "OOS": -1.0}
    trades = pd.DataFrame({"Open time": [index[2], index[2], index[30]],
                           "Close time": [index[5], index[5], index[34]],
                           "Type": ["Buy", "Sell", "Buy"], "Size": [1.5, 1.5, 2.0],
                           "sample": ["IS", "IS", "OOS"]})
    assert list(tradelevel.drift(trades, bars, move, 10.0)) == [90.0, -90.0, -80.0]


def test_floating_risk_in_r() -> None:
    """Hand-built: equity +500, -1500, -500, +3000 is a 2R fall from its high of 0.5R, a worst
    day of -1.5R, and with 1R = 1000 over two years a net of 0.75R a year: the fall cost
    2 / 0.75 years of net. A strategy that lost money never repays it: +inf, never NaN."""
    days = pd.bdate_range("2021-01-04", periods=4)
    daily = pd.DataFrame({"a": [500.0, -1500.0, -500.0, 3000.0],
                          "b": [-200.0, np.nan, -300.0, 100.0]}, index=days)
    trades = pd.DataFrame({"identity": ["a", "a", "b"], "Profit/Loss": [-1500.0, 3000.0, -400.0],
                           "MAE ($)": [-2200.0, -100.0, -700.0]})
    got = floating.table(daily, trades, 1000.0, 2.0)
    assert list(got.loc["a"]) == [2.0, -1.5, -2.2, 0.75, 2.0 / 0.75]
    assert list(got.loc["b"]) == [0.5, -0.3, -0.7, -0.2, np.inf]   # a fall from the start counts
    flat = pd.DataFrame({"identity": ["a"], "Profit/Loss": [0.0], "MAE ($)": [0.0]})
    assert floating.table(daily[["a"]] * 0, flat, 1000.0, 2.0).at["a", "dd_over_net_year"] == np.inf


if __name__ == "__main__":
    test_lo_t_is_the_daily_t_and_has_no_ceiling()
    test_trade_t_and_its_ar1_twin()
    test_drift_takes_out_exactly_what_the_market_paid()
    test_floating_risk_in_r()
    print("ok")
