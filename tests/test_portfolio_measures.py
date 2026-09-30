"""Known-answer checks for portfolio/common/construct/pairs (PLAN.md §8.1)."""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.common.construct.pairs import measures, rolling, stress  # noqa: E402

FAILED = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """Print one check's result and remember failures."""
    print(f"{'OK  ' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        FAILED.append(name)


def test_pearson_spearman_match_scipy() -> None:
    """Pearson and Spearman equal scipy on random correlated series."""
    rng = np.random.default_rng(1)
    a = rng.normal(size=48)
    b = 0.4 * a + rng.normal(size=48)
    got_p = measures.pearson(a, b, {})
    want_p = pearsonr(a, b)[0]
    check("pearson == scipy", np.isclose(got_p, want_p), f"{got_p:.6f} vs {want_p:.6f}")
    got_s = measures.spearman(a, b, {})
    want_s = spearmanr(a, b)[0]
    check("spearman == scipy", np.isclose(got_s, want_s), f"{got_s:.6f} vs {want_s:.6f}")


def test_co_loss_hand_table() -> None:
    """Co-loss on a 12-month hand table equals 3/12."""
    # both < 0 on exactly 3 of 12 overlapping months
    a = np.array([-1, -1, -1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=float)
    b = np.array([-1, -1, -1, -1, -1, 1, 1, 1, 1, 1, 1, 1], dtype=float)
    got = measures.co_loss(a, b, {})
    check("co_loss == 3/12", np.isclose(got, 3 / 12), f"{got}")


def test_tail_worst_months_only() -> None:
    """Tail correlation is high on a pair built to correlate only in its worst months, unlike the whole-series Pearson."""
    rng = np.random.default_rng(2)
    n = 100
    a = rng.normal(scale=1.0, size=n)
    b = rng.normal(scale=1.0, size=n)
    qa, qb = np.quantile(a, 0.30), np.quantile(b, 0.30)
    tail_idx = np.where((a <= qa) | (b <= qb))[0]
    b[tail_idx] = a[tail_idx] + rng.normal(scale=0.01, size=tail_idx.size)
    got = measures.tail(a, b, {"tail_quantile": 0.30})
    whole = measures.pearson(a, b, {})
    check("tail correlation high", got > 0.9, f"tail={got:.3f}")
    check("tail != whole-series pearson", not np.isclose(got, whole, atol=0.2), f"{got:.3f} vs {whole:.3f}")


def test_overlap_never_forced_zero() -> None:
    """overlap() counts the 5 shared rows; pearson computes on them rather than reading 0.0."""
    a = np.array([1.0, 2.0, 3.0, 4.0, 5.0, np.nan, np.nan])
    b = np.array([1.0, 2.1, 2.9, 4.2, 4.8, 1.0, np.nan])
    n = measures.overlap(a, b)
    check("overlap == 5", n == 5, f"{n}")
    got = measures.pearson(a, b, {})
    check("pearson computed on the 5, not forced to 0.0", got > 0.9, f"{got:.3f}")


def test_nan_below_min_finite() -> None:
    """A coefficient on fewer than 3 finite rows is NaN."""
    a = np.array([1.0, 2.0, np.nan, np.nan, np.nan])
    b = np.array([1.0, 2.0, np.nan, 3.0, np.nan])
    got = measures.pearson(a, b, {})
    check("pearson NaN below 3 finite rows", np.isnan(got), f"{got}")


def test_rolling_whole_and_recent() -> None:
    """Rolling whole and recent maxima both find the one high-rho window."""
    # 120 months: first 60 independent (rho ~ 0), last 60 (window_start=60, a clean
    # non-overlapping window) built at rho = 0.9 — the one window that should win the max.
    rng = np.random.default_rng(3)
    n = 120
    a = rng.normal(size=n)
    b = np.empty(n)
    b[:60] = rng.normal(size=60)
    b[60:] = 0.9 * a[60:] + rng.normal(scale=0.05, size=60)
    result = rolling.rolling_max(a, b, window=60, recent=36, method="pearson")
    check("rolling whole_abs picks up the rho=0.9 window",
          result["whole_abs"] > 0.8, f"{result}")
    check("rolling recent_abs == whole_abs (the winning window ends inside the last 36)",
          np.isclose(result["recent_abs"], result["whole_abs"]), f"{result}")
    check("n_windows == n - window + 1", result["n_windows"] == n - 60 + 1, f"{result['n_windows']}")


def test_rolling_skips_nonfinite_window() -> None:
    """A window touching a non-finite row is excluded from n_windows."""
    a = np.arange(70, dtype=float)
    b = np.arange(70, dtype=float)
    a[65] = np.nan
    result = rolling.rolling_max(a, b, window=60, recent=10, method="pearson")
    # 11 windows total (start 0..10); windows with start in [6,10] contain index 65 -> 5 skipped
    check("rolling skips windows touching the NaN", result["n_windows"] == 11 - 5, f"{result}")


def test_stress_calm_vs_stress_days() -> None:
    """Stress-day correlation reads ~0 on independent calm days and 1 on identical planted stress days."""
    rng = np.random.default_rng(4)
    n = 500
    a = rng.normal(size=n)
    b = rng.normal(size=n)  # independent on calm days
    stress_idx = np.zeros(n, dtype=bool)
    stress_idx[::20] = True  # planted stress days, ~5%
    planted = -3.0 + rng.normal(scale=0.5, size=stress_idx.sum())
    a[stress_idx] = planted
    b[stress_idx] = planted  # identical (not constant) on stress days -> rho == 1
    calm = stress.stress_corr(a, b, ~stress_idx)
    hot = stress.stress_corr(a, b, stress_idx)
    check("stress_corr on calm days ~= 0", abs(calm) < 0.2, f"calm={calm:.3f}")
    check("stress_corr on planted stress days == 1", np.isclose(hot, 1.0), f"stress={hot:.3f}")


def test_stress_days_selection() -> None:
    """stress_days picks the pool's worst days, planted worst day included."""
    rng = np.random.default_rng(5)
    n = 200
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    pool = pd.DataFrame({"m1": rng.normal(size=n), "m2": rng.normal(size=n)}, index=idx)
    worst_day = idx[3]
    pool.loc[worst_day] = -100.0
    days = stress.stress_days(pool, 0.01)
    check("stress_days includes the planted worst day", worst_day in days, f"{list(days)[:3]}")


def test_effective_n_clones_and_independent() -> None:
    """Effective N reads 1 for k clones and ~k for k independent series, both formulas."""
    k = 8
    clones = np.ones((k, k))
    result = stress.effective_n(clones)
    check("effective_n clones participation == 1", np.isclose(result["participation"], 1.0), f"{result}")
    check("effective_n clones average == 1", np.isclose(result["average"], 1.0), f"{result}")

    independent = np.eye(k)
    result = stress.effective_n(independent)
    check("effective_n independent participation == k", np.isclose(result["participation"], k), f"{result}")
    check("effective_n independent average == k", np.isclose(result["average"], k), f"{result}")


def report_timings() -> None:
    """Print rolling_max's wall time for one pair and for a 1,225-pair pool, both 120 months."""
    rng = np.random.default_rng(6)
    a = rng.normal(size=120)
    b = rng.normal(size=120)
    t0 = time.perf_counter()
    rolling.rolling_max(a, b, window=60, recent=36, method="pearson")
    one_pair = time.perf_counter() - t0
    print(f"TIMING one pair, 120 months, rolling_max: {one_pair * 1000:.3f} ms")

    n_pairs = 1225
    series = rng.normal(size=(50, 120))
    t0 = time.perf_counter()
    pairs = 0
    for i in range(50):
        for j in range(i + 1, 50):
            rolling.rolling_max(series[i], series[j], window=60, recent=36, method="pearson")
            pairs += 1
    elapsed = time.perf_counter() - t0
    print(f"TIMING {pairs} pairs (~{n_pairs}), 120 months: {elapsed:.3f} s total, "
          f"{elapsed / pairs * 1000:.3f} ms/pair")


def main() -> int:
    """Run every check and report; exit non-zero if any failed."""
    test_pearson_spearman_match_scipy()
    test_co_loss_hand_table()
    test_tail_worst_months_only()
    test_overlap_never_forced_zero()
    test_nan_below_min_finite()
    test_rolling_whole_and_recent()
    test_rolling_skips_nonfinite_window()
    test_stress_calm_vs_stress_days()
    test_stress_days_selection()
    test_effective_n_clones_and_independent()
    report_timings()
    if FAILED:
        print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
