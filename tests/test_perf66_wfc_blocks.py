#!/usr/bin/env python3
"""3.9d: the wfc null read in blocks of draws equals the whole-matrix reading and holds a fraction of its memory."""

import sys
import tracemalloc
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.weekly import flip
from studies.optimisation.wfc.inputs import config
from studies.optimisation.wfc.measure import level, reading


def whole(
    e_is: dict, e_oos: dict, weeks: dict, years: float, cfg: dict, straddle: float = 0.0
) -> dict:
    """The retired reference: draws x variants held whole (rho, tails with `nulo_p5/p95`, level, r_sel, wide blocks)."""
    knobs = cfg["null"]
    main, wide = np.random.SeedSequence(knobs["seed"]).spawn(2)
    signs = flip.signs(main, knobs["draws"], len(weeks["gross"]), knobs["block_weeks"])
    rho = float(flip.spearman(e_is["gross"], e_oos["gross"]))
    spread = flip.spearman(e_is["gross"], signs @ weeks["gross"])
    flat = signs @ weeks["net"] / years
    best = level.top(e_is["net"], cfg["level"]["top_share"])
    tops = np.median(flat[:, best], axis=1)
    obs = float(np.median(e_oos["net"][best]))
    kept = level.retention(
        e_is["net"], e_oos["net"], best, cfg["level"]["r_sel_min_gap"]
    )
    low, high = (
        (None, None)
        if kept is None
        else np.percentile(
            level.retention(e_is["net"], flat, best, cfg["level"]["r_sel_min_gap"]),
            [5, 95],
        )
    )
    blocked = {"p_mas_bloque": None, "p_menos_bloque": None}
    if straddle > knobs["straddle_warn"]:
        again = flip.signs(
            wide, knobs["draws"], len(weeks["gross"]), cfg["annotate"]["block_weeks"]
        )
        tail = flip.tails(rho, flip.spearman(e_is["gross"], again @ weeks["gross"]))
        blocked = {"p_mas_bloque": tail["p_mas"], "p_menos_bloque": tail["p_menos"]}
    return {
        "rho": rho,
        **flip.tails(rho, spread),
        "p_nivel": float((1 + (tops >= obs).sum()) / (1 + len(tops))),
        "r_sel_p5": low,
        "r_sel_p95": high,
        **blocked,
    }


def panel(weeks: int, variants: int, seed: int) -> tuple:
    """In-sample, out-of-sample and weekly excess of a random panel."""
    rng = np.random.default_rng(seed)
    gross = rng.normal(0.1, 1.0, (weeks, variants)) + rng.normal(0, 1.0, (weeks, 1))
    wk = {"gross": gross, "net": gross - 0.05}
    return (
        {"gross": rng.normal(size=variants), "net": rng.normal(size=variants)},
        {k: v.sum(axis=0) / 2.0 for k, v in wk.items()},
        wk,
    )


@pytest.mark.parametrize("weeks,variants", [(40, 30), (120, 200), (80, 7), (260, 64)])
def test_blocks_equal_the_whole_matrix(
    monkeypatch: pytest.MonkeyPatch, weeks: int, variants: int
) -> None:
    """rho, p_mas, p_menos and p_nivel within 1e-12 relative, with a block that cuts the draws unevenly."""
    cfg = config.load(["null.draws=1300"])
    monkeypatch.setattr(reading, "BLOCK", 400)
    for seed in range(3):
        e_is, e_oos, wk = panel(weeks, variants, seed)
        for straddle in (0.0, 1.0):  # 1.0 is above `straddle_warn`: the wide-block path
            got = reading.measure(e_is, e_oos, wk, 2.0, cfg, straddle)
            want = whole(e_is, e_oos, wk, 2.0, cfg, straddle)
            assert (want["p_mas_bloque"] is None) == (straddle == 0.0)
            for key, value in want.items():
                assert got[key] == (
                    pytest.approx(value, rel=1e-12, abs=1e-15)
                    if value is not None
                    else None
                ), key


def test_peak_memory_is_under_a_quarter(monkeypatch: pytest.MonkeyPatch) -> None:
    """tracemalloc peak of the blocks against the whole matrix, 20,000 draws x 600 variants."""
    cfg = config.load(["null.draws=20000"])
    e_is, e_oos, wk = panel(52, 600, 1)
    monkeypatch.setattr(reading, "BLOCK", 1000)
    peaks = []
    for run in (
        lambda: reading.measure(e_is, e_oos, wk, 2.0, cfg),
        lambda: whole(e_is, e_oos, wk, 2.0, cfg),
    ):
        tracemalloc.start()
        run()
        peaks.append(tracemalloc.get_traced_memory()[1])
        tracemalloc.stop()
    print(f"peak blocks {peaks[0] / 1e6:.0f} MB, whole {peaks[1] / 1e6:.0f} MB")
    assert peaks[0] < peaks[1] / 4
