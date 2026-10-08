#!/usr/bin/env python3
"""Step 18 on panels whose answer is known by construction: the CSCV, its null, its power, its state."""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import fanout
from studies.optimisation.cscv.inputs import config
from studies.optimisation.cscv.measure import cscv, null, outputs, queue
from studies.optimisation.cscv.verdict import state

BINS, REACH, TOL = 256, 6.0, 0.01
# What the implementation of 2026-10-04 (`measure/cscv.py::run`, argmax, Sharpe, deleted on
# 2026-10-07) returned on golden(seed), 10 blocks: PBO, sum of picks, mean Sharpe out and in.
# The same code gave the same PBO as the new one, to the last digit, on the ten mothers of
# Trade_NIKKEI225_M30_volatilidadL (daily cells, N 215-438) before it was deleted.
GOLDEN = {0: (0.7023809523809523, 3412, -0.047498337683781616, 0.1601614430810656),
          1: (0.20634920634920634, 1475, 0.058620394797931914, 0.167066239634462),
          2: (0.011904761904761904, 792, 0.3854636138141632, 0.39312573270336554),
          3: (0.0, 756, 0.4699741397147749, 0.46997413971477486)}


def golden(seed: int) -> np.ndarray:
    """The panel the frozen numbers were computed on: 203 rows, 24 correlated columns."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.02 * seed, 1, (203, 24)) + 0.5 * rng.normal(0, 1, (203, 1))
    x[:, 3] += 0.15 * seed
    return x


def noise(seed: int, weeks: int = 400, width: int = 60, mean: float = 0.0,
          shared: float = 0.6) -> np.ndarray:
    """A panel with nothing to choose: fat tails, columns correlated `shared` through one factor."""
    rng = np.random.default_rng(seed)
    return (np.sqrt(shared) * rng.standard_t(5, (weeks, 1))
            + np.sqrt(1 - shared) * rng.standard_t(5, (weeks, width))) / np.sqrt(5 / 3) + mean


def run(values: np.ndarray, blocks: int = 10, track: int | None = None) -> dict:
    """One CSCV of a panel."""
    return cscv.run(cscv.sums(values, blocks), cscv.partitions(blocks), 64, BINS, REACH, track)


def by_rows(values: np.ndarray, blocks: int) -> dict:
    """The CSCV with nothing clever: rows concatenated, one partition at a time, both ways."""
    pieces = np.array_split(np.arange(len(values)), blocks)
    rows = {"pick": [], "sr_in": [], "sr_out": [], "omega": []}
    for half in cscv.partitions(blocks).astype(bool):
        for inside in (half, ~half):
            a = values[np.concatenate([p for p, use in zip(pieces, inside) if use])]
            b = values[np.concatenate([p for p, use in zip(pieces, inside) if not use])]
            sa, sb = (np.where(v.std(0, ddof=1) > 0, v.mean(0) / np.where(v.std(0, ddof=1) > 0,
                                                                         v.std(0, ddof=1), 1), 0)
                      for v in (a, b))
            pick = int(sa.argmax())
            rows["pick"].append(pick)
            rows["sr_in"].append(sa[pick])
            rows["sr_out"].append(sb[pick])
            rows["omega"].append(((sb < sb[pick]).sum() + 1) / (values.shape[1] + 1))
    return {k: np.array(v) for k, v in rows.items()}


def cfg_of(*overrides: str) -> dict:
    """The study's config with a small null, for tests."""
    return config.load(["null.draws=40", "perf.workers=8", *overrides])


def test_the_partitions_are_every_half_once() -> None:
    """C(15,7) = 6,435 halves hold the first block; with their complements, C(16,8) = 12,870."""
    member = cscv.partitions(16)
    assert member.shape == (6435, 16) and (member.sum(axis=1) == 8).all() and (member[:, 0] == 1).all()
    both = np.vstack([member, 1 - member])
    assert len(np.unique(both, axis=0)) == 12870


def test_the_vectorised_pbo_is_the_old_implementation_s() -> None:
    """§8.5.1: the frozen numbers of the deleted implementation, reproduced within 1e-4."""
    for seed, (pbo, picks, out, inside) in GOLDEN.items():
        found = run(golden(seed))
        assert abs(float((found["omega"] <= 0.5).mean()) - pbo) <= 1e-4, seed
        assert int(found["pick"].sum()) == picks
        assert np.isclose(found["sr_out"].mean(), out) and np.isclose(found["sr_in"].mean(), inside)


