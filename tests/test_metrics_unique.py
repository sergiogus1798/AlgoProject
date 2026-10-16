#!/usr/bin/env python3
"""Known-answer test: core.metrics is the one Sharpe, drawdown and profit factor, and the fast forms that stay obey it."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import metrics  # noqa: E402
from engines.nulls import kernel, stats  # noqa: E402
from mt5.verify import judge  # noqa: E402
from sqx.variants import united  # noqa: E402
from ui.daemon.databank import segments  # noqa: E402
from studies.breakage.mcRetest.model import drawdown as mcdd  # noqa: E402
from studies.optimisation.cscv.measure import cscv  # noqa: E402

CURVES = {
    "normal": np.array([10.0, -5, 20, -15, 8, -3, 12]),
    "flat": np.array([4.0, 4, 4, 4]),
    "noloss": np.array([3.0, 0, 5, 2]),
    "empty": np.array([]),
}
# What every copy deleted on 2026-10-16 gave on the normal curve, run before the deletion:
# core.significance.annual_sharpe, engines.nulls.stats, three portfolio _sharpe, sqx united,
# mt5 judge.max_dd, the two ui drawdowns, gate decay.sharpe and resample.max_drawdown.
FROZEN = {
    "weekday_sharpe": 5.10589842,
    "per_trade_sharpe": 0.3216413676,
    "dd_money": 15.0,
    "profit_factor": 2.1739130435,
    "dd_pct_1000": 1.4634146341,
}


def days(n: int) -> np.ndarray:
    """n consecutive weekdays from Monday 2024-01-01."""
    return pd.bdate_range("2024-01-01", periods=n).to_numpy()


def test_the_normal_curve_gives_what_every_old_copy_gave() -> None:
    """The one definition reproduces the deleted copies where they all agreed."""
    p = CURVES["normal"]
    got = {
        "weekday_sharpe": metrics.sharpe(metrics.weekday_pnl(p, days(p.size)), 252),
        "per_trade_sharpe": metrics.sharpe(p, 1),
        "dd_money": metrics.dd_money(metrics.cumulative(p)),
        "profit_factor": metrics.profit_factor(p),
        "dd_pct_1000": metrics.dd_pct(1000 + np.cumsum(p), 1000.0),
    }
    for k, want in FROZEN.items():
        assert got[k] == pytest.approx(want, abs=1e-9), k


def test_edge_rules() -> None:
    """Flat: Sharpe NaN; no loss: PF inf; empty: Sharpe and PF NaN, drawdown 0."""
    flat, noloss, empty = CURVES["flat"], CURVES["noloss"], CURVES["empty"]
    assert np.isnan(metrics.sharpe(flat, 252)) and np.isnan(metrics.sharpe(empty, 252))
    assert np.isnan(metrics.sharpe(np.array([1.0]), 1))
    assert np.isnan(metrics.sharpe(np.zeros(5), 1))
    assert metrics.profit_factor(noloss) == np.inf
    assert np.isnan(metrics.profit_factor(empty))
    assert np.isnan(metrics.profit_factor(np.zeros(3)))
    assert metrics.profit_factor(np.array([-1.0, -2])) == 0.0
    assert metrics.dd_money(metrics.cumulative(empty)) == 0.0
    assert metrics.dd_pct(np.array([]), 100.0) == 0.0
    assert [metrics.finite(v) for v in (np.inf, np.nan, 2.0)] == [None, None, 2.0]


def test_the_two_drawdowns_differ_only_in_where_the_peak_starts() -> None:
    """dd_money peaks at the curve's first value; dd_pct at the deposit, so a first loss counts."""
    curve = np.array([990.0, 1010.0, 1000.0])
    assert metrics.dd_money(curve) == 10.0
    assert metrics.dd_pct(curve, 1000.0) == pytest.approx(1.0)
    assert metrics.dd_pct(np.array([1000.0, 1020.0, 1005.0]), 1000.0) == pytest.approx(
        15 / 1020 * 100
    )


