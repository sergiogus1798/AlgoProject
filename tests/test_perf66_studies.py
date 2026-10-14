"""Encargo 66 §9, piece C3: the point speed-ups of studies/ give today's numbers, with the old logic as oracle."""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core import sqxretest
from studies.optimisation.oos2Reading import inputs as oos2
from studies.readings.entryQuality import eratio
from studies.screening.analysis import tradelevel as tl

FIXTURE = Path(__file__).parent / "fixtures" / "retest.sqx"


def _old_blind(
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    span: tuple,
    window: str,
    variant: str,
    point_value: float,
) -> tuple:
    """drift_term as it was: `inside[pool == group]` per (window, hold) pair."""
    per_window, _ = tl.VARIANTS[variant]
    label = tl.calendar(trades["Open time"], window)
    inside = np.arange(len(bars))[bars.index.slice_indexer(*span)]
    pool = (
        tl.calendar(bars.index[inside], window)
        if per_window
        else np.full(len(inside), "")
    )
    mine = trades.assign(sample=label if per_window else "")
    opened, grid = bars["Open"].to_numpy(), bars.index.to_numpy()
    weight = 1.0 / np.r_[np.nan, tl.atr(bars)[:-1]]
    weight[~np.isfinite(weight)] = 0.0
    held = np.searchsorted(
        grid, trades["Close time"].to_numpy(), side="right"
    ) - np.searchsorted(grid, trades["Open time"].to_numpy(), side="right")
    keys = pd.MultiIndex.from_arrays([mine["sample"].to_numpy(), held])
    moved = {}
    for group, hold in keys.unique():
        at = inside[pool == group]
        at = at[at + hold < len(opened)]
        moved[group, hold] = (
            (opened[at + hold] - opened[at]) * weight[at]
        ).sum() / weight[at].sum()
    side = np.where(trades["Type"].astype(str) == "Sell", -1.0, 1.0)
    return (
        side
        * trades["Size"].to_numpy()
        * point_value
        * pd.Series(moved).reindex(keys).to_numpy(),
        label,
    )


def _market(n: int = 60_000, trades: int = 400, seed: int = 3) -> tuple:
    """Synthetic 30-minute bars and a random trade list over them."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=n, freq="30min")
    close = 100 + np.cumsum(rng.normal(0, 0.2, n))
    bars = pd.DataFrame(
        {
            "Open": close + rng.normal(0, 0.05, n),
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
        },
        index=idx,
    )
    at = np.sort(rng.integers(100, n - 200, trades))
    held = rng.integers(1, 30, trades)
    tr = pd.DataFrame(
        {
            "Open time": idx[at],
            "Close time": idx[at + held],
            "Type": rng.choice(["Buy", "Sell"], trades),
            "Size": rng.uniform(0.1, 2, trades),
        }
    )
    return bars, tr


@pytest.mark.parametrize("variant", ["c", "d"])
def test_drift_term_equals_old(variant: str) -> None:
    """The new drift_term is array-equal to the old per-pair logic."""
    bars, tr = _market()
    span = ("2018-06-01", "2021-12-31")
    t0 = time.time()
    want = _old_blind(tr, bars, span, "semester", variant, 10.0)
    t1 = time.time()
    got = tl.drift_term(tr, bars, span, "semester", variant, 10.0)
    t2 = time.time()
    print(f"drift_term {variant}: old {t1 - t0:.3f} s, new {t2 - t1:.3f} s")
    np.testing.assert_array_equal(got[0], want[0])
    np.testing.assert_array_equal(got[1], want[1])


def test_drift_term_group_outside_span_is_nan_like_before() -> None:
    """Groups outside the span stay NaN as in the old logic."""
    bars, tr = _market()
    span = (
        "2019-01-01",
        "2019-12-31",
    )  # most trades sit in windows the span does not hold
    want, got = (
        _old_blind(tr, bars, span, "year", "d", 1.0)[0],
        tl.drift_term(tr, bars, span, "year", "d", 1.0)[0],
    )
    assert np.isnan(want).any()
    np.testing.assert_array_equal(got, want)


def _old_matched(
    index: pd.DatetimeIndex,
    pool: np.ndarray,
    entry: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """The hour-matched draw as it was, one mask per hour."""
    hours = index.hour.to_numpy()
    picks = []
    for hour, count in zip(*np.unique(hours[entry], return_counts=True)):
        same = pool[hours[pool] == hour]
        picks.append(rng.choice(same, size=count, replace=same.size < count))
    return np.concatenate(picks)


def test_matched_equals_old_same_stream() -> None:
    """The new matched draw equals the old one on the same random stream."""
    bars, _ = _market(n=400_000)
    entry = np.sort(np.random.default_rng(1).integers(1000, 390_000, 800))
    pool = eratio.eligible(bars.index, entry, 50)
    a, b = np.random.default_rng(7), np.random.default_rng(7)
    split = eratio.by_hour(bars.index, pool, entry)
    t0 = time.time()
    want = [_old_matched(bars.index, pool, entry, a) for _ in range(20)]
    t1 = time.time()
    got = [eratio.matched(bars.index, pool, entry, b, split) for _ in range(20)]
    t2 = time.time()
    print(f"matched x20: old {t1 - t0:.3f} s, new {t2 - t1:.3f} s")
    for x, y in zip(want, got):
        np.testing.assert_array_equal(x, y)
    np.testing.assert_array_equal(
        eratio.matched(bars.index, pool, entry, np.random.default_rng(2)),
        _old_matched(bars.index, pool, entry, np.random.default_rng(2)),
    )


def test_stored_counts_what_simulations_decodes() -> None:
    """`stored` counts as many simulations as `simulations` decodes."""
    assert sqxretest.stored(FIXTURE) == int(
        sqxretest.simulations(FIXTURE)["index"].size
    )


def test_mother_trades_filters_equal_old(tmp_path: Path) -> None:
    """mother_trades keeps the same rows as the old mask filter."""
    n = 300
    rng = np.random.default_rng(0)
    t = pd.DataFrame(
        {
            "variant_id": rng.choice(["v1", "v2", "v3"], n),
            "Open time": pd.date_range("2025-01-01", periods=n, freq="h"),
            "x": rng.normal(size=n),
        }
    )
    t["Close time"] = t["Open time"] + pd.Timedelta("30min")
    t.to_parquet(tmp_path / oos2.TRADES)
    pd.DataFrame(
        {"variant_id": ["v1", "v2", "v3"], "origin": [False, True, False]}
    ).to_parquet(tmp_path / "manifest.parquet")
    span = (pd.Timestamp("2025-01-03"), pd.Timestamp("2025-01-10"))
    old = t[t["variant_id"] == "v2"]
    old = old[(old["Open time"] >= span[0]) & (old["Close time"] < span[1])]
    pd.testing.assert_frame_equal(
        oos2.mother_trades(tmp_path, span).reset_index(drop=True),
        old.reset_index(drop=True),
    )
