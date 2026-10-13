#!/usr/bin/env python3
"""Known-answer tests for the calc-engines review (2026-10-04): BH, the empirical p, the
drawdown from the starting balance and in exit order, placement support, the ATR regime
lag, ledger pooling across units, expected max at N=1, curve clones and the excess fdr."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.surface import dedupe, plateau
from arch.bootstrap import optimal_block_length

from engines.inference import excess, fdr
from engines.inference.snooping import superior
from engines.market import calibrate
from engines.nulls import inputs, kernel, model, stats, verdict
from engines.regimes import regime
from ledger import trials


def test_fdr_refuses_nan() -> None:
    """A NaN p raises instead of being named a discovery."""
    rows = [{"metric": m, "p": p} for m, p in
            (("a", 0.04), ("nan", float("nan")), ("b", 0.001), ("c", 0.9), ("d", 0.002))]
    with pytest.raises(ValueError):
        fdr.discoveries(rows)
    with pytest.raises(ValueError):
        fdr.adjusted(rows)


def test_fdr_adjusted_matches_scipy() -> None:
    """BH adjusted p equals scipy's to 1e-12 and discoveries are q <= alpha."""
    p = np.random.default_rng(7).uniform(0, 1, 48)
    rows = [{"metric": str(i), "p": float(x)} for i, x in enumerate(p)]
    q = fdr.adjusted(rows)
    assert np.allclose([q[str(i)] for i in range(48)], sps.false_discovery_control(p), atol=1e-12)
    assert fdr.discoveries(rows) == {m for m, v in q.items() if v <= 0.05}


def test_pvalue_known_answers() -> None:
    """The empirical p on hand cases: NaN seen, NaN draws, inf draws."""
    d = np.arange(10.0)
    assert np.isnan(verdict.pvalue(float("nan"), d, "sharpe"))
    assert verdict.pvalue(4.5, d, "sharpe") == pytest.approx(6 / 11, abs=1e-12)
    assert verdict.pvalue(4.5, d, "dd") == pytest.approx(6 / 11, abs=1e-12)
    # off centre the two tails differ: a high Sharpe is good, a low drawdown is good
    assert verdict.pvalue(1.5, d, "sharpe") == pytest.approx(9 / 11, abs=1e-12)
    assert verdict.pvalue(1.5, d, "dd") == pytest.approx(3 / 11, abs=1e-12)
    holes = np.r_[d, [np.nan] * 10]
    assert verdict.pvalue(4.5, holes, "sharpe") == pytest.approx(6 / 11, abs=1e-12)
    assert verdict.pvalue(4.5, np.r_[d, np.inf], "sharpe") == pytest.approx(7 / 12, abs=1e-12)


def _ladder(pnl: tuple) -> np.ndarray:
    """One run of the ladder kernel on the given P/L, priced as price steps."""
    n = len(pnl)
    out = np.empty((1, 5))
    kernel.runs(np.zeros((1, n), np.int64), np.arange(1, n + 1)[None, :], np.ones((1, n)),
                np.zeros(n + 1), np.r_[0.0, pnl], np.zeros(n), 1.0, out)
    return out[0]


@pytest.mark.parametrize("pnl,dd", [((-100.0, 50.0, 10.0), 100.0), ((10.0, -30.0, 5.0), 30.0)])
def test_drawdown_from_start(pnl: tuple, dd: float) -> None:
    """Drawdown counts the fall from the starting balance, in every implementation."""
    arr = np.array([pnl])
    assert stats.drawdown(arr)[0] == pytest.approx(dd, abs=1e-12)
    out = _ladder(pnl)
    assert out[4] == pytest.approx(dd, abs=1e-12)
    ref = stats.measure(arr, list(kernel.NAMES))
    for i, name in enumerate(kernel.NAMES):
        assert out[i] == pytest.approx(ref[name][0], abs=1e-9)
    if pnl[0] < 0:
        assert out[3] == pytest.approx(-0.4, abs=1e-12)


