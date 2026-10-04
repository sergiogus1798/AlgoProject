#!/usr/bin/env python3
"""studies.optimisation.marketSurfaces.measure.lift from its definitions: the top-k of a row;
J = x / (2k − x); the lift of a market under its own zero-edge null is 1 in expectation; a
market whose top is the main one's reads a lift far above every draw; variants that trade the
same days make the null's J wider than independent ones; the mother's share has its baseline."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.marketSurfaces.measure import lift

RNG = np.random.default_rng(3)
V, D, K = 200, 400, 20
SIGNS = RNG.choice([-1.0, 1.0], size=(lift.DRAWS, D))


def test_tops_and_jaccard() -> None:
    """The top-2 of a row, and J at no, half and full overlap."""
    got = lift.tops(np.array([[3.0, 9.0, 1.0, 7.0]]), 2)
    assert got.tolist() == [[False, True, False, True]]
    assert lift.jaccard(np.array([0, 10, 20]), 20).tolist() == [0.0, 10 / 30, 1.0]


def test_lift_is_one_under_the_null() -> None:
    """A zero-edge market read against its own null: lifts average 1, chance near k²/n."""
    days = RNG.normal(size=(D, V))
    main_top = lift.tops(RNG.normal(size=(1, V)), K)[0]
    null = lift.flipped(days, SIGNS, K)
    got = lift.market(main_top, null[0], null, 0)
    assert np.isclose(got["lifts"].mean(), 1.0)
    expected = (K * K / V) / (2 * K - K * K / V)          # independent variants: hypergeometric
    assert abs(got["chance"] - expected) < 0.01, got["chance"]
    assert abs(got["inside_null"].mean() - K / V) < 0.03


def test_shared_region_reads_far_above_chance() -> None:
    """The main market's own top as the other's: J = 1, beyond every draw."""
    days = RNG.normal(size=(D, V))
    null = lift.flipped(days, SIGNS, K)
    main_top = np.arange(V) < K
    got = lift.market(main_top, main_top, null, 0)
    assert got["j"] == 1.0 and got["lift"] > np.percentile(got["lifts"], 95) and got["inside"]


def test_dependent_variants_widen_the_null() -> None:
    """Ten clusters of twenty variants trading the same days: same mean J, a far wider one."""
    alone = lift.flipped(RNG.normal(size=(D, V)), SIGNS, K)
    base = np.repeat(RNG.normal(size=(D, 10)), 20, axis=1)
    alike = lift.flipped(base + 0.05 * RNG.normal(size=(D, V)), SIGNS, K)
    main_top = np.arange(V) < K                            # one whole cluster
    a, b = lift.market(main_top, main_top, alone, None), lift.market(main_top, main_top, alike, None)
    assert np.std(b["lifts"] * b["chance"]) > 2 * np.std(a["lifts"] * a["chance"])
    assert a["inside"] is None and a["inside_null"] is None


def test_together() -> None:
    """Three markets read as one: the share, its baseline, the median lift, and nothing from none."""
    days = RNG.normal(size=(D, V))
    null = lift.flipped(days, SIGNS, K)
    main_top = np.arange(V) < K
    yes, no = lift.market(main_top, main_top, null, 0), lift.market(main_top, ~main_top, null, 0)
    got = lift.together({"a": yes, "b": no, "c": no})
    assert got["markets"] == 3 and np.isclose(got["inside"], 1 / 3)
    assert np.isclose(got["excess"], 1 / 3 - got["baseline"]) and abs(got["baseline"] - 0.1) < 0.03
    assert got["lift"] == no["lift"] == 0.0 and got["null"]["excess"][0] <= 0 <= got["null"]["excess"][-1]
    assert lift.together({})["lift"] is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
