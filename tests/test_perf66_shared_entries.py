"""Encargo 66, N12 B (owner, 2026-10-13): the four rungs of the monkey share their random entries.

One stream per strategy (and block) serves `timing`, `timing_holds`, `timing_sizing` and `free`:
the uniforms that place the entries come first and are the same for the four, the redrawn holds
come second and are the same for the two rungs that redraw them. A rung maps a uniform onto the
bars ITS hold leaves room for, so each rung alone is the null it was; only the coupling moves.
The reference of (b) is the per-rung procedure as it stood at 9ec2c34, kept only here."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engines.nulls import kernel, lookup, model, simulate, windowed
from studies.screening.analysis import resample
from test_perf66_kernel import COSTS, grid as windowed_grid, scattered
from test_perf66_ladder import config, kept_of, rnd

RUNGS = tuple(model.RUNGS)
OLD_ID = {"timing": 1, "timing_holds": 2, "timing_sizing": 3, "free": 4}   # the old per-rung seed part


def old_nulls(kept: dict, rung: str, cfg: dict, key: str) -> np.ndarray:
    """The net of every monkey as the per-rung procedure drew it: own seed, holds before uniforms."""
    knobs, loc = cfg["nulls"], kept["located"]
    lo, hi = loc["window"]
    n = loc["entry"].size
    block = max(1, knobs["chunk_trades"] // n)
    out = np.empty((knobs["draws"], 5))
    for i, done in enumerate(range(0, knobs["draws"], block)):
        batch = min(block, knobs["draws"] - done)
        rng = np.random.default_rng([knobs["seed"], simulate._stable(key), OLD_ID[rung], i])
        holds = (rng.choice(loc["hold"], size=(batch, n), replace=True)
                 if rung in ("timing_holds", "free") else np.broadcast_to(loc["hold"], (batch, n)))
        entries = (lo + rng.random((batch, n)) * (hi - holds - lo + 1)).astype(np.int64)
        size = loc["size"].mean() if rung in ("timing_sizing", "free") else loc["size"]
        kernel.runs(entries, holds, np.broadcast_to(size, (batch, n)), kept["bars"]["enter_px"],
                    kept["bars"]["leave_px"], kept["cost"], kept["value"], out[done:done + batch])
    return out[:, 0]


def new_nulls(kept: dict, rung: str, cfg: dict, key: str = "k") -> np.ndarray:
    """The net of every monkey of the shared stream."""
    return simulate.nulls(kept, rung, cfg, key, 1)["net"]


def small() -> dict:
    """A 60-trade strategy on a random walk, holds of 1 to ~40 bars, window of 20,000 bars."""
    return kept_of(*rnd(np.random.default_rng(4), 60, 20_000, 40), 20_000, seed=4)


def test_a_entries_are_shared() -> None:
    """(a) Same seed: the uniforms of the four rungs are one array; entries follow the hold."""
    loc = small()["located"]
    drawn = {r: model.RUNGS[r](loc, 500, np.random.default_rng([9, 1]), placed=False) for r in RUNGS}
    for r in RUNGS:
        assert np.array_equal(drawn[r]["u"], drawn["timing"]["u"]), r
    assert np.array_equal(drawn["timing_holds"]["holds"], drawn["free"]["holds"])
    placed = {r: model.RUNGS[r](loc, 500, np.random.default_rng([9, 1])) for r in RUNGS}
    assert np.array_equal(placed["timing"]["entries"], placed["timing_sizing"]["entries"])
    assert np.array_equal(placed["timing_holds"]["entries"], placed["free"]["entries"])
    flat = dict(loc, hold=np.full(loc["hold"].size, 7))        # one hold for all: the four are one
    same = [model.RUNGS[r](flat, 500, np.random.default_rng([9, 1]))["entries"] for r in RUNGS]
    assert all(np.array_equal(same[0], e) for e in same)


def test_a_windowed_entries_are_shared() -> None:
    """(a) The gate's windowed monkey: same generator state, same entries wherever the hold is the same."""
    shared = windowed_grid()
    mine = scattered(shared, 120)
    mine["hold"][:] = 5                                        # a redrawn hold of 5 is the trade's own
    got = {r: windowed.draw(shared, mine, r, 300, np.random.default_rng([3, 1])) for r in RUNGS}
    for r in RUNGS:
        assert np.array_equal(got[r]["entries"], got["timing"]["entries"]), r
    mine = scattered(shared, 120)
    got = {r: windowed.draw(shared, mine, r, 300, np.random.default_rng([3, 1])) for r in RUNGS}
    assert np.array_equal(got["timing"]["entries"], got["timing_sizing"]["entries"])
    assert np.array_equal(got["timing_holds"]["entries"], got["free"]["entries"])


