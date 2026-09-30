"""The pair filters on INDEPENDENT strategies: short overlaps skip rolling, tail is one-sided (owner, 2026-09-30)."""

import sys
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


def test_short_overlap_judged_without_rolling() -> None:
    """36 shared months (>= 24, < 60): rolling does not apply, the rest decide (owner, 2026-09-30)."""
    rng = np.random.default_rng(8)
    n_months = 80
    n = n_months * DAYS_PER_MONTH
    daily, monthly = _pool({"X": rng.normal(size=n), "Y": rng.normal(size=n),
                            "Z": rng.normal(size=n)}, n_months)
    cut = n_months - 36
    monthly.loc[monthly.index[:cut], ["Y", "Z"]] = np.nan
    daily.loc[daily.index[: cut * DAYS_PER_MONTH], ["Y", "Z"]] = np.nan
    cfg = _cfg()
    result = admissible_mod.admissible(table.table(daily, monthly, cfg), ["X", "Y", "Z"], cfg)
    check("36-month pairs: no 'undefined', no rolling filter counted",
          not any(k == "undefined" or k.startswith("rolling_") for k in result["counts"]),
          f"{result['counts']}")
    check("n_without_rolling counts the three short pairs", result["n_without_rolling"] == 3,
          f"{result['n_without_rolling']}")
    many = np.random.default_rng(9).normal(size=(20, 300))
    daily, monthly = _pool({f"S{k}": np.repeat(many[k], DAYS_PER_MONTH) / DAYS_PER_MONTH
                            for k in range(20)}, 300)
    result = admissible_mod.admissible(table.table(daily, monthly, cfg), list(daily.columns), cfg)
    check("tail never rejects independent strategies (one-sided, Berkson ≈ −0.46)",
          "tail" not in result["counts"], f"{result['counts']}")


def main() -> int:
    """Run every check and report."""
    test_short_overlap_judged_without_rolling()
    if FAILED:
        print(f"\n{len(FAILED)} check(s) failed: {FAILED}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