def test_drawdown_reads_exit_order() -> None:
    """Columns P/L (-60, +100, -60) but exits fall in time as +100, -60, -60: dd 120, run 2."""
    out = np.empty((1, 5))
    kernel.runs(np.array([[1, 0, 2]]), np.ones((1, 3), np.int64), np.ones((1, 3)), np.zeros(4),
                np.array([0.0, 100.0, -60.0, -60.0]), np.zeros(3), 1.0, out)
    assert out[0, 4] == pytest.approx(120.0, abs=1e-12)
    # unequal holds: entered as +100, -60, -60 (dd 120) but closed as -60, +100, -60 (dd 60)
    kernel.runs(np.array([[0, 1, 2]]), np.array([[3, 1, 2]]), np.ones((1, 3)), np.zeros(5),
                np.array([0.0, 0.0, -60.0, 100.0, -60.0]), np.zeros(3), 1.0, out)
    assert out[0, 4] == pytest.approx(60.0, abs=1e-12)


def test_on_grid_enters_on_its_own_bar() -> None:
    """A trade opened at a bar's open time sits on that bar, not on the next one."""
    index = pd.date_range("2024-01-01", periods=10, freq="h")
    trades = pd.DataFrame({"Open time": index[[2, 5]], "Close time": index[[4, 6]], "Size": 1.0})
    located = inputs.on_grid(trades, index, 5)
    assert (list(located["entry"]), list(located["hold"])) == ([2, 5], [2, 1])


def test_convention_picks_the_one_that_reconciles() -> None:
    """Trades priced open to open are read as open-open, at correlation 1 and no gap."""
    rng = np.random.default_rng(5)
    frame = pd.DataFrame({"Open": 100 + rng.normal(0, 1, 300).cumsum()})
    frame["Close"] = frame["Open"] + rng.normal(0, 1, 300)
    entry = np.arange(0, 280, 7)
    located = {"entry": entry, "exit": entry + 5, "size": np.ones(entry.size)}
    cost = np.full(entry.size, 0.5)
    move = frame["Open"].to_numpy()[located["exit"]] - frame["Open"].to_numpy()[entry]
    got = calibrate.convention(pd.DataFrame({"Profit/Loss": 10.0 * move - cost}), frame, located, 10.0, cost)
    assert got["fill"] == "open-open"
    assert got["corr"] == pytest.approx(1.0, abs=1e-9) and got["median_gap"] < 1e-9


def test_place_reaches_last_bar() -> None:
    """Entries cover 0..7 for hold 3 in window (0, 10), uniformly."""
    loc = {"window": (0, 10), "hold": np.array([3]), "size": np.array([1.0])}
    e = model.timing(loc, 200000, np.random.default_rng(1))["entries"].ravel()
    assert e.max() == 7
    counts = np.bincount(e, minlength=8)
    assert sps.chisquare(counts).pvalue > 0.001


def test_atr_regime_is_lagged() -> None:
    """The ATR of day D is the close of D-1: the spike day shows 2.0."""
    idx = pd.date_range("2024-01-01", periods=40, freq="1D")
    day = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0}, index=idx)
    day.loc[idx[30], ["High", "Low"]] = [120.0, 80.0]
    vol = regime.atr(day, {"atr_period": 14})["vol"]
    assert vol[idx[30]] == pytest.approx(2.0, abs=1e-9)
    assert vol[idx[31]] == pytest.approx(4.7142857, abs=1e-6)


def _frame(*rows: tuple) -> pd.DataFrame:
    """A ledger frame with the columns accumulated reads."""
    return pd.DataFrame(rows, columns=["n_scored", "sharpe_mean", "sharpe_std", "score_unit"])