def test_block_sums_equal_concatenated_rows_partition_by_partition() -> None:
    """Unequal blocks, a column that never moves and one flat for half the history."""
    x = golden(1)
    x[:, 5] = 0.0
    x[:110, 7] = 0.0
    fast, slow = run(x, 8), by_rows(x, 8)
    order = np.lexsort((fast["sr_in"], fast["sr_out"])), np.lexsort((slow["sr_in"], slow["sr_out"]))
    for key in ("sr_in", "sr_out", "omega"):
        assert np.allclose(fast[key][order[0]], slow[key][order[1]], rtol=1e-9, atol=1e-12), key
    assert sorted(fast["pick"]) == sorted(slow["pick"])


def test_one_real_edge_reads_no_overfitting() -> None:
    """A column that truly earns: PBO near 0, the pick never loses, choosing dominates chance."""
    x = noise(3)
    x[:, 7] += 0.45
    said = outputs.summary(run(x), TOL)
    assert said["pbo"] < 0.02 and said["p_perdida"] < 0.02, said
    assert said["primer_orden"] and said["segundo_orden"] and said["hc"] < 0.5


def test_the_seesaw_without_resampling() -> None:
    """Means removed and nothing redrawn (Witzany's table 3): the pick loses outside whenever it won inside."""
    u = null.standard(noise(4))["u"]
    said = outputs.summary(run(u), TOL)
    assert said["p_perdida"] > 0.97 and said["pbo"] > 0.95 and said["beta"] < -0.8, said


def test_noise_loses_as_often_as_two_independent_halves_predict() -> None:
    """Halves of i.i.d. weeks are independent, so E[P(loss)] = Phi(-Sharpe x sqrt(weeks / 2))."""
    from scipy.stats import norm
    for mean, weeks in ((0.0, 400), (0.1, 400)):
        got = np.mean([outputs.summary(run(noise(s, weeks, 60, mean, 0.0)), TOL)["p_perdida"]
                       for s in range(60)])
        want = norm.cdf(-mean * np.sqrt(weeks / 2))
        print(f"     ruido puro, Sharpe semanal {mean}: P pérdida media {got:.3f}, predicha {want:.3f}")
        assert abs(got - want) < 0.06, (mean, got, want)


def test_dominance_against_all_variants_by_hand() -> None:
    """Four lists against «all» = {-1, +1} in equal parts, on 8 bins over [-2, 2)."""
    found = {"lo": -2.0, "hi": 2.0, "hist": np.array([0, 0, 50, 0, 0, 0, 50, 0])}
    better, same = np.full(10, 1.0), np.array([-1.0, 1.0] * 5)
    assert outputs.dominance(better, found, 0.0) == {"primer_orden": True, "segundo_orden": True, "brecha": 0.0}
    assert outputs.dominance(same, found, 0.0)["primer_orden"]
    worse = outputs.dominance(np.full(10, -1.0), found, 0.0)
    assert not worse["primer_orden"] and not worse["segundo_orden"] and worse["brecha"] == 0.5
    sure = outputs.dominance(np.zeros(10), found, 0.0)       # same mean, no spread
    assert not sure["primer_orden"] and sure["segundo_orden"] and sure["brecha"] == 0.5
    assert outputs.dominance(np.array([1.0] * 99 + [-1.5]), found, 0.01)["primer_orden"]   # tolerance


def test_the_null_equalises_every_column_to_the_median_sharpe() -> None:
    """u + m: each column's Sharpe is the panel's median one; redrawn sums are the panel's."""
    x = noise(5) + np.linspace(-0.1, 0.3, 60)
    shared = null.standard(x)
    z = shared["u"] + shared["m"]
    assert np.allclose(z.mean(0) / z.std(0, ddof=1), np.median(x.mean(0) / x.std(0, ddof=1)))
    rows = np.random.default_rng(1).integers(0, len(x), len(x))
    mean = np.full(60, shared["m"])
    mean[:6] += 0.02
    got, want = null.redrawn(shared, rows, mean, 10), cscv.sums((shared["u"] + mean)[rows], 10)
    assert all(np.allclose(got[k], want[k]) for k in ("n", "s1", "s2"))


