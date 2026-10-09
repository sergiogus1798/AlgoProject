#!/usr/bin/env python3
"""Known-answer tests of the parameter map: a planted quadratic is legible with the right ranking, noise is not."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.cloud import one
from studies.optimisation.cloud.inputs import cloud as inputs
from studies.optimisation.cloud.inputs.config import config
from studies.optimisation.cloud.measure import reference
from studies.optimisation.cloud.model import surrogate

CFG = config([])


def batch(n: int = 1000, seed: int = 0) -> pd.DataFrame:
    """A batch as `inputs.measured` returns it: the mother, `n` uniform variants over 5 live
    parameters and one frozen, 4 canaries, 3 inert copies of the mother, one exact duplicate
    and one variant under the trade floor.

    build: 6(x0 - ½)² + x1 + x2·x3 + a little noise, x4 moves nothing. oos1: noise.
    """
    rng = np.random.default_rng(seed)
    x = rng.random((n + 1, 5))
    build = 6 * (x[:, 0] - 0.5) ** 2 + x[:, 1] + x[:, 2] * x[:, 3] + 0.05 * rng.normal(size=n + 1)
    frame = pd.DataFrame(10 + 90 * x, columns=[f"param_P{i}" for i in range(5)]).assign(
        param_Frozen=7.0, stratum="lhs", origin=False, build_excess=build,
        oos1_excess=rng.standard_t(3, n + 1), build_trades=500.0, oos1_trades=60.0)
    frame.loc[0, ["stratum", "origin"]] = ["origin", True]
    frame = frame.assign(build_profit=frame["build_excess"] * 1000 + 5,
                         oos1_profit=frame["oos1_excess"] * 1000)
    mother, twin, thin = frame.iloc[[0]], frame.iloc[[1]], frame.iloc[[2]]
    canary = mother.assign(stratum="canary", origin=False, build_excess=1e6, param_P4=1e3,
                           build_profit=-1.0)
    extra = [canary] * 4 + [mother.assign(stratum="inert", origin=False, param_Frozen=99.0)] * 3 \
        + [twin.assign(param_P4=55.0), thin.assign(build_trades=74.0, build_profit=-2.0)]
    out = pd.concat([frame, *extra], ignore_index=True)
    return out.assign(variant_id=[f"P{i:05d}" for i in range(len(out))])


def test_the_screen_counts_what_each_filter_removes() -> None:
    """7 controls, one variant under 15 x 5 = 75 trades, one exact duplicate; the mother stays."""
    kept, counts = inputs.screen(batch(), 15)
    assert counts == {"lote": 1010, "controles": 7, "vivos": 5, "suelo": 75, "suelo_dentro": 1,
                      "duplicados": 1, "quedan": 1001, "avisos": []}
    assert kept["origin"].sum() == 1 and set(kept["stratum"]) == {"lhs", "origin"}
    low = batch().assign(build_trades=lambda f: f["build_trades"].where(~f["origin"], 10.0))
    kept, counts = inputs.screen(low, 15)
    assert counts["suelo_dentro"] == 0 and len(counts["avisos"]) == 1 and counts["quedan"] == 1002


def test_a_planted_quadratic_is_legible_with_the_right_ranking() -> None:
    """Variances 36/180, 1/12, 1/48 + 1/48 + 1/144: x0 60 %, x1 25 %, x2 and x3 interacting, x4 nothing."""
    found = one.read(batch(), CFG)
    assert found["live"] == [f"param_P{i}" for i in range(5)] and found["coefficients"] == 21
    build, oos1 = found["legs"]["build"], found["legs"]["oos1"]
    first, total = build["indices"]["first"], build["indices"]["total"]
    assert build["legible"] and build["r2_adj"] > 0.95 > 0.1 > build["r2_ref"]
    order = np.argsort(total)[::-1]
    assert list(order[:2]) == [0, 1] and order[-1] == 4 and set(order[2:4]) == {2, 3}
    assert abs(first[0] - 0.6025) < 0.03 and abs(first[1] - 0.2510) < 0.03 and total[4] < 0.01
    assert abs(total[2] - 0.0837) < 0.02 and total[2] > first[2] and total[3] > first[3]
    assert not oos1["legible"]


def test_the_report_carries_the_facts_and_says_noise_is_noise(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The contract validates; oos1's tab opens with «sin estructura distinguible del ruido»."""
    monkeypatch.setattr(inputs, "measured", lambda work: batch())
    got = one.run(Path("Strategy_1.2.3"), CFG)
    facts = got["facts"]
    assert got["strategy"] == "Strategy 1.2.3" and got["verdict"] is None
    assert facts["vivos"] == 5 and facts["variantes"] == {"build": 1001, "oos1": 1001}
    assert facts["build"]["legible"] is True and facts["oos1"]["legible"] is False
    assert set(facts["build"]["sobol_total"]) == {f"P{i}" for i in range(5)}
    tabs = {t["name"]: t["blocks"] for t in got["tabs"]}
    assert tabs["oos1"][0]["label"] == "Sin estructura distinguible del ruido"
    assert tabs["build"][0]["label"] == "Ranking legible"
    assert sum(b["kind"] == "grid" for b in tabs["build"]) == 6


def test_fewer_variants_than_coefficients_is_no_map() -> None:
    """21 coefficients and 21 variants: nothing fitted, said in so many words."""
    found = one.read(batch().iloc[:21], CFG | {"floor_is_per_param": 0})
    assert found["legs"] == {} and len(found["cloud"]) == 21


def test_noise_is_called_legible_at_the_nominal_rate() -> None:
    """300 clouds of heavy-tailed noise, 150 variants, 3 parameters: about 5 % beat their own p95."""
    rng = np.random.default_rng(1)
    hits = 0
    for seed in range(300):
        unit, y = rng.random((150, 3)), rng.standard_t(3, 150)
        ref = reference.shuffled(unit, y, 200, seed)
        hits += reference.legible(surrogate.fit(unit, y)["r2_adj"], ref, 95)["legible"]
    assert 0.012 <= hits / 300 <= 0.088, hits        # 5 % ± 3 standard errors of 300 draws


def test_a_two_valued_parameter_is_not_charged_for_its_square() -> None:
    """x in {0, 1} makes x² a copy of x: rank 2, so the adjustment uses 2 and not 3."""
    rng = np.random.default_rng(2)
    unit, y = rng.integers(0, 2, (50, 1)).astype(float), rng.normal(size=50)
    r2 = 1 - (1 - surrogate.fit(unit, y)["r2_adj"]) * 48 / 49
    assert abs(r2 - np.corrcoef(unit[:, 0], y)[0, 1] ** 2) < 1e-9
