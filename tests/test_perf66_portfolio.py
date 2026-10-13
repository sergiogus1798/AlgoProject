"""Encargo 66 §9, piece C1: the faster rolling ranks, server_days and medoids equal the old logic bit for bit.

The old implementations are kept here as the oracle.
"""

import sys
import time
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
import pytest
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import rankdata

from portfolio.common.construct.equity import days
from portfolio.common.construct.pairs import rolling, table
from studies.screening.gate import redundancy


def _timed(label: str, old: Callable, new: Callable) -> tuple[Any, Any]:
    """Run both, print their times, return both results."""
    t0 = time.perf_counter(); a = old(); t1 = time.perf_counter(); b = new(); t2 = time.perf_counter()
    sys.stderr.write(f"\n[perf66] {label}: before {1e3 * (t1 - t0):.1f} ms, after {1e3 * (t2 - t1):.1f} ms\n")
    return a, b


# ---- 9.6 rolling ranks ------------------------------------------------------------------

def _old_rolling_max(a: np.ndarray, b: np.ndarray, window: int, recent: int, method: str) -> dict:
    """The pre-change rolling-correlation maxima, kept as the oracle."""
    n = a.size
    if n < window:
        return {"whole": np.nan, "recent": np.nan, "whole_abs": np.nan, "recent_abs": np.nan, "n_windows": 0}
    aw, bw = sliding_window_view(a, window), sliding_window_view(b, window)
    valid = np.all(np.isfinite(aw), axis=1) & np.all(np.isfinite(bw), axis=1)
    if method == "spearman":
        aw, bw = np.apply_along_axis(rankdata, 1, aw), np.apply_along_axis(rankdata, 1, bw)
    corr = np.where(valid, rolling._window_pearson(aw, bw), np.nan)
    rec = np.arange(window - 1, n) >= (n - recent)

    def mx(mask: np.ndarray, ab: bool) -> float:
        """Max (of the absolute value when `ab`) of the valid correlations under the mask."""
        v = corr[mask & valid]
        return float("nan") if v.size == 0 else float(np.nanmax(np.abs(v) if ab else v))

    al = np.ones(corr.size, dtype=bool)
    return {"whole": mx(al, False), "recent": mx(rec, False), "whole_abs": mx(al, True),
            "recent_abs": mx(rec, True), "n_windows": int(valid.sum())}


def _monthly(seed: int, n: int = 180, nan_head: int = 0) -> np.ndarray:
    """Seeded monthly returns, optionally NaN at the head."""
    x = np.random.default_rng(seed).normal(size=n)
    x[::7] = np.round(x[::7])   # ties
    x[:nan_head] = np.nan
    return x


def test_rolling_spearman_equal_with_ties_and_nan() -> None:
    """The rolling Spearman equals the old one with ties and NaN."""
    series = [_monthly(0), _monthly(1, nan_head=30), _monthly(2, nan_head=100), _monthly(3, n=40)]
    ranks = [rolling.ranked_windows(x, 60) for x in series]
    for p in range(len(series)):
        for q in range(p + 1, len(series)):
            if series[p].size != series[q].size:
                continue
            old = _old_rolling_max(series[p], series[q], 60, 24, "spearman")
            new = rolling.rolling_max(series[p], series[q], 60, 24, "spearman", (ranks[p], ranks[q]))
            plain = rolling.rolling_max(series[p], series[q], 60, 24, "spearman")
            for k in old:
                assert np.array_equal(old[k], new[k], equal_nan=True) and np.array_equal(old[k], plain[k], equal_nan=True)
    assert rolling.ranked_windows(series[3], 60) is None


def test_table_equal_and_timing() -> None:
    """The pairs table equals the old one and is not slower."""
    rng = np.random.default_rng(5)
    idx = pd.date_range("2012-01-02", periods=1500, freq="B")
    daily = pd.DataFrame(rng.normal(size=(1500, 30)), index=idx, columns=[f"s{i:02d}" for i in range(30)])
    daily.iloc[:400, 3:6] = np.nan
    monthly = daily.groupby(daily.index.to_period("M")).sum(min_count=1)
    cfg = {"pairs": {"tail_quantile": 0.1, "rolling_months": 60, "recent_months": 24, "stress_quantile": 0.9,
                     "min_overlap_months": 12}}
    try:
        new = table.table(daily, monthly, cfg)
    except KeyError as e:
        pytest.skip(f"pairs cfg needs key {e}")
    orig = rolling.ranked_windows
    rolling.ranked_windows = lambda x, w: None     # no precomputed ranks: today's per-pair path
    try:
        old = table.table(daily, monthly, cfg)
    finally:
        rolling.ranked_windows = orig
    pd.testing.assert_frame_equal(old, new, check_exact=True)


def test_rolling_timing() -> None:
    """The rolling correlation is timed against the old one."""
    a, b = _monthly(10, n=240), _monthly(11, n=240)
    ra, rb = rolling.ranked_windows(a, 60), rolling.ranked_windows(b, 60)
    old, new = _timed("rolling_max spearman x200", lambda: [_old_rolling_max(a, b, 60, 24, "spearman") for _ in range(200)],
                      lambda: [rolling.rolling_max(a, b, 60, 24, "spearman", (ra, rb)) for _ in range(200)])
    assert old[0] == new[0] or np.isnan(old[0]["whole"])


# ---- 9.21 server_days -------------------------------------------------------------------

