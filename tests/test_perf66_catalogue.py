"""Encargo 66 §10: the catalogue measures right (tracemalloc off in timings, PSS, first touch outside the clock)."""

import multiprocessing as mp
from multiprocessing.synchronize import Event
import os
import time
import tracemalloc

import numpy as np
import pytest

from perf.measure import harness, runner, scaling


def test_tracemalloc_off_in_timing_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """A timing run does not trace allocations; a memtop run does."""
    seen = {}

    def call(cfg: dict) -> dict:
        """Record whether tracemalloc is on."""
        seen["on"] = tracemalloc.is_tracing()
        return {"scale": 1, "bytes_in": 0}

    monkeypatch.setitem(runner.TARGETS, "t", {"call": call})
    cfg = {"harness": {"sample_ms": 10}}
    r = runner.measure("t", cfg)
    assert seen["on"] is False and r["alloc_peak_mb"] is None
    r = runner.measure("t", cfg, memtop=3)
    assert (
        seen["on"] is True
        and r["alloc_peak_mb"] is not None
        and not tracemalloc.is_tracing()
    )


def test_timing_unchanged_by_memory_pass_for_numpy_free_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The memory pass leaves the wall time of numpy-free code alone."""

    def call(cfg: dict) -> dict:
        """Busy-wait 50 ms."""
        t = time.perf_counter()
        while time.perf_counter() - t < 0.05:
            pass
        return {"scale": 1, "bytes_in": 0}

    monkeypatch.setitem(runner.TARGETS, "t", {"call": call})
    cfg = {"harness": {"sample_ms": 10}}
    # the fastest of five each: a busy-wait preempted under load only ever runs longer
    plain = min(runner.measure("t", cfg)["wall_s"] for _ in range(5))
    traced = min(runner.measure("t", cfg, 1)["wall_s"] for _ in range(5))
    assert abs(plain - traced) < 0.02, (plain, traced)


def _child(ready: Event, go: Event) -> None:
    """Signal ready, then wait for go."""
    ready.set()
    go.wait(20)


def test_pss_counts_shared_pages_once() -> None:
    """PSS of a forked tree counts shared pages once, unlike summed RSS."""
    big = np.ones(200 * 1024 * 1024 // 8)  # 200 MB, written
    ctx = mp.get_context("fork")
    ready, go = [ctx.Event() for _ in range(4)], ctx.Event()
    kids = [ctx.Process(target=_child, args=(r, go)) for r in ready]
    for k in kids:
        k.start()
    for r in ready:
        r.wait(10)
    pss = harness._tree_rss(os.getpid())
    rss = sum(
        int(open(f"/proc/{k.pid}/statm").read().split()[1]) * 4096 / 2**20 for k in kids
    )
    go.set()
    for k in kids:
        k.join()
    assert big[0] == 1
    assert rss > 700  # summed RSS of the children alone is the old inflated figure
    assert (
        pss < 450
    )  # PSS of parent + 4 children: ~200 MB shared once plus interpreters


def test_first_touch_outside_the_clock() -> None:
    """The buffers of the scaling triad are touched before the clock starts."""
    scaling._prepare(8192)
    assert len(scaling._BUF) == 3
    t = time.perf_counter()
    scaling.triad(8192, 1)
    warm = time.perf_counter() - t
    scaling._BUF = ()
    t = time.perf_counter()
    scaling.triad(8192, 1)
    cold = time.perf_counter() - t
    assert warm < cold