def panels(count: int, width: int = 60, weeks: int = 400) -> dict:
    """Several no-edge mothers for the queue."""
    return {f"m{i}": {"net": noise(10 + i, weeks, width, 0.03), "track": 0,
                      "gross": noise(10 + i, weeks, width, 0.04)} for i in range(count)}


def test_same_seed_same_null_for_1_8_and_96_processes() -> None:
    """§8.5.2: every draw seeds its own stream, so the cut of the queue changes nothing."""
    got = [queue.run(panels(1), cfg_of(f"perf.workers={w}"))[0]["m0"]["draws"] for w in (1, 8, 96)]
    for other in got[1:]:
        for kind in got[0]:
            pd.testing.assert_frame_equal(got[0][kind], other[kind])
    alone = queue.run({"m1": panels(2)["m1"]}, cfg_of())[0]["m1"]["draws"]["nulo"]
    pd.testing.assert_frame_equal(alone, queue.run(panels(2), cfg_of())[0]["m1"]["draws"]["nulo"])


def test_the_null_centres_on_a_half_and_the_planted_edge_is_seen() -> None:
    """§8.5.3 and §8.5.4: null PBO median in 0.4-0.6 on no-edge panels; power grows with delta."""
    found, _ = queue.run(panels(6, 150, 784), cfg_of("null.draws=80", "perf.workers=96"))
    power = {}
    for name, got in found.items():
        pbo = got["draws"]["nulo"]["pbo"]
        assert 0.4 <= pbo.median() <= 0.6, (name, pbo.median())
        assert 0.4 <= got["draws"]["nulo_bruto"]["pbo"].median() <= 0.6
        power[name] = [float((got["draws"][k]["pbo"] < np.percentile(pbo, 5)).mean())
                       for k in ("d01", "d02", "d03")]
    mean = np.mean(list(power.values()), axis=0)
    print(f"     potencia media en 6 paneles sin ventaja (150 variantes, 784 semanas, 80 sorteos): "
          f"d=0,1 {mean[0]:.2f} · d=0,2 {mean[1]:.2f} · d=0,3 {mean[2]:.2f}")
    assert mean[2] > 0.25 and mean[2] > mean[0], mean


def test_the_queue_scales_with_the_processes() -> None:
    """§8.5.5, with a modest bound: the machine is shared. The real ratio is printed."""
    wall = {}
    for workers in (1, 96):
        began = time.time()
        queue.run({"m": {"net": noise(1, 784, 300, 0.03), "gross": noise(2, 784, 300, 0.03),
                         "track": None}}, cfg_of("null.draws=48", f"perf.workers={workers}"))
        wall[workers] = time.time() - began
    print(f"     240 CSCV de 300 variantes: {wall[1]:.1f} s con 1 proceso, {wall[96]:.1f} s con "
          f"{fanout.CORES} (pedidos 96): x{wall[1] / wall[96]:.1f}")
    assert wall[1] / wall[96] > 4, wall


def test_the_state_follows_the_proposal_s_table() -> None:
    """NO PASA on loss >= 0.5 or PBO over its p95; LIMBO on loss over its null's p95 or too few; else PASA."""
    cfg = cfg_of()
    base = {"n": 100, "p_perdida": 0.1, "pbo_sobre_p95": 0, "p_perdida_sobre_p95": 0}
    assert state.state(base, cfg) == "pasa"
    assert state.state(base | {"p_perdida": 0.45}, cfg) == "pasa"       # no fixed cut under 0.5
    assert state.state(base | {"p_perdida_sobre_p95": 1}, cfg) == "limbo"
    assert state.state(base | {"p_perdida": 0.5}, cfg) == "no_pasa"
    assert state.state(base | {"p_perdida": 0.5, "p_perdida_sobre_p95": 1}, cfg) == "no_pasa"
    assert state.state(base | {"pbo_sobre_p95": 1, "p_perdida_sobre_p95": 1}, cfg) == "no_pasa"
    assert state.state({"n": 29}, cfg) == "limbo"


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            began = time.time()
            test()
            print(f"  ok   {name} ({time.time() - began:.1f} s)")
    print("todas las propiedades se cumplen")
