#!/usr/bin/env python3
"""Encargo 66 §3.3, §3.5, §3.6: the ladder without `argsort` and on threads gives the bits it gave.

The oracle is the code as it was on 2026-10-12, copied here: the rungs that place with numpy
and the kernel that orders each run's exits with a stable `argsort`. Every case goes through
both and the five statistics must be equal as arrays. A second, independent oracle is the
closed form of the `timing` null's net: a sum of independent uniform placements."""

import sys
from pathlib import Path

import numpy as np
from numba import njit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import fanout
from engines.nulls import kernel, model, simulate

NAMES = list(kernel.NAMES)
CHUNK = 200_000


@njit(cache=True, nogil=True, error_model="numpy")
def old_runs(
    entries: np.ndarray,
    holds: np.ndarray,
    sizes: np.ndarray,
    enter_px: np.ndarray,
    leave_px: np.ndarray,
    cost: np.ndarray,
    value: float,
    out: np.ndarray,
) -> np.ndarray:
    """kernel.runs as it was before encargo 66, verbatim."""
    n_runs, n = entries.shape
    pnl = np.empty(n)
    for s in range(n_runs):
        net = gain = loss = 0.0
        for k in range(n):
            e = entries[s, k]
            p = (
                value * sizes[s, k] * (leave_px[e + holds[s, k]] - enter_px[e])
                - cost[k]
            )
            pnl[k] = p
            net += p
            if p > 0.0:
                gain += p
            elif p < 0.0:
                loss -= p
        curve = peak = dd = 0.0
        for k in np.argsort(entries[s] + holds[s], kind="mergesort"):  # exit order
            curve += pnl[k]
            peak = max(peak, curve)
            dd = max(dd, peak - curve)
        mean = net / n
        var = 0.0
        for k in range(n):
            var += (pnl[k] - mean) ** 2
        out[s, 0] = net
        out[s, 1] = mean / np.sqrt(var / (n - 1))
        out[s, 2] = gain / loss if loss > 0.0 else np.inf
        out[s, 3] = net / dd if dd > 0.0 else 0.0
        out[s, 4] = dd


def old_draw(located: dict, rung: str, draws: int, rng: np.random.Generator) -> tuple:
    """model.RUNGS[rung] as it was, but for the 2026-10-13 order (N12 B): the uniforms, then the redrawn holds."""
    lo, hi = located["window"]
    n = located["hold"].size
    u = rng.random((draws, n))  # the uniforms first, shared by the four (N12 B)
    if rung in ("timing_holds", "free"):
        holds = rng.choice(located["hold"], size=(draws, n), replace=True)
    else:
        holds = np.broadcast_to(located["hold"], (draws, n))
    entries = (lo + u * (hi - holds - lo + 1)).astype(np.int64)
    size = (
        located["size"].mean() if rung in ("timing_sizing", "free") else located["size"]
    )
    return entries, holds, np.broadcast_to(size, (draws, n))


