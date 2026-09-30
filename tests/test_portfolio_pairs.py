"""Known-answer checks for pairs/table.py and search/admissible.py (PLAN.md §8.1, §6)."""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.common.construct.inputs import config as cfg_module  # noqa: E402
from portfolio.common.construct.pairs import table  # noqa: E402
from portfolio.common.construct.search import admissible as admissible_mod  # noqa: E402

DAYS_PER_MONTH = 21
FAILED = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """Print one check's result and remember failures."""
    print(f"{'OK  ' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        FAILED.append(name)


def _cfg(overrides: list[str] | None = None) -> dict:
    """The real engine config, optionally overridden."""
    return cfg_module.load(overrides)


def _pool(series: dict[str, np.ndarray], n_months: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily and monthly frames from per-identity daily arrays of length n_months*DAYS_PER_MONTH."""
    daily_index = pd.bdate_range("2005-01-01", periods=n_months * DAYS_PER_MONTH)
    month_index = pd.period_range("2005-01", periods=n_months, freq="M")
    daily = pd.DataFrame(series, index=daily_index)
    monthly = pd.DataFrame({name: arr.reshape(n_months, DAYS_PER_MONTH).sum(axis=1)
                            for name, arr in series.items()}, index=month_index)
    return daily, monthly


def _filters_of(failing: pd.DataFrame, i: str, j: str) -> set[str]:
    """The filter names a pair failed under, whichever order i, j were declared."""
    lo, hi = min(i, j), max(i, j)
    rows = failing[(failing["i"] == lo) & (failing["j"] == hi)]
    return set(rows["filter"])


def _correlate(base: np.ndarray, rho: float, rng: np.random.Generator) -> np.ndarray:
    """A series with sample Pearson ~= rho against base (unit-variance construction)."""
    return rho * base + np.sqrt(1 - rho**2) * rng.normal(size=base.size)


def test_independent_pairs_all_admissible() -> None:
    """Three mutually independent strategies clear every pairwise filter."""
    rng = np.random.default_rng(66)
    n_months = 60
    n = n_months * DAYS_PER_MONTH
    series = {name: rng.normal(size=n) for name in ("X", "Y", "Z")}
    daily, monthly = _pool(series, n_months)
    cfg = _cfg()
    pairs = table.table(daily, monthly, cfg)
    result = admissible_mod.admissible(pairs, sorted(series), cfg)
    for i, j in (("X", "Y"), ("X", "Z"), ("Y", "Z")):
        check(f"{i}-{j} has no failing filter", _filters_of(result["failing"], i, j) == set(),
              f"{_filters_of(result['failing'], i, j)}")
    check("independent trio fully admissible", result["n_admissible_pairs"] == 3,
          f"{result['n_admissible_pairs']}")


def test_clone_and_negative_correlate_rejected() -> None:
    """A rho=0.95 clone and a rho=-0.6 correlate both fail on the owner's |rho| rule."""
    rng = np.random.default_rng(2)
    n_months = 96
    n = n_months * DAYS_PER_MONTH
    base = rng.normal(size=n)
    clone = _correlate(base, 0.95, rng)
    neg = _correlate(base, -0.6, rng)
    daily, monthly = _pool({"X": base, "X_clone": clone, "X_neg": neg}, n_months)
    cfg = _cfg()
    pairs = table.table(daily, monthly, cfg)
    result = admissible_mod.admissible(pairs, ["X", "X_clone", "X_neg"], cfg)
    clone_got = _filters_of(result["failing"], "X", "X_clone")
    expected = {"pearson_monthly", "pearson_daily", "spearman_monthly", "spearman_daily",
                "rolling_pearson_whole", "rolling_pearson_recent",
                "rolling_spearman_whole", "rolling_spearman_recent"}
    check("clone fails pearson, spearman and rolling at both frequencies",
          expected.issubset(clone_got), f"{clone_got}")
    neg_got = _filters_of(result["failing"], "X", "X_neg")
    check("negative correlate fails on |rho|, pearson_monthly", "pearson_monthly" in neg_got, f"{neg_got}")
    check("neither pair admissible", result["n_admissible_pairs"] == 0, f"{result['n_admissible_pairs']}")


def test_overlap_below_minimum_rejects_alone() -> None:
    """18 shared months rejects on 'overlap' alone, whatever the coefficients would have read."""
    rng = np.random.default_rng(4)
    n_months = 40
    n = n_months * DAYS_PER_MONTH
    x = rng.normal(size=n)
    y = x.copy()  # a perfect clone: every other filter would pass this pair if it were checked
    daily, monthly = _pool({"X": x, "Y": y}, n_months)
    cutoff_month = n_months - 18  # Y's history is only its last 18 months, NaN before that
    monthly.loc[monthly.index[:cutoff_month], "Y"] = np.nan
    daily.loc[daily.index[: cutoff_month * DAYS_PER_MONTH], "Y"] = np.nan
    cfg = _cfg()
    pairs = table.table(daily, monthly, cfg)
    result = admissible_mod.admissible(pairs, ["X", "Y"], cfg)
    got = _filters_of(result["failing"], "X", "Y")
    check("18 overlapping months rejects on 'overlap' only", got == {"overlap"}, f"{got}")
    check("overlap pair not admissible", result["n_admissible_pairs"] == 0, f"{result}")


def test_recent_window_correlation_fails_rolling() -> None:
    """Correlated only in the last 36 months fails both rolling maxima."""
    rng = np.random.default_rng(5)
    n_months = 150
    n = n_months * DAYS_PER_MONTH
    recent_start = (n_months - 36) * DAYS_PER_MONTH
    base = rng.normal(size=n)
    other = rng.normal(size=n)
    other[recent_start:] = 0.9 * base[recent_start:] + np.sqrt(1 - 0.81) * rng.normal(size=n - recent_start)
    daily, monthly = _pool({"X": base, "X_recent": other}, n_months)
    cfg = _cfg()
    pairs = table.table(daily, monthly, cfg)
    whole_pearson = pairs[(pairs["measure"] == "pearson_monthly")]["value"].iloc[0]
    result = admissible_mod.admissible(pairs, ["X", "X_recent"], cfg)
    got = _filters_of(result["failing"], "X", "X_recent")
    check("whole-period monthly pearson stays under threshold",
          abs(whole_pearson) < cfg["pairs"]["pearson"], f"pearson_monthly={whole_pearson:.3f}")
    check("fails rolling recent", "rolling_pearson_recent" in got, f"{got}")
    check("fails rolling whole too", "rolling_pearson_whole" in got, f"{got}")


def test_daily_correlated_monthly_cancels() -> None:
    """Strong shared day-of-month oscillation correlates daily but sums to ~0 each month."""
    rng = np.random.default_rng(23)
    n_months = 66  # above the 60-month rolling window, so rolling is defined, not NaN
    n = n_months * DAYS_PER_MONTH
    phase = 2 * np.pi * np.arange(DAYS_PER_MONTH) / DAYS_PER_MONTH
    shared = np.tile(5.0 * np.sin(phase), n_months)  # exact zero-sum block, every month
    a = shared + rng.normal(scale=1.0, size=n)
    b = shared + rng.normal(scale=1.0, size=n)
    daily, monthly = _pool({"A": a, "B": b}, n_months)
    cfg = _cfg()
    pairs = table.table(daily, monthly, cfg)
    daily_rho = pairs[pairs["measure"] == "pearson_daily"]["value"].iloc[0]
    monthly_rho = pairs[pairs["measure"] == "pearson_monthly"]["value"].iloc[0]
    result = admissible_mod.admissible(pairs, ["A", "B"], cfg)
    got = _filters_of(result["failing"], "A", "B")
    check("daily pearson exceeds threshold", daily_rho > cfg["pairs"]["pearson"], f"{daily_rho:.3f}")
    check("monthly pearson stays under threshold",
          abs(monthly_rho) < cfg["pairs"]["pearson"], f"{monthly_rho:.3f}")
    check("rejected on the daily measures alone",
          got == {"pearson_daily", "spearman_daily"}, f"{got}")


def test_relaxed_run_lets_the_clone_pearson_pass() -> None:
    """--set pairs.pearson=0.99 passes the clone's pearson rows and names 'pearson' as relaxed."""
    rng = np.random.default_rng(7)
    n_months = 96
    n = n_months * DAYS_PER_MONTH
    base = rng.normal(size=n)
    daily, monthly = _pool({"X": base, "X_clone": _correlate(base, 0.95, rng)}, n_months)
    pairs = table.table(daily, monthly, _cfg())
    relaxed_cfg = _cfg(["pairs.pearson=0.99"])
    check("relaxed cfg names pearson", relaxed_cfg["relaxed"] == {"pearson": 0.99},
          f"{relaxed_cfg['relaxed']}")
    result = admissible_mod.admissible(pairs, ["X", "X_clone"], relaxed_cfg)
    got = _filters_of(result["failing"], "X", "X_clone")
    check("pearson rows no longer fail under the relaxed threshold",
          "pearson_monthly" not in got and "pearson_daily" not in got, f"{got}")
    check("spearman still fails at the owner's threshold", "spearman_monthly" in got, f"{got}")
    check("result carries the relaxed flag", result["relaxed"] == {"pearson": 0.99}, f"{result['relaxed']}")


def test_n_out_counts_partners() -> None:
    """n_out counts only identities with >= 1 admissible partner."""
    rng = np.random.default_rng(66)
    n_months = 60
    n = n_months * DAYS_PER_MONTH
    x, y, z = rng.normal(size=n), rng.normal(size=n), rng.normal(size=n)
    lonely = _correlate((x + y + z) / 3, 0.95, rng)  # a clone of everyone: no admissible partner
    daily, monthly = _pool({"X": x, "Y": y, "Z": z, "Lonely": lonely}, n_months)
    cfg = _cfg()
    identities = sorted(["X", "Y", "Z", "Lonely"])
    pairs = table.table(daily, monthly, cfg)
    result = admissible_mod.admissible(pairs, identities, cfg)
    check("n_in == 4", result["n_in"] == 4, f"{result['n_in']}")
    check("n_out == 3 (Lonely has no admissible partner)", result["n_out"] == 3, f"{result['n_out']}")
    lonely_idx = identities.index("Lonely")
    check("Lonely's graph row is all False", not result["graph"][lonely_idx].any(),
          f"{result['graph'][lonely_idx]}")


def test_effective_n_of_independent_pool() -> None:
    """Effective N of k independent strategies reads close to k, both formulas."""
    rng = np.random.default_rng(2)
    n_months = 300  # a long build keeps the "average" formula's mean-rho estimate stable
    n = n_months * DAYS_PER_MONTH
    k = 10
    names = [f"S{i}" for i in range(k)]
    series = {name: rng.normal(size=n) for name in names}
    daily, monthly = _pool(series, n_months)
    cfg = _cfg()
    pairs = table.table(daily, monthly, cfg)
    result = admissible_mod.admissible(pairs, sorted(names), cfg)
    calm, stress_eff = result["effective_n"]["calm"], result["effective_n"]["stress"]
    check(f"calm participation close to k={k}",
          abs(calm["participation"] - k) < 2, f"{calm['participation']:.2f}")
    check(f"calm average close to k={k}", abs(calm["average"] - k) < 2, f"{calm['average']:.2f}")
    check("effective_n reports both calm and stress keys",
          set(result["effective_n"]) == {"calm", "stress"} and set(stress_eff) == {"participation", "average"},
          f"{stress_eff}")


def report_timing_n50() -> None:
    """Wall time and shape of table() over 50 identities, 96 months of synthetic build data."""
    rng = np.random.default_rng(10)
    n_months = 96
    n = n_months * DAYS_PER_MONTH
    names = [f"P{i:03d}" for i in range(50)]
    series = {name: rng.normal(size=n) for name in names}
    daily, monthly = _pool(series, n_months)
    cfg = _cfg()
    t0 = time.perf_counter()
    pairs = table.table(daily, monthly, cfg)
    elapsed = time.perf_counter() - t0
    n_pairs = len(names) * (len(names) - 1) // 2
    print(f"TIMING N=50 ({n_pairs} pairs, 96 months): {elapsed:.2f} s, "
          f"{len(pairs)} rows, {elapsed / n_pairs * 1000:.3f} ms/pair")


def main() -> int:
    """Run every check and report timing; exit non-zero if any failed."""
    test_independent_pairs_all_admissible()
    test_clone_and_negative_correlate_rejected()
    test_overlap_below_minimum_rejects_alone()
    test_recent_window_correlation_fails_rolling()
    test_daily_correlated_monthly_cancels()
    test_relaxed_run_lets_the_clone_pearson_pass()
    test_n_out_counts_partners()
    test_effective_n_of_independent_pool()
    report_timing_n50()
    print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
