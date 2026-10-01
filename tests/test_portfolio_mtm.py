#!/usr/bin/env python3
"""M1 minute path, server days and M5 blocks on hand-made bars, plus the archived golden."""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import archive_dir  # noqa: E402
from core import barstore  # noqa: E402
from engines.market import calibrate  # noqa: E402
from portfolio.common.construct.equity import blocks, days, excursions, paths  # noqa: E402

POINT_VALUE = 1000.0


def _bars(start: str, periods: int, **overrides: np.ndarray) -> pd.DataFrame:
    """Flat M1 bars (High 1.10, Low 1.00, Close 1.05) for `periods` minutes from `start`."""
    idx = pd.date_range(start, periods=periods, freq="1min")
    frame = pd.DataFrame({"High": 1.10, "Low": 1.00, "Close": 1.05}, index=idx)
    for key, value in overrides.items():
        frame[key] = value
    return frame


def _trade(open_t: pd.Timestamp, close_t: pd.Timestamp, open_p: float, close_p: float,
           pnl: float, side: str = "Buy") -> pd.DataFrame:
    """One-row trades frame (schema T) with a fixed Size of 1.0 lot."""
    return pd.DataFrame({"Type": pd.Categorical([side]), "Open time": [open_t],
                          "Close time": [close_t], "Open price": [open_p],
                          "Close price": [close_p], "Size": [1.0], "Profit/Loss": [pnl]})


def check_long_across_days() -> None:
    """A long spanning three day boundaries: floating to the cent, close-day increment,
    a same-day trade, and Σ daily = Σ Profit/Loss exactly."""
    bars = _bars("2026-01-01 00:00", 3 * 24 * 60)
    trades = pd.concat([
        _trade(pd.Timestamp("2026-01-01 10:00"), pd.Timestamp("2026-01-03 10:00"), 1.00, 1.05, 50.0),
        _trade(pd.Timestamp("2026-01-02 03:00"), pd.Timestamp("2026-01-02 04:00"), 1.05, 1.00, -50.0),
    ], ignore_index=True)
    path = paths.minute_path(trades, bars, POINT_VALUE)
    d = days.server_days(path, "UTC", "UTC")
    dp = days.daily_pnl(d)

    assert abs(dp.sum() - trades["Profit/Loss"].sum()) < 1e-9, "sum daily != sum Profit/Loss"
    day2 = pd.Timestamp("2026-01-02")
    assert abs(dp[day2] - (-50.0)) < 1e-9, "same-day trade must land whole on its day"
    day3 = pd.Timestamp("2026-01-03")
    last_floating_before_close = d.loc[pd.Timestamp("2026-01-02"), "float_end"]
    assert abs(dp[day3] - (50.0 - last_floating_before_close)) < 1e-9, \
        "close-day increment must equal realised minus last floating"
    print("ok: long across three day boundaries")


def check_short_worst_is_high() -> None:
    """A short's worst floating price is the minute's High, best is the Low."""
    high = np.full(200, 1.10)
    low = np.full(200, 1.00)
    high[50], low[50] = 1.20, 0.90
    bars = _bars("2026-01-01 00:00", 200, High=high, Low=low)
    trades = _trade(bars.index[10], bars.index[100], 1.05, 1.05, 0.0, side="Sell")
    path = paths.minute_path(trades, bars, POINT_VALUE)
    assert path["worst"][40] == -150.0, "short worst must use the High wick"
    assert path["best"][40] == 150.0, "short best must use the Low wick"
    print("ok: short worst = High, best = Low")


def check_weekend_gap() -> None:
    """No bars over the weekend: the path skips it, and the daily sum still holds exactly."""
    week = pd.bdate_range("2026-01-05", periods=5, freq="B")
    idx = pd.DatetimeIndex(sorted(
        t for day in week for t in pd.date_range(day, periods=24 * 60, freq="1min")))
    bars = pd.DataFrame({"High": 1.10, "Low": 1.00, "Close": 1.05}, index=idx)
    trades = _trade(pd.Timestamp("2026-01-09 20:00"), pd.Timestamp("2026-01-12 08:00"), 1.00, 1.05, 50.0)
    path = paths.minute_path(trades, bars, POINT_VALUE)
    d = days.server_days(path, "UTC", "UTC")
    assert pd.Timestamp("2026-01-10") not in d.index and pd.Timestamp("2026-01-11") not in d.index, \
        "a weekend day with no path minute must not appear"
    assert abs(days.daily_pnl(d).sum() - 50.0) < 1e-9
    print("ok: weekend gap skipped, sum still exact")