def old_nulls(kept: dict, rung: str, cfg: dict, key: str) -> np.ndarray:
    """simulate.nulls as it was, serial, on the old rungs and the old kernel."""
    knobs = cfg["nulls"]
    root = [knobs["seed"], simulate._stable(key), simulate.TAG]
    block = max(1, knobs["chunk_trades"] // kept["located"]["entry"].size)
    out = np.empty((knobs["draws"], 5))
    for i, done in enumerate(range(0, knobs["draws"], block)):
        batch = min(block, knobs["draws"] - done)
        drawn = old_draw(
            kept["located"], rung, batch, np.random.default_rng(root + [i])
        )
        old_runs(
            *drawn,
            kept["bars"]["enter_px"],
            kept["bars"]["leave_px"],
            kept["cost"],
            kept["value"],
            out[done : done + batch],
        )
    return out


def new_nulls(
    kept: dict, rung: str, cfg: dict, key: str, threads: int | None = None
) -> np.ndarray:
    """`simulate.nulls` as one column per statistic."""
    got = simulate.nulls(kept, rung, cfg, key, threads)
    return np.column_stack([got[name] for name in NAMES])


def config(draws: int, seed: int = 77) -> dict:
    """The nulls config of these tests."""
    return {
        "nulls": {"seed": seed, "chunk_trades": CHUNK, "draws": draws},
        "statistics": {"report": NAMES},
        "barrier": {},
    }


def kept_of(
    entry: np.ndarray,
    hold: np.ndarray,
    bars: int,
    seed: int = 1,
    value: float = 100.0,
    window: tuple | None = None,
) -> dict:
    """What simulate.fixed() returns, by hand on a random walk."""
    r = np.random.default_rng(seed)
    px = 2000 + np.cumsum(r.normal(0, 2, bars))
    entry, hold = np.asarray(entry).astype(np.int64), np.asarray(hold).astype(np.int64)
    located = {
        "entry": entry,
        "exit": entry + hold,
        "hold": hold,
        "size": r.uniform(0.1, 2, entry.size),
        "window": window or (int(entry.min()), int((entry + hold).max())),
    }
    return {
        "located": located,
        "bars": {"enter_px": px, "leave_px": px + 0.1},
        "value": value,
        "cost": r.uniform(1, 5, entry.size),
        "levels": {},
    }


def rnd(
    r: np.random.Generator, n: int, bars: int, hmax: int, zero: float = 0.0
) -> tuple:
    """Sorted random entries and holds, a share `zero` of the holds being 0."""
    hold = np.minimum(1 + r.geometric(0.1, n), hmax)
    hold[r.random(n) < zero] = 0
    return np.sort(r.integers(5, bars - hmax - 5, n)), hold


def cases() -> dict:
    """The eleven adversarial strategies of the audit (verify/c.py), same construction."""
    r = np.random.default_rng(42)
    return {
        "shorts (value<0) n=500": kept_of(
            *rnd(r, 500, 60_000, 400), 60_000, value=-99.85
        ),
        "ties: n=5000 in 2000 bars": kept_of(*rnd(r, 5000, 2000, 60), 2000),
        "ties + 40% holds of 0": kept_of(*rnd(r, 5000, 2000, 60, 0.4), 2000),
        "all holds 0, n=3000/500 bars": kept_of(
            np.sort(r.integers(5, 495, 3000)), np.zeros(3000), 500
        ),
        "every exit on ONE bar": kept_of(np.full(800, 100), np.full(800, 50), 1000),
        "two exit bars only": kept_of(
            np.full(800, 100), np.full(800, 50), 1000, window=(100, 151)
        ),
        "n=2": kept_of([10, 4000], [3, 90], 5000),
        "n=3 in 60000 bars": kept_of([10, 30000, 59000], [3, 0, 400], 60_000),
        "n=1": kept_of([10], [7], 500, window=(10, 400)),
        "one huge hold + many tiny": kept_of(
            np.r_[10, np.sort(r.integers(20, 50_000, 999))],
            np.r_[55_000, r.integers(0, 3, 999)],
            60_000,
        ),
        "shorts + ties + zeros": kept_of(
            *rnd(r, 4000, 1500, 40, 0.3), 1500, value=-100.0
        ),
    }


def same(a: np.ndarray, b: np.ndarray) -> bool:
    """Equal as arrays; a NaN (the Sharpe of a one-trade run) equals a NaN."""
    return np.array_equal(a, b, equal_nan=True)


def test_adversarial_cases_bit_for_bit() -> None:
    """The adversarial cases match the old ladder bit for bit at 1 and 4 threads."""
    for label, kept in cases().items():
        block = max(1, CHUNK // kept["located"]["entry"].size)
        for draws in (
            2 * block + 7,
            max(1, block // 3),
        ):  # a partial last block; under one
            for rung in model.RUNGS:
                old = old_nulls(kept, rung, config(draws), "s")
                assert same(new_nulls(kept, rung, config(draws), "s", 1), old), (
                    label,
                    rung,
                )
                assert same(new_nulls(kept, rung, config(draws), "s", 4), old), (
                    label,
                    rung,
                )


def test_random_seeds_bit_for_bit() -> None:
    """Random seeds match the old ladder bit for bit."""
    r = np.random.default_rng(5)
    for seed in range(12):
        n = int(r.integers(2, 900))
        kept = kept_of(*rnd(r, n, 20_000, 300, 0.1), 20_000, seed=seed)
        for rung in model.RUNGS:
            cfg = config(int(r.integers(1, 3 * CHUNK // n)), seed)
            assert same(
                new_nulls(kept, rung, cfg, f"k{seed}"),
                old_nulls(kept, rung, cfg, f"k{seed}"),
            ), (seed, n, rung)


def test_runs_kernel_bit_for_bit() -> None:
    """kernel.runs (the real run, and whoever hands it entries) against the argsort one."""
    for label, kept in cases().items():
        for rung in model.RUNGS:
            drawn = old_draw(kept["located"], rung, 40, np.random.default_rng(3))
            tail = (
                kept["bars"]["enter_px"],
                kept["bars"]["leave_px"],
                kept["cost"],
                kept["value"],
            )
            old, new = np.empty((40, 5)), np.empty((40, 5))
            old_runs(*drawn, *tail, old)
            kernel.runs(*drawn, *tail, new)
            assert same(new, old), (label, rung)


def _resolved(_key: int) -> int:
    """How many blocks' worth of threads simulate.nulls takes inside a fanout worker."""
    seen = []
    spare, simulate.ThreadPoolExecutor = (
        simulate.ThreadPoolExecutor,
        lambda n: seen.append(n),
    )
    try:
        simulate.nulls(
            kept_of([10, 40, 90], [3, 5, 2], 500), "timing", config(CHUNK), "s"
        )
    finally:
        simulate.ThreadPoolExecutor = spare
    return len(seen)


def test_no_threads_inside_a_fanout_worker() -> None:
    """A fanout worker takes no threads for its blocks."""
    assert dict(fanout.run(_resolved, {0: 1, 1: 1}, 2)) == {0: 0, 1: 0}


def test_timing_net_against_its_closed_form() -> None:
    """Each trade lands uniform on its own lo..hi-hold and they are independent: mean and
    variance of the net are sums over trades of the mean and variance over those bars."""
    kept = kept_of(*rnd(np.random.default_rng(8), 300, 30_000, 200), 30_000, seed=4)
    at, bars = kept["located"], kept["bars"]
    lo, hi = at["window"]
    mu = var = 0.0
    for hold, size, cost in zip(at["hold"], at["size"], kept["cost"]):
        e = np.arange(lo, hi - hold + 1)
        v = (
            kept["value"] * size * (bars["leave_px"][e + hold] - bars["enter_px"][e])
            - cost
        )
        mu, var = mu + v.mean(), var + v.var()
    draws = 200_000
    got = simulate.nulls(kept, "timing", config(draws, 11), "oracle")["net"]
    assert abs(got.mean() - mu) < 5 * np.sqrt(var / draws), (got.mean(), mu)
    assert abs(got.std(ddof=1) / np.sqrt(var) - 1) < 5 / np.sqrt(2 * draws)


if __name__ == "__main__":
    import time

    kept = kept_of(*rnd(np.random.default_rng(1), 500, 60_000, 400), 60_000)
    for f in (old_nulls, new_nulls):
        f(kept, "free", config(50), "warm"), f(kept, "timing", config(50), "warm")
    for rung in ("timing", "free"):
        cfg, took = config(200_000), {}
        for label, f, extra in (
            ("old", old_nulls, ()),
            ("new 1 thread", new_nulls, (1,)),
            ("new 4 threads", new_nulls, (4,)),
            (f"new {fanout.CORES} threads", new_nulls, (None,)),
        ):
            t0 = time.perf_counter()
            f(kept, rung, cfg, "t", *extra)
            took[label] = time.perf_counter() - t0
        print(
            rung,
            "n=500, 200k draws:",
            ", ".join(
                f"{k} {v:.2f} s (x{took['old'] / v:.1f})" for k, v in took.items()
            ),
        )
