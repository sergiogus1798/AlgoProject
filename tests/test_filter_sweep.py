#!/usr/bin/env python3
"""Known-answer tests for the filter sweep and its replication (CALC_REVIEW m29): a lone strong
filter can be named, the reference's best filters obey the sweep's floor, an empty sample is NaN."""

import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.inference import fdr
from studies.screening.analysis import improvement, replication
from studies.screening.replication import report

N = 4000
TARGET = "Sharpe Ratio (OOS)"


def population(metrics: int, n: int, seed: int) -> tuple[dict[str, np.ndarray], list[str]]:
    """Pure noise: `metrics` in-sample columns and one outcome, none related to another."""
    rng = np.random.default_rng(seed)
    names = [f"m{i:03d} (IS)" for i in range(metrics)]
    return {TARGET: rng.normal(size=n)} | {m: rng.normal(size=n) for m in names}, names


def test_a_lone_five_sd_lift_among_209_nulls_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """105 metrics cut at 5 % from both ends are 210 filters of 200 survivors each; the top 5 %
    of one metric is lifted by 5 standard errors of a median of 200, the other 209 are noise.
    One cut per metric, because nested cuts of a lifted metric would all be lifted with it."""
    monkeypatch.setattr(improvement, "CUTS", (5,))
    columns, names = population(105, N, 1)
    strong = {"metric": names[0], "side": "top", "cut": 5}
    kept = improvement.survivors(columns[names[0]], strong)
    assert kept.sum() == 200
    columns[TARGET][kept] += 5 * 1.2533 / np.sqrt(200)
    rows = improvement.sweep(columns, names, TARGET)
    assert len(rows) == 210
    p = {r["metric"]: r["p"] for r in rows}[improvement.label(strong)]
    assert p == pytest.approx(1 / 6000, rel=1e-12)
    assert p < improvement.ALPHA / 210
    assert fdr.discoveries(rows, improvement.ALPHA) == {improvement.label(strong)}


def test_a_filter_off_the_floor_keeps_its_first_pass() -> None:
    """A filter some of whose first 2,000 resamples cross zero is not redrawn: its numbers are
    those of before the fix (recorded from that code), whatever the family's size."""
    y = np.random.default_rng(7).normal(size=N)
    mask = np.arange(N) < 300
    got = improvement.lift(y, mask, 0.0, reach=6000)
    assert got == pytest.approx({"d_median": -0.03725226232373601, "d_median_lo": -0.15225947793145916,
                                 "d_median_hi": 0.03004202685622892, "d_hit": -0.04783333333333334,
                                 "d_hit_lo": -0.10449999999999998, "d_hit_hi": 0.012166666666666659,
                                 "p": 0.413}, abs=1e-12)


def test_best_filters_obey_the_sweeps_floor() -> None:
    """On a reference of 1,000 the 5 % and 10 % cuts keep 50 and 100: the sweep would not judge
    them, so they cannot be the reference's best. On one of 229 nothing reaches 200."""
    columns, names = population(21, 1000, 2)
    best = report.best_filters(columns, TARGET, names)
    assert len(best) == report.FILTERS
    assert all(improvement.survivors(columns[c["metric"]], c).sum() >= improvement.MIN_SURVIVORS
               for c in best)
    columns, names = population(21, 229, 3)
    assert report.best_filters(columns, TARGET, names) == []


def test_an_empty_sample_is_nan_not_a_warning() -> None:
    """No strategy of the sample clears the reference's threshold: n is 0, the rest NaN."""
    full, none = np.array([1.0, -1.0, 2.0]), np.array([])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for reference, sample in ((full, none), (none, full)):
            gap = replication.hit_gap(reference, sample, 0.0)
            assert set(gap) == {"gap", "lo", "hi"} and all(np.isnan(v) for v in gap.values())
        columns, names = population(1, 1000, 4)
        below = {k: v - 100 if k == names[0] else v for k, v in columns.items()}
        got = replication.carried(columns, below, {"metric": names[0], "side": "top", "cut": 10},
                                  TARGET)
    assert got["n"] == 0 and got["share"] == 0.0
    assert np.isnan(got["observed"]) and np.isnan(got["lo"]) and np.isnan(got["hi"])
    assert got["predicted"] == pytest.approx((columns[TARGET][columns[names[0]] >= np.quantile(
        columns[names[0]], 0.9)] > 0).mean(), abs=1e-12)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
