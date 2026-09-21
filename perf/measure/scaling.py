"""What this machine gives when every core asks for memory at once, which is the real ceiling."""

import os
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

import numpy as np

TRIAD_BYTES = 24  # two reads and one write of float64 per element, per pass


def triad(kb: float, passes: int) -> int:
    """A STREAM triad: read two vectors, scale one, add, write the result.

    Args:
        kb: Working set of all three vectors together, in kilobytes.
        passes: How many times the triad is run.

    Returns:
        Bytes moved. The standard memory-bandwidth kernel, chosen because it does almost no
        arithmetic: whatever it takes longer than, it took waiting for memory.
    """
    os.environ["OMP_NUM_THREADS"] = "1"
    n = max(int(kb * 1024 / TRIAD_BYTES), 1)
    a, b, c = (np.ones(n), np.ones(n), np.ones(n))
    for _ in range(passes):
        np.add(b, c * 1.5, out=a)
    return n * TRIAD_BYTES * passes


def _job(args: tuple) -> int:
    """One worker's share of a sweep point."""
    return triad(*args)


def sweep(cfg: dict, kb: float) -> list[dict]:
    """The same kernel run by one process, then by two, then by every core.

    Args:
        cfg: What config.load() returned.
        kb: Working set per process, in kilobytes.

    Returns:
        One row per worker count with the aggregate GB/s and the speedup over one process.
        Run this at a cache-resident size and at a DRAM-resident size: the gap between the
        two curves is the part of the machine that cores cannot buy back.

        Passes are set so both sizes move the same total bytes. Without that the small
        working set finishes in microseconds and the curve measures pool dispatch instead
        of memory.
    """
    passes = max(round(cfg["scaling"]["probe_passes"] * cfg["scaling"]["probe_mb"] * 1024
                       / kb), 1)
    ctx = get_context("forkserver")
    ctx.set_forkserver_preload(["perf.measure.scaling"])
    out = []
    for workers in cfg["scaling"]["workers"]:
        if workers > (os.cpu_count() or 1):
            continue
        with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
            args = [(kb, passes)] * workers
            list(pool.map(_job, args[:workers]))          # warm the pool before the clock
            start = time.perf_counter()
            moved = sum(pool.map(_job, args))
            elapsed = time.perf_counter() - start
        out.append({"workers": workers, "gb_s": moved / elapsed / 1e9})
    return [r | {"speedup": r["gb_s"] / out[0]["gb_s"]} for r in out]


def machine(cfg: dict) -> dict:
    """Both curves plus what the machine says about itself.

    Args:
        cfg: What config.load() returned.

    Returns:
        `cache` and `dram`, the two sweeps, and `cores`. A cache curve that scales and a
        DRAM curve that flattens is the signature of a kernel whose working set is too big:
        adding workers past the flattening point buys nothing and costs memory.
    """
    return {"cores": os.cpu_count(),
            "cache": sweep(cfg, cfg["scaling"]["small_kb"]),
            "dram": sweep(cfg, cfg["scaling"]["probe_mb"] * 1024)}