def test_b_each_rung_keeps_its_law() -> None:
    """(b) Per rung, the net's mean and quantiles equal the old per-rung procedure's, within MC error."""
    kept, cfg = small(), config(40_000, 5)
    for rung in RUNGS:
        old, new = old_nulls(kept, rung, cfg, "k"), new_nulls(kept, rung, cfg)
        sd = old.std()
        assert abs(old.mean() - new.mean()) < 5 * sd * np.sqrt(2 / old.size), rung
        for q in (0.05, 0.25, 0.5, 0.75, 0.95):
            assert abs(np.quantile(old, q) - np.quantile(new, q)) < 0.05 * sd, (rung, q)
        assert 0.97 < new.std() / sd < 1.03, rung


def test_b_windowed_rung_keeps_its_law() -> None:
    """(b) The windowed rungs: shared stream against an independent stream per rung, same law."""
    shared = windowed_grid()
    mine = scattered(shared, 80)
    for rung in RUNGS:
        a = windowed.means(shared, mine, COSTS, rung, 30_000, resample.stream(1, "x"))
        b = windowed.means(shared, mine, COSTS, rung, 30_000, resample.stream(2, f"x|{rung}"))
        assert abs(a.mean() - b.mean()) < 5 * a.std() * np.sqrt(2 / a.size), rung
        for q in (0.05, 0.5, 0.95):
            assert abs(np.quantile(a, q) - np.quantile(b, q)) < 0.06 * a.std(), (rung, q)


def test_c_paired_difference_is_tighter() -> None:
    """(c) The difference between two rungs varies less on shared entries than on independent ones."""
    kept, cfg = small(), config(40_000, 5)
    for a, b in (("timing", "timing_sizing"), ("timing_holds", "free"), ("timing", "timing_holds")):
        paired = new_nulls(kept, a, cfg) - new_nulls(kept, b, cfg)
        apart = old_nulls(kept, a, cfg, "k") - old_nulls(kept, b, cfg, "k")
        assert paired.var() < 0.7 * apart.var(), (a, b, paired.var() / apart.var())


def test_d_reproducible_and_only_replays() -> None:
    """(d) Same seed, same output; one rung drawn alone gets the entries the full run gave it."""
    kept, cfg = small(), config(3_000, 11)
    for rung in RUNGS:
        assert np.array_equal(new_nulls(kept, rung, cfg), new_nulls(kept, rung, cfg)), rung
    shared = windowed_grid()
    mine = scattered(shared, 60)
    table = {r: windowed.priced(shared, mine, COSTS, r) for r in RUNGS}
    full = {r: lookup.means(table[r], 400, resample.stream(7, "id")) for r in RUNGS}   # level3c's key: no rung in it
    for rung in RUNGS[::-1]:                                   # `--only`: one rung, any order
        assert np.array_equal(lookup.means(table[rung], 400, resample.stream(7, "id")), full[rung])
    again = {r: windowed.means(shared, mine, COSTS, r, 400, resample.stream(7, "id")) for r in RUNGS}
    assert all(np.array_equal(again[r], full[r]) for r in RUNGS)
    other = lookup.means(table["timing"], 400, resample.stream(8, "id"))
    assert not np.array_equal(other, full["timing"])           # another root, other entries
