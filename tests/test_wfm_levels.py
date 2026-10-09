#!/usr/bin/env python3
"""Step 19's known answers: the oos2 re-charge on a hand-made trade, L1's false-positive rate on
near-copy cells without edge, a planted edge and a planted loss, the facts each `modo_real`
emits, the effective cells of identical and of orthogonal curves, the drift's denominator, and
the same seed giving the same null."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.weekly import flip
from studies.optimisation.wfm import run
from studies.optimisation.wfm.measure import drift, excess, levels
from studies.optimisation.wfm.verdict import call

WEEKS, CELLS, YEARS, ALPHA = 143, 30, 2.75, 0.05


def panel(rng: np.random.Generator, edge: float) -> pd.DataFrame:
    """30 near-copy cells: one shared weekly curve, a little of each cell's own noise."""
    shared = rng.standard_normal((WEEKS, 1)) + edge
    return pd.DataFrame(shared + 0.3 * rng.standard_normal((WEEKS, CELLS)),
                        columns=[f"c{i}" for i in range(CELLS)])


def facts(cells: pd.DataFrame, seed: int = 0) -> dict:
    """L1's facts of one panel, as `verdict.call` reads them."""
    got = levels.l1(cells, flip.signs(seed, 500, len(cells)), YEARS)
    return {"l1": got, "centro": {"exceso_oos2": float(cells["c0"].sum() / YEARS)}}


def test_recharge_by_hand() -> None:
    """2 lots, point value 0.5: spread +10 and slippage +3 twice = 2*0.5*16 = 16; plus 0.01 % more
    commission on a 20 000 open price = 2*0.5*20000*0.01/100 = 2."""
    trade = pd.DataFrame({"Size": [2.0], "Open price": [20000.0]})
    card = {"point_value": 0.5, "commission_method": "PercentageBased"}
    got = excess.recharge(trade, card | {"spread": 30.0, "slippage": 4.0, "commission": 0.0},
                          card | {"spread": 40.0, "slippage": 7.0, "commission": 0.01})
    assert np.allclose(got, [18.0]), got


def test_l1_rejects_five_in_a_hundred_without_edge() -> None:
    """Symmetric noise, no edge: p- <= 0.05 about 5 % of the time, and p+ the same."""
    rng = np.random.default_rng(1)
    got = [facts(panel(rng, 0.0), i)["l1"] for i in range(400)]
    low = np.mean([g["p_menos"] <= ALPHA for g in got])
    high = np.mean([g["p_mas"] <= ALPHA for g in got])
    print(f"sin ventaja, 400 madres: p- <= 0.05 en {low:.1%}, p+ <= 0.05 en {high:.1%}")
    assert 0.02 <= low <= 0.085 and 0.02 <= high <= 0.085, (low, high)


def test_planted_edge_and_planted_loss() -> None:
    """+0.4 sd a week reads «reoptimizar gana»; -0.4, NO PASA; nothing, never NO PASA here."""
    rng = np.random.default_rng(2)
    won = call.call(facts(panel(rng, 0.4)), call.FIJO, ALPHA)
    lost = call.call(facts(panel(rng, -0.4)), call.FIJO, ALPHA)
    assert won["verdict"] == call.PASA and won["label"].endswith(call.WINS), won
    assert lost["verdict"] == call.NO_PASA and call.STATE[lost["verdict"]] == "fail", lost


def test_reoptimizado_only_adds_limbo_and_its_facts() -> None:
    """A losing centre or a worse-than-frozen L2 is LIMBO in `reoptimizado` and nothing in
    `fijo`; `reopt` exists among the facts only in `reoptimizado`."""
    said = {"l1": {"mediana_exceso": 5.0, "p_mas": 0.3, "p_menos": 0.7},
            "l2": {"p_menos": 0.01}, "centro": {"exceso_oos2": -1.0}}
    assert call.call(said, call.FIJO, ALPHA)["verdict"] == call.PASA
    got = call.call(said, call.REOPT, ALPHA)
    assert got["verdict"] == call.LIMBO and got["why"] == ["centro_no_gana", "reoptimizar_empeora"]
    level = {"mediana_exceso": 1.0, "delta": 1.0, "p_mas": .5, "p_menos": .5, "nulo_p5": 0., "nulo_p95": 0.}
    measured = {"l1": level, "l2": level, "per_year": pd.Series({"c": 2.0}), "centre": "c",
                "effective": 1.0, "positive": 1.0}
    found = {"cells": 3, "passed": False}
    assert "reopt" not in run.facts(measured, 0.5, found, call.FIJO)
    assert run.facts(measured, 0.5, found, call.REOPT)["reopt"] == {"centro_exceso": 2.0, "l2_p_menos": 0.5}


def test_effective_cells() -> None:
    """30 identical curves are worth 1; 30 exactly uncorrelated ones, 30."""
    rng = np.random.default_rng(3)
    same = pd.DataFrame(np.repeat(rng.standard_normal((WEEKS, 1)), CELLS, axis=1))
    noise = rng.standard_normal((WEEKS, CELLS))
    apart, _ = np.linalg.qr(noise - noise.mean(axis=0))     # orthonormal and centred: zero correlation
    assert abs(levels.effective(same) - 1) < 1e-9
    assert abs(levels.effective(pd.DataFrame(apart)) - CELLS) < 1e-6


def test_drift_divides_by_the_mothers_own_parameters() -> None:
    """Mother A has two parameters and moves one per step: 50 %, whatever B's three are."""
    index = pd.MultiIndex.from_tuples([(s, "cell", i) for s in "AB" for i in range(3)],
                                      names=["strategy", "result", "index"])
    nan = np.nan
    chosen = pd.DataFrame({"a1": [1, 2, 3, nan, nan, nan], "a2": [5, 5, 5, nan, nan, nan],
                           "b1": [nan] * 3 + [1, 2, 3], "b2": [nan] * 3 + [1, 2, 3],
                           "b3": [nan] * 3 + [1, 2, 3]}, index=index)
    got = drift.summary(drift.per_step(chosen), chosen).set_index("strategy")
    assert got.loc["A", "parameters"] == 2 and got.loc["B", "parameters"] == 3
    assert got.loc["A", "share_changed_median"] == 0.5 and got.loc["B", "share_changed_median"] == 1.0


def test_same_seed_same_null() -> None:
    """One seed, one answer; another seed, another null."""
    cells = panel(np.random.default_rng(4), 0.1)
    assert facts(cells, 7)["l1"]["p_menos"] == facts(cells, 7)["l1"]["p_menos"]
    assert not np.array_equal(facts(cells, 7)["l1"]["null"], facts(cells, 8)["l1"]["null"])


if __name__ == "__main__":
    for test in [v for k, v in dict(globals()).items() if k.startswith("test_")]:
        test()
    print("ok")