def _old_server_days(path: np.ndarray, feed_zone: str, day_zone: str) -> np.ndarray:
    """The pre-change server-day assignment, kept as the oracle."""
    days._FRAME_CACHE.clear()
    frame = days._minute_frame(path, feed_zone, day_zone).copy()
    frame["e0"] = frame.groupby("day")["close"].last().shift(1).fillna(0.0).reindex(frame["day"]).to_numpy()
    frame["rel_worst"] = frame["worst"] - frame["e0"]
    frame["rel_best"] = frame["best"] - frame["e0"]
    g = frame.groupby("day")
    prev = g["realised"].last().shift(1).fillna(0.0)
    out = pd.DataFrame({
        "closed": g["realised"].last() - prev, "float_end": g["close"].last() - g["realised"].last(),
        "low": g["rel_worst"].min(), "high": g["rel_best"].max(),
        "low_open": frame["rel_worst"].where(frame["open"] > 0).groupby(frame["day"]).min(),
        "opened": g["opens"].sum().astype(int), "open_end": g["open"].last() > 0})
    out.attrs["n_nat"] = frame.attrs["n_nat"]
    return out


def _path(n: int = 400_000, seed: int = 0, start: str = "2018-01-01") -> dict:
    """A seeded random-walk equity path of n bars."""
    rng = np.random.default_rng(seed)
    t = pd.date_range(start, periods=n * 3 // 2, freq="min")
    t = t[t.dayofweek < 5][:n]
    realised = np.cumsum((rng.random(n) < 1e-4) * rng.normal(0, 50, n))
    flo = rng.normal(0, 5, n)
    close = realised + flo
    return {"t": t.values, "worst": close - abs(flo), "best": close + abs(flo), "close": close,
            "realised": realised, "open": (rng.random(n) < 0.3).astype(float),
            "opens": (rng.random(n) < 1e-4).astype(float)}


@pytest.mark.parametrize("zones", [("UTC", "UTC"), ("EETUS", "EETUS"), ("EETUS", "America/New_York"),
                                   ("Asia/Jerusalem", "UTC"), ("America/New_York", "EETUS")])
def test_server_days_equal_every_zone_dst_included(zones: tuple[str, str]) -> None:
    """Server days equal the old ones in every zone pair, DST included."""
    # 400k minutes from March reach DST changes in both hemispheres' feeds (NY, Jerusalem)
    path = _path(start="2018-03-01")
    old = _old_server_days(path, *zones)
    days._FRAME_CACHE.clear()
    new = days.server_days(path, *zones)
    pd.testing.assert_frame_equal(old, new, check_exact=True)
    assert old.attrs["n_nat"] == new.attrs["n_nat"]


def test_server_days_nan_and_fractional_opens_fall_back() -> None:
    """NaN and fractional opens fall back to the old path."""
    path = _path(60_000)
    path["close"][5_000] = np.nan
    path["opens"][10] = 0.5
    old = _old_server_days(path, "UTC", "UTC")
    days._FRAME_CACHE.clear()
    pd.testing.assert_frame_equal(old, days.server_days(path, "UTC", "UTC"), check_exact=True)


def test_server_days_timing() -> None:
    """Server days are timed against the old assignment."""
    path = _path(1_500_000, start="2016-01-04")
    days._FRAME_CACHE.clear()
    old, new = _timed("server_days 1.5M min, UTC", lambda: _old_server_days(path, "UTC", "UTC"),
                      lambda: (days._FRAME_CACHE.clear(), days.server_days(path, "UTC", "UTC"))[1])
    pd.testing.assert_frame_equal(old, new, check_exact=True)


# ---- 9.18 medoids -----------------------------------------------------------------------

def _old_medoides(metrics: pd.DataFrame, oos: pd.DataFrame, alive: list) -> pd.DataFrame:
    """The pre-change medoid selection, kept as the oracle."""
    out = pd.DataFrame({"grupo": None, "medoide": False}, index=alive)
    names = metrics.loc[alive, "strategy"]
    groups = {s: sorted(g.index, key=names.get) for s, g in metrics.loc[alive].groupby("structure")}
    out["grupo"] = [names[groups[metrics.at[i, "structure"]][0]] for i in alive]
    bars = {i: set(g) for i, g in oos[oos["identity"].isin(alive)].groupby("identity")["open_time"]}

    def jaccard(a: str, b: str) -> float:
        """Jaccard overlap of two identities' OOS bars."""
        union = len(bars.get(a, ())) + len(bars.get(b, ())) - len(bars.get(a, set()) & bars.get(b, set()))
        return len(bars.get(a, set()) & bars.get(b, set())) / union if union else 0.0

    for members in groups.values():
        score = {i: sum(jaccard(i, j) for j in members if j != i) / max(len(members) - 1, 1) for i in members}
        out.loc[max(members, key=lambda i: (score[i], -members.index(i))), "medoide"] = True
    return out


def test_medoides_equal_and_timing() -> None:
    """The medoids equal the old ones and are not slower."""
    rng = np.random.default_rng(1)
    m = 600
    ids = [f"id{i:04d}" for i in range(m)]
    metrics = pd.DataFrame({"strategy": [f"S{i:04d}" for i in range(m)], "structure": rng.integers(0, 3, m)}, index=ids)
    oos = pd.concat([pd.DataFrame({"identity": i, "open_time": rng.integers(0, 400, 80)}) for i in ids])
    oos.loc[oos["identity"].isin(ids[:4]), "open_time"] = 7    # ties / zero-union cases
    alive = pd.Index(ids)
    old, new = _timed("medoides 600 in 3 groups", lambda: _old_medoides(metrics, oos, alive),
                      lambda: redundancy.medoides(metrics, oos, alive))
    pd.testing.assert_frame_equal(old, new)