def test_accumulated_ignores_non_sharpe_units() -> None:
    """p_pass rows add to N but not to sigma; annualised is converted."""
    rng = np.random.default_rng(3)
    a, b = rng.normal(0.01, 0.05, 100), rng.normal(0.0, 0.05, 40)
    frame = _frame((100, a.mean(), a.std(ddof=1), "per_period"),
                   (40, b.mean(), b.std(ddof=1) * np.sqrt(252), "annualised"),
                   (5000, 0.4, 0.2, "p_pass"))
    frame.loc[1, "sharpe_mean"] = b.mean() * np.sqrt(252)
    got = trials.accumulated(frame)
    assert got["n"] == 5140
    assert got["sigma"] == pytest.approx(np.r_[a, b].std(ddof=1), abs=1e-9)


def test_accumulated_single_candidate_search() -> None:
    """A one-candidate search leaves sigma finite and exact."""
    rng = np.random.default_rng(5)
    a = rng.normal(0.0, 0.05, 100)
    frame = _frame((100, a.mean(), a.std(ddof=1), "per_period"), (1, 0.3, float("nan"), "per_period"))
    got = trials.accumulated(frame)
    assert got["sigma"] == pytest.approx(np.r_[a, 0.3].std(ddof=1), abs=1e-9)


def test_expected_max_one_trial() -> None:
    """The expected maximum of one draw is 0 and the DSR stays finite."""
    assert plateau.expected_max_sharpe(0.05, 1) == 0.0
    assert np.isfinite(plateau.deflated_sharpe(-0.5, 0.05, 1, 100, 0.0, 3.0)["benchmark"])
    assert plateau.deflated_sharpe(-0.5, 0.05, 1, 100, 0.0, 3.0)["dsr"] < 0.5


def test_curve_duplicates_reads_dates() -> None:
    """Equal values on other dates are not clones; an exact copy is."""
    v = [0.0, 1.0, 3.0]
    s1 = pd.Series(v, index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]))
    s2 = pd.Series(v, index=pd.to_datetime(["2021-06-01", "2021-06-02", "2021-06-03"]))
    assert dedupe.curve_duplicates({"a": s1, "b": s2}).to_dict() == {"a": False, "b": False}
    assert dedupe.curve_duplicates({"a": s1, "b": s1.copy()}).to_dict() == {"a": False, "b": True}


def test_excess_fdr_is_a_rate() -> None:
    """The fdr is capped at 1."""
    p = np.r_[0.01, np.linspace(0.2, 1, 99)]
    got = excess.excess(p, 0.05)
    assert got["fdr"] == 1.0
    assert got["excess"] == pytest.approx(-4.0, abs=1e-12)


def test_touched_reads_the_last_bar() -> None:
    """A stop reached only on the last bar of the trade's life is a touch, at that offset."""
    low, high = np.array([10.0, 10.0, 10.0, 4.0]), np.full(4, 11.0)
    offset, on_stop, on_target = kernel.touched(np.array([0]), np.array([3]), low, high,
                                                np.array([5.0]), np.array([20.0]))
    assert (offset[0], bool(on_stop[0]), bool(on_target[0])) == (3, True, False)


def test_distrust_flags_a_p_on_the_floor() -> None:
    """A p equal to the smallest observable one is saturated, not measured."""
    cfg = {"verdict": {"min_trades": 1}, "nulls": {"draws": 999}}
    kept = {"checks": {"corr": 1.0}, "levels": {}}
    said = verdict.distrust(kept, {"net": 1 / 1000, "dd": 0.5}, 100, cfg)
    assert any(line.startswith("P SATURADO en net:") for line in said)


def test_block_length_is_the_median_column() -> None:
    """One persistent column among noise does not set the block of the whole panel."""
    rng = np.random.default_rng(11)
    panel = pd.DataFrame(rng.normal(0, 1, (1500, 5)))
    for i in range(1, 1500):
        panel.iloc[i, 0] += 0.9 * panel.iloc[i - 1, 0]
    lengths = optimal_block_length(panel)["stationary"]
    assert superior.block_length(panel) == max(1, round(float(lengths.median())))
    assert superior.block_length(panel) < lengths.max() - 5


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