def check_eetus_and_dst() -> None:
    """EETUS is New York + 7 h, and an hour a clock change repeats is dropped and counted."""
    idx = pd.date_range("2026-11-01 07:55", periods=20, freq="1min")   # ambiguous NY 01:xx
    bars = pd.DataFrame({"High": 1.1, "Low": 1.0, "Close": 1.05}, index=idx)
    trades = _trade(idx[0], idx[-1], 1.00, 1.05, 50.0)
    path = paths.minute_path(trades, bars, POINT_VALUE)
    d = days.server_days(path, "EETUS", "UTC")
    assert d.attrs["n_nat"] > 0, "a DST-ambiguous hour must be counted, not guessed"

    # EETUS day cut 7 h off New York: 2026-09-14 23:30 EETUS == 16:30 New York (no DST shift here).
    idx2 = pd.date_range("2026-09-14 23:00", periods=90, freq="1min")
    bars2 = pd.DataFrame({"High": 1.1, "Low": 1.0, "Close": 1.05}, index=idx2)
    trades2 = _trade(idx2[0], idx2[-1], 1.00, 1.05, 10.0)
    path2 = paths.minute_path(trades2, bars2, POINT_VALUE)
    d2 = days.server_days(path2, "EETUS", "America/New_York")
    assert pd.Timestamp("2026-09-14") in d2.index, "EETUS 23:30 must read as 16:30 New York, same day"
    print("ok: EETUS shift and DST-ambiguous hour")


def check_blocks_and_carry() -> None:
    """Joint low beats the sum of separate day-lows, and a flat block after a closed loss
    carries the last level forward instead of 0."""
    low_a = np.array([-10, 0, 0, 0], dtype=np.float32)
    low_b = np.array([0, 0, -8, 0], dtype=np.float32)
    day_labels = np.array([1, 1, 1, 1], dtype="int64")
    joint = blocks.joint_day_low([low_a, low_b], day_labels)
    assert joint.iloc[0] > (low_a.min() + low_b.min()), \
        "joint low of non-coincident worst minutes must be above the sum of the day-lows"

    bars = _bars("2026-01-05 00:00", 11)
    trades = _trade(bars.index[0], bars.index[10], 1.05, 1.00, -50.0)
    path = paths.minute_path(trades, bars, POINT_VALUE)
    g = blocks.grid(pd.Timestamp("2026-01-05 00:00", tz="UTC"),
                     pd.Timestamp("2026-01-05 01:00", tz="UTC"), 5)
    bl = blocks.blocks(path, "UTC", "UTC", g)
    assert np.allclose(bl["low"][2:], -50.0), \
        "a flat block after the closed loss must carry -50, not reset to 0"
    print("ok: joint diversification and carried level after a closed loss")


def check_golden() -> None:
    """The archived USDJPY strategy: MAE/MFE licence shares, and Σ daily = Σ Profit/Loss."""
    root = archive_dir() / "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048"
    runs = sorted(root.glob("*/harvest/trades.parquet")) if root.exists() else []
    if not runs:
        print("skip: golden archive not present on this machine")
        return

    trades = pd.read_parquet(runs[0])
    feed = "USDJPY_M1"
    t0 = time.perf_counter()
    bars = barstore.source(feed, ["High", "Low", "Close"])
    t_read = time.perf_counter() - t0
    value = calibrate.point_value(trades)

    t0 = time.perf_counter()
    path = paths.minute_path(trades, bars, value)
    t_path = time.perf_counter() - t0
    tm = time.perf_counter()
    d = days.server_days(path, "Asia/Jerusalem", "UTC")
    t_days = time.perf_counter() - tm
    tm = time.perf_counter()
    grid = blocks.grid(pd.Timestamp(path["t"][0], tz="UTC"), pd.Timestamp(path["t"][-1], tz="UTC"), 5)
    blocks.blocks(path, "Asia/Jerusalem", "UTC", grid)
    t_blocks = time.perf_counter() - tm

    dp = days.daily_pnl(d)
    gap = abs(dp.sum() - trades["Profit/Loss"].sum())
    assert gap < 1e-6, f"golden Σ daily != Σ Profit/Loss, gap={gap}"

    rebuilt = excursions.rebuild(trades, bars, value)
    lic = excursions.licence(trades, rebuilt, tolerance=1.0, min_share=0.99)
    assert lic["mae_exact"] >= 0.99, f"MAE exact share {lic['mae_exact']} below 0.99"
    assert lic["mfe_exact"] >= 0.99, f"MFE exact share {lic['mfe_exact']} below 0.99"

    print(f"ok: golden — n={lic['n']} mae_exact={lic['mae_exact']:.3f} "
          f"mfe_exact={lic['mfe_exact']:.3f} sum-gap={gap:.2e}")
    print(f"    timing: bars read {t_read:.2f}s, path {t_path:.2f}s, days {t_days:.2f}s, "
          f"blocks {t_blocks:.2f}s")


def main() -> None:
    """Run every check; a failure raises and exits non-zero."""
    check_long_across_days()
    check_short_worst_is_high()
    check_weekend_gap()
    check_eetus_and_dst()
    check_blocks_and_carry()
    check_golden()
    print("ok")


if __name__ == "__main__":
    main()