def test_weekday_pnl_counts_trading_days_only() -> None:
    """Two Mondays and a Saturday close that lands on the third Monday; the rest zeros."""
    closed = pd.to_datetime(
        ["2024-01-01 10:00", "2024-01-08 15:00", "2024-01-13 02:00"]
    )
    daily = np.array([100.0, 0, 0, 0, 0, 40.0, 0, 0, 0, 0, 60.0])
    got = metrics.sharpe(metrics.weekday_pnl(np.array([100.0, 40, 60]), closed), 252)
    assert got == pytest.approx(daily.mean() / daily.std(ddof=1) * np.sqrt(252))


def test_years_is_elapsed_days() -> None:
    """One convention, no +1."""
    assert metrics.years("2024-01-01", "2025-01-01") == 366 / 365.25


def test_axis_forms_match_the_scalar_ones() -> None:
    """Several series at once give each series' own figure."""
    x = np.random.default_rng(3).normal(0.1, 1.0, (4, 30))
    assert np.allclose(metrics.sharpe(x, 1), [metrics.sharpe(r, 1) for r in x])
    assert np.allclose(metrics.sharpe(x.T, 1, axis=0), metrics.sharpe(x, 1))
    c = metrics.cumulative(x)
    assert np.allclose(metrics.dd_money(c), [metrics.dd_money(r) for r in c])
    assert np.allclose(metrics.profit_factor(x), [metrics.profit_factor(r) for r in x])


@pytest.mark.parametrize("name", ["normal", "flat", "noloss"])
def test_the_fast_forms_that_stay_obey_the_same_rules(name: str) -> None:
    """The null's numpy and compiled forms, mcRetest's per-simulation one, CSCV, united, MT5."""
    p = CURVES[name]
    sh, dd, pf = (
        metrics.sharpe(p, 1),
        metrics.dd_money(metrics.cumulative(p)),
        metrics.profit_factor(p),
    )
    got = stats.measure(p[None], ["sharpe", "pf", "dd"])
    np.testing.assert_equal(
        [got["sharpe"][0], got["pf"][0], got["dd"][0]], [sh, pf, dd]
    )
    row = np.zeros(5)
    gain, loss = p[p > 0].sum(), -p[p < 0].sum()
    kernel._write(p, p.sum(), gain, loss, dd, row)
    np.testing.assert_allclose(row[1:3], [sh, pf], rtol=1e-12)
    n = p.size
    leave = np.arange(n, dtype=np.int64)
    scratch = (np.zeros(n + 1, np.int64), np.zeros(n, np.int64), np.zeros(n))
    assert kernel._drawdown(p, leave, *scratch) == pytest.approx(dd)
    sims = mcdd.prepare(
        {"pnl": p, "offsets": np.array([0, n]), "capital": 1000.0, "n": n}
    )
    assert mcdd.deepest(sims)[0] == pytest.approx(dd)
    assert mcdd.deepest_pct(sims)[0] == pytest.approx(
        metrics.dd_pct(1000 + np.cumsum(p), 1000.0)
    )
    frame = pd.DataFrame({"Close time": days(n), "Profit/Loss": p})
    assert judge.max_dd(frame, 1000.0) == pytest.approx(
        metrics.dd_pct(1000 + np.cumsum(p), 1000.0)
    )
    joined = united.from_curves(pd.DataFrame({"v": p}, index=days(n))).iloc[0]
    assert joined["Drawdown"] == pytest.approx(dd)
    np.testing.assert_allclose(joined["SharpeRatio"], metrics.sharpe(p, 252))
    if (
        name == "normal"
    ):  # CSCV ranks: its flat column is 0 on purpose, see its docstring
        s1, s2 = np.array([p.sum()]), np.array([np.square(p).sum()])
        assert cscv.ratio_from_sums(np.array([float(n)]), s1, s2, False)[
            0
        ] == pytest.approx(sh)


def test_window_payloads_keep_the_profit_factor_numeric() -> None:
    """No loss is None, never a string: the table sorts and formats numbers only."""
    assert segments.figures(pd.Series([3.0, 5.0]))["Profit factor"] is None
    assert segments.figures(pd.Series([3.0, -1.0]))["Profit factor"] == 3.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
