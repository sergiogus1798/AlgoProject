#!/usr/bin/env python3
"""Encargo 66 §9 (C2): mt5.compare.pair, assetdata.load/symbol_for and feed scale.by_week equal their old logic."""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata
from engines.market.feed import scale
from mt5 import compare


def old_pair(sqx: pd.DataFrame, mt5: pd.DataFrame, tolerance_min: float) -> pd.DataFrame:
    """Today's pair(), verbatim: the oracle."""
    free = mt5.reset_index(drop=True).copy()
    free["taken"] = False
    rows = []
    for values in sqx.itertuples(index=False, name=None):
        row = dict(zip(sqx.columns, values))
        side = free[(free["Type"] == row["Type"]) & ~free["taken"]]
        gap = (side["Open time"] - row["Open time"]).abs()
        near = gap[gap <= pd.Timedelta(minutes=tolerance_min)]
        if len(near):
            i = near.idxmin()
            free.loc[i, "taken"] = True
            row.update({f"{c}_mt5": free.loc[i, c] for c in mt5.columns})
        rows.append(row)
    out = pd.DataFrame(rows, columns=[*sqx.columns, *(f"{c}_mt5" for c in mt5.columns)])
    return out.astype({f"{c}_mt5": mt5[c].dtype for c in mt5.columns})


