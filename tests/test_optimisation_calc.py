#!/usr/bin/env python3
"""Known-answer tests: wfc interval, wfm per-cell Sharpe, cloud origin rank, marketSurfaces with no rows."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.cloud.measure import stability
from studies.optimisation.marketSurfaces.verdict import call
from studies.optimisation.wfc.measure import correlation
from studies.optimisation.wfm.measure import equity


def test_wfc_interval_uses_the_spearman_variance() -> None:
    """n = 103: the Fisher-z half-width is 1.959964*sqrt(1.06/100) = 0.2018 (Pearson's was 0.1960)."""
    rng = np.random.default_rng(0)
    kept = pd.DataFrame({"i": rng.random(103), "o": rng.random(103)})
    lo, hi = correlation.correlation(kept, {"is": "i", "oos": "o"})["ci95"]
    assert abs((np.arctanh(hi) - np.arctanh(lo)) / 2 - 0.2018) < 1e-4


def test_wfm_cell_sharpe_rolls_a_weekend_close_to_monday() -> None:
    """Fri 10, Sun 500, Mon -20, Tue 30: the Sunday close counts on Monday (480), Sharpe 10.35."""
    close = pd.to_datetime(["2024-01-05", "2024-01-07", "2024-01-08", "2024-01-09"])
    trades = pd.DataFrame({"strategy": "s", "sample": "OOS", "result": "c", "Close time": close,
                           "Profit/Loss": [10.0, 500.0, -20.0, 30.0]})
    got = equity.per_cell(trades, "s")["sharpe"].iloc[0]
    assert abs(got - 10.35) < 0.01, got


def test_origin_rank_ignores_nan_variants() -> None:
    """[1, 2, NaN, 3] with origin 3: rank 1.0 (was 0.75)."""
    per = {"sharpe": pd.DataFrame({"a": [1.0], "b": [2.0], "c": [np.nan], "o": [3.0]})}
    assert stability.origin_rank(per, per["sharpe"].index, "o").iloc[0] == 1.0


def test_no_rows_is_not_a_region_that_travels() -> None:
    """No declared market in the batch: `fail`, never `pass` through all([])."""
    rows = pd.DataFrame({"segment": [], "state": []})
    assert call.mother(rows, 4, 0.5)["state"] == "fail"


if __name__ == "__main__":
    test_wfc_interval_uses_the_spearman_variance()
    test_wfm_cell_sharpe_rolls_a_weekend_close_to_monday()
    test_origin_rank_ignores_nan_variants()
    test_no_rows_is_not_a_region_that_travels()
    print("ok")


def test_negative_original_is_no_ratio() -> None:
    """A strategy that lost in the original has no 'share kept': -200 against -100 is not 2.0."""
    from studies.breakage.mcRetest.verdict import scoring
    result = {"s": {"original_net": -100.0, "fragility": {"net_p5": {"point": -200.0}},
                    "modes": {"perturbed": True}}}
    from studies.breakage.mcRetest.inputs import tasks
    key = next(k for k, r in tasks.ROLE.items() if r == "execution")
    result = {key: result["s"]}
    assert scoring._kept(result, "execution") == 1.0, "no valid ratio: the neutral 1.0"


def test_design_levels_widen_on_the_right_side_of_a_negative_original() -> None:
    """Original -10, min_span 0.3: the span reaches -13..-7 (it was -7..-13, the wrong side)."""
    from studies.breakage.spp.model import profile
    levels = pd.DataFrame({"level": np.arange(-20.0, 1.0)})
    call_ = {"center": -10.0, "argmax": -10.0, "from": -10.0, "to": -10.0}
    got = profile.design_levels(levels, call_, -10.0, 8, 0.3)
    assert min(got) <= -13 and max(got) >= -7, got


def test_pooled_rho_ignores_a_constant_cell() -> None:
    """A NaN cell rho (constant metric) must not turn the pooled figure into NaN."""
    from studies.optimisation.wfm.measure import correlation as wfm
    cells = pd.DataFrame({"rho": [0.2, 0.4, float("nan")], "n_steps": [10, 10, 10]})
    assert abs(wfm.pooled(cells, n_resamples=200)["rho"] - np.tanh(np.mean([np.arctanh(0.2), np.arctanh(0.4)]))) < 1e-9
