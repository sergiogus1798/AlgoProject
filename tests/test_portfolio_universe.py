"""Known-answer checks for sqxcurve, matrix, reconcile and calendar (PLAN.md §5.1, Q1)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata  # noqa: E402
from core.datapaths import variants_dir  # noqa: E402
from core.paths import archive_dir  # noqa: E402
from core.barstore import source as bar_source  # noqa: E402
from portfolio.common.construct.equity import days, matrix, paths, reconcile, sqxcurve  # noqa: E402
from portfolio.common.construct.inputs import source  # noqa: E402
from portfolio.common.construct.inputs import calendar  # noqa: E402

FAILED = []

HARVEST = (archive_dir() / "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048"
           / "2026-09-28T0919" / "harvest" / "equity.parquet")
BATCH = (variants_dir("Test_USDJPY_donchianUpperCrossUp_H1", "Strategy_10.1.79")
         / "equity.parquet")


def check(name: str, ok: bool, detail: str = "") -> None:
    """Print one check's result and remember failures."""
    print(f"{'OK  ' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        FAILED.append(name)


def test_sqx_segment_slice() -> None:
    """A leg's values are kept as they are (each day's lowest equity), sliced to its window."""
    days = pd.to_datetime(["2007-12-28", "2008-01-01", "2008-01-02", "2018-01-02"])
    equity = pd.Series([0.0, -5.0, 10.0, 99.0], index=days)
    got = sqxcurve._segment(equity, assetdata.load("USDJPY"), "build")
    check("segment slice keeps the build days' values",
          got["low"].tolist() == [-5.0, 10.0] and (got["segment"] == "build").all(), f"{got}")


def test_batch_warmup_and_duplicates_dropped() -> None:
    """A synthetic batch column: overlapping legs, duplicate dates, warm-up zeros."""
    build_days = pd.date_range("2008-01-01", "2017-12-31", freq="7D")
    build = pd.Series(np.arange(len(build_days), dtype=float) * 10.0, index=build_days)
    overlap = build_days[build_days >= "2017-11-01"]  # shares dates with build's own tail
    oos1_warmup = pd.Series(0.0, index=overlap)
    oos1_days = pd.date_range("2018-01-01", "2022-12-31", freq="7D")
    oos1_real = pd.Series(np.arange(len(oos1_days), dtype=float) * 5.0, index=oos1_days)
    oos1 = pd.concat([oos1_warmup, oos1_real])
    column = pd.concat([build, oos1]).sort_index(kind="stable")
    n_dup_before = column.index.duplicated().sum()
    pnl = sqxcurve.from_batch(column, "USDJPY")
    check("earlier leg's real value kept on a duplicate date",
          pnl.loc[pd.Timestamp(overlap[0]), "low"] == build.loc[overlap[0]])
    check("synthetic batch has duplicates before processing", n_dup_before > 0, f"{n_dup_before}")
    check("no duplicate dates after from_batch", not pnl.index.duplicated().any())
    data = assetdata.load("USDJPY")
    lo, hi = pd.Timestamp(assetdata.window(data, "build")[0], unit="ms"), \
        pd.Timestamp(assetdata.window(data, "oos1")[1], unit="ms")
    check("no day outside build/oos1", ((pnl.index >= lo) & (pnl.index < hi)).all())


def test_matrix_zero_inside_nan_outside() -> None:
    """0 on a day inside history with no P&L, NaN outside it."""
    a = pd.Series([1.0, 2.0], index=pd.to_datetime(["2020-01-02", "2020-01-06"]))
    b = pd.Series([5.0, 6.0, 7.0], index=pd.to_datetime(["2019-12-31", "2020-01-03", "2020-01-08"]))
    spans = {"A": (pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-06")),
             "B": (pd.Timestamp("2019-12-31"), pd.Timestamp("2020-01-08"))}
    frame = matrix.stack({"A": a, "B": b}, spans)
    check("inside history, no trade -> 0", frame.loc["2020-01-03", "A"] == 0.0)
    check("has a trade -> its value", frame.loc["2020-01-02", "A"] == 1.0)
    check("outside history -> NaN", pd.isna(frame.loc["2019-12-31", "A"])
          and pd.isna(frame.loc["2020-01-08", "A"]))
    check("only days some series carries (no weekend rows)",
          "2020-01-04" not in frame.index.strftime("%Y-%m-%d") and len(frame) == 5)


def test_monthly_nan_only_whole_month_outside() -> None:
    """Monthly sum is NaN only when the whole month is outside a column's history."""
    a = pd.Series([1.0], index=pd.to_datetime(["2020-02-15"]))
    spans = {"A": (pd.Timestamp("2020-02-01"), pd.Timestamp("2020-02-29"))}
    frame = matrix.stack({"A": a}, spans)
    monthly = matrix.monthly(frame)
    check("one month present, not NaN", not pd.isna(monthly.loc[pd.Period("2020-02", "M"), "A"]))
    check("that month sums to the trade", monthly.loc[pd.Period("2020-02", "M"), "A"] == 1.0)


def test_calendar_matching_symbols() -> None:
    """USDJPY and XAUUSD share the same policy dates: the calendar is exactly theirs."""
    cal = calendar.portfolio(["USDJPY", "XAUUSD"])
    data = assetdata.load("USDJPY")
    for seg in ("build", "oos1", "oos2"):
        lo, hi = assetdata.window(data, seg)
        want = (pd.Timestamp(lo, unit="ms"), pd.Timestamp(hi, unit="ms") - pd.Timedelta(days=1))
        check(f"calendar {seg} matches own dates", cal[seg] == want, f"{cal[seg]} vs {want}")
    borrowed_usdjpy = calendar.borrowed(cal, "USDJPY")
    check("no borrowed days when symbols match", all(v == 0 for v in borrowed_usdjpy.values()))


def test_calendar_fx_plus_synthetic_index() -> None:
    """A synthetic index policy extends build past FX's own end; FX borrows those days from oos1."""
    fx = {"build": {"from": 2008, "to": 2017}, "oos1": {"from": 2018, "to": 2022},
          "oos2": {"from": 2023, "to": "2026-08-30"}}
    index = {"build": {"from": 2013, "to": 2019}, "oos1": {"from": 2020, "to": 2023},
             "oos2": {"from": 2024, "to": "2026-08-31"}}
    cal = calendar.combine({"FX": fx, "INDEX": index})
    check("build ends at the later (index's) end",
          cal["build"][1] == pd.Timestamp("2019-12-31"), f"{cal['build']}")
    fx_borrowed = calendar.borrowed_from(cal, fx)
    check("FX borrows 2018-2019 build days from its own oos1",
          fx_borrowed["build"] == 730, f"{fx_borrowed}")
    index_borrowed = calendar.borrowed_from(cal, index)
    check("INDEX borrows nothing (calendar is its own)",
          all(v == 0 for v in index_borrowed.values()), f"{index_borrowed}")


def test_reconcile_ok_and_out() -> None:
    """A copy reconciles ok; a copy off by 5 $ on 2 of 30 days reconciles out at 0.99."""
    idx = pd.date_range("2020-01-01", periods=30, freq="D")
    rebuilt = pd.Series(np.random.default_rng(3).normal(size=30).cumsum(), index=idx)
    ok = reconcile.curve(rebuilt, rebuilt.copy(), tolerance=1.0, min_share=0.99)
    check("identical curves reconcile ok", ok["verdict"] == "ok" and ok["max_gap"] == 0.0, f"{ok}")
    planted = rebuilt.copy()
    planted.iloc[[10, 20]] -= 5.0
    out = reconcile.curve(rebuilt, planted, tolerance=1.0, min_share=0.99)
    check("two days off by 5 $ reconcile out", out["verdict"] == "out"
          and np.isclose(out["exact"], 28 / 30) and np.isclose(out["max_gap"], 5.0), f"{out}")
    days = pd.DataFrame({"closed": [0.0, -3.0, 0.0], "float_end": [-2.0, 0.0, 1.0],
                         "low": [-4.0, -1.0, 0.0]}, index=idx[:3])
    check("low_equity: previous close plus the day's low",
          reconcile.low_equity(days).tolist() == [-4.0, -3.0, -3.0])


def test_real_harvest_and_batch() -> None:
    """The archived strategy's harvest and the real 16.5 batch: segments, windows, duplicates."""
    if not HARVEST.exists() or not BATCH.exists():
        check("real fixtures present", False, "skipped: files not found")
        return
    data = assetdata.load("USDJPY")
    got = {"harvest": sqxcurve.from_harvest(pd.read_parquet(HARVEST), "USDJPY"),
           "batch": sqxcurve.from_batch(pd.read_parquet(BATCH)["P00000"], "USDJPY")}
    for name, frame in got.items():
        check(f"{name}: no duplicate dates", not frame.index.duplicated().any())
        for segment, rows in frame.groupby("segment"):
            lo, hi = (pd.Timestamp(x, unit="ms") for x in assetdata.window(data, segment))
            check(f"{name} {segment}: every day inside its window",
                  ((rows.index >= lo) & (rows.index < hi)).all(), f"{len(rows)} days")
    check("batch carries oos2", "oos2" in set(got["batch"]["segment"]))


def test_golden_rebuild_against_sqx_curve() -> None:
    """The M1 rebuild's daily lowest equity equals SQX's own curve, leg by leg (🔬 max 0.16 $)."""
    if not HARVEST.exists():
        check("golden archive present", False, "skipped: archive not found")
        return
    s = source.load(HARVEST.parts[-4], HARVEST.parts[-3])
    bars = bar_source(s["feed"], ["High", "Low", "Close"])
    sqx = sqxcurve.from_harvest(s["sqx_equity"], s["symbol"])
    for sample, segment in sqxcurve.SAMPLE_TO_SEGMENT.items():
        trades = s["trades"][s["trades"]["sample"] == sample]
        table = days.server_days(paths.minute_path(trades, bars, s["point_value"]),
                                 s["clock"], s["clock"])
        got = reconcile.curve(reconcile.low_equity(table),
                              sqx.loc[sqx["segment"] == segment, "low"], 1.0, 0.99)
        check(f"golden {segment}: rebuild == SQX daily low", got["verdict"] == "ok", f"{got}")


def main() -> int:
    """Run every check and report."""
    test_sqx_segment_slice()
    test_batch_warmup_and_duplicates_dropped()
    test_matrix_zero_inside_nan_outside()
    test_monthly_nan_only_whole_month_outside()
    test_calendar_matching_symbols()
    test_calendar_fx_plus_synthetic_index()
    test_reconcile_ok_and_out()
    test_real_harvest_and_batch()
    test_golden_rebuild_against_sqx_curve()
    if FAILED:
        print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