def frames(n: int, seed: int, grid: int) -> tuple:
    """Trades on a coarse minute grid (many ties), a few NaT, shuffled MT5 order."""
    rng = np.random.default_rng(seed)
    def one(m: int) -> pd.DataFrame:
        """One random trade frame of m rows."""
        t = pd.Timestamp("2026-09-14") + pd.to_timedelta(rng.integers(0, grid, m) * 5, unit="m")
        f = pd.DataFrame({"Type": rng.choice(["Buy", "Sell"], m), "Open time": t,
                          "Open price": rng.normal(100, 1, m), "Close time": t + pd.Timedelta(hours=2),
                          "Close price": rng.normal(100, 1, m), "Profit/Loss": rng.normal(0, 5, m)})
        f.loc[rng.random(m) < 0.02, "Open time"] = pd.NaT
        return f
    return one(n), one(n + n // 5).sample(frac=1, random_state=seed)


def test_pair_equal_with_ties() -> None:
    """The new pair() equals the old one on tied, shuffled, empty inputs."""
    for seed, grid in [(0, 40), (1, 400), (2, 3000)]:
        sqx, mt5 = frames(600, seed, grid)
        mt5.index = np.arange(len(mt5)) * 3 + 7                  # not a RangeIndex
        for tol in (0.0, 5.0, 17.5, 60.0):
            pd.testing.assert_frame_equal(compare.pair(sqx, mt5, tol), old_pair(sqx, mt5, tol))
    e = sqx.iloc[:0]
    pd.testing.assert_frame_equal(compare.pair(e, mt5, 5), old_pair(e, mt5, 5))
    pd.testing.assert_frame_equal(compare.pair(sqx, mt5.iloc[:0], 5), old_pair(sqx, mt5.iloc[:0], 5))


def test_pair_timing() -> None:
    """The new pair() is faster than the old one."""
    sqx, mt5 = frames(600, 5, 400)
    t = time.time(); old_pair(sqx, mt5, 30); a = time.time() - t
    t = time.time(); compare.pair(sqx, mt5, 30); b = time.time() - t
    print(f"\npair 600 trades: before {a:.3f} s, after {b:.4f} s")
    assert b < a


def test_load_equal_and_isolated() -> None:
    """A mutated load() result never leaks into the next load."""
    for s in assetdata.symbols():
        a = assetdata.load(s)
        a["costs"]["MUTATED"] = 1
        a["segments"]["build"]["from"] = "x"
        a["segments_default"]["MUTATED"] = 1
        b = assetdata.load(s)
        assert "MUTATED" not in b["costs"] and "MUTATED" not in b["segments_default"]
        assert b["segments"]["build"]["from"] != "x"
        assert list(b) == list(assetdata.load(s))
    t = time.time(); [assetdata.load(s) for s in assetdata.symbols()]
    print(f"\nload x{len(assetdata.symbols())}: {(time.time() - t) * 1e3:.1f} ms")


def test_symbol_for_equal_and_invalidates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """symbol_for matches the slow lookup and sees an edited card."""
    for s in assetdata.symbols():
        feed = assetdata.load(s)["sqx_symbol"]
        old = next(x for x in assetdata.symbols() if assetdata.load(x)["sqx_symbol"] == feed)
        assert assetdata.symbol_for(feed) == old
    assert assetdata.symbol_for("NO_SUCH_M1") is None
    # An edited card is seen: copy two cards into a scratch assets root and change one.
    src = assetdata.SYMBOLS
    (tmp_path / "symbols").mkdir()
    for f in list(src.glob("*.yaml"))[:2]:
        (tmp_path / "symbols" / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(assetdata, "SYMBOLS", tmp_path / "symbols")
    first = sorted((tmp_path / "symbols").glob("*.yaml"))[0]
    feed = assetdata.safe_load(first.read_text(encoding="utf-8"))["sqx_symbol"]
    assert assetdata.symbol_for(feed) == first.stem
    first.write_text(first.read_text(encoding="utf-8").replace(feed, "EDITED_M1", 1), encoding="utf-8")
    assert assetdata.symbol_for(feed) is None and assetdata.symbol_for("EDITED_M1") == first.stem
    first.unlink()
    assert assetdata.symbol_for("EDITED_M1") is None


def old_cells(r: np.ndarray, at: np.ndarray, weeks: int, min_weeks: int) -> tuple:
    """Today's by_week(), verbatim, with its pure-numpy _mad: the oracle."""
    def mad(v: np.ndarray) -> float:
        """Scaled median absolute deviation of the finite values."""
        v = v[np.isfinite(v)]
        return np.nan if not len(v) else scale.MAD_TO_SIGMA * np.median(np.abs(v - np.median(v)))
    week = at // scale.WEEK
    first = int(week[0])
    n = int(week[-1]) - first + 1
    hour = (at % scale.WEEK) // 60
    out = np.full((168, n), np.nan)
    order = np.lexsort((at, hour))
    hour_s, week_s, r_s = hour[order], week[order] - first, r[order]
    edges = np.searchsorted(hour_s, np.arange(169))
    for h in range(168):
        wk, rr = week_s[edges[h]:edges[h + 1]], r_s[edges[h]:edges[h + 1]]
        if not len(wk):
            continue
        cut = np.searchsorted(wk, np.arange(n + 1))
        for w in range(min_weeks, n):
            out[h, w] = mad(rr[cut[max(0, w - weeks)]:cut[w]])
    return out, first


def test_by_week_bit_equal() -> None:
    """scale.by_week equals the old numpy loop bit for bit."""
    yrs = 3
    n = yrs * 52 * 5 * 1440
    at = (np.arange(n) // (5 * 1440)) * 7 * 1440 + np.arange(n) % (5 * 1440)
    at = at[(np.arange(n) % 997) != 0]                           # holes; a gap of hours too
    at = at[(at // 60 % 168) != 100]                             # an hour with no bars at all
    r = np.random.default_rng(0).standard_normal(len(at)) * 1e-4
    r[np.random.default_rng(1).random(len(at)) < 0.01] = np.nan
    scale.by_week(r[:5000], at[:5000], 26, 4)                    # compile outside the timing
    t = time.time(); want = old_cells(r, at, 26, 4); a = time.time() - t
    t = time.time(); got = scale.by_week(r, at, 26, 4); b = time.time() - t
    print(f"\nby_week {yrs} y: before {a:.2f} s, after {b:.2f} s")
    assert got[1] == want[1]
    np.testing.assert_array_equal(got[0], want[0])               # bit for bit, NaN in the same places
