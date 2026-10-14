"""Run one target inside its own process and report what it cost. Internal to the harness."""

import argparse
import cProfile
import json
import os
import resource
import threading
import time
import tracemalloc

import psutil
from pathlib import Path

from perf.inputs import config
from perf.inputs.targets import TARGETS
from perf.measure import harness

MB = 1024 * 1024


def _cpu() -> float:
    """CPU seconds of this process and every process under it, alive or already reaped."""
    alive = 0.0
    for child in psutil.Process().children(recursive=True):
        try:
            alive += sum(child.cpu_times()[:2])
        except psutil.Error:        # gone between the listing and the read: os.times() has it
            pass
    return sum(os.times()[:4]) + alive


def _watch(state: dict, done: threading.Event, every: float) -> None:
    """Keep the allocation sites from the instant Python was holding the most.

    Args:
        state: Mutated in place; carries the largest size seen and its snapshot.
        done: Set by the caller when the target has returned.
        every: Seconds between checks.

    A snapshot taken after the call has returned shows what survived, which is close to
    nothing and tells you nothing. The sites that matter are the ones alive at the peak, so
    they have to be caught while the peak is still standing.
    """
    while not done.wait(every):
        size = tracemalloc.get_traced_memory()[0]
        if size > state["size"]:
            state["size"], state["snap"] = size, tracemalloc.take_snapshot()


def measure(name: str, cfg: dict, memtop: int = 0) -> harness.Measured:
    """Call one target once, with the clock and the allocator watching.

    Args:
        name: Target name as the registry spells it.
        cfg: What config.load() returned.
        memtop: How many allocation sites to report, largest first; 0 to report none.

    Returns:
        Wall seconds, CPU seconds of the whole process tree (workers included), peak Python allocation (None unless memtop > 0: tracemalloc is off in a timing run) and peak RSS of this process, plus the
        scale and bytes the target reported. `alloc_peak_mb` counts only what Python
        allocated here: numpy buffers inside a worker process are invisible to it, which is
        why the harness samples the whole tree's RSS as well.
    """
    if memtop:      # tracemalloc slows object-heavy code up to x1,8: only when memory is asked for
        tracemalloc.start()
    state, done = {"size": 0, "snap": None}, threading.Event()
    watcher = threading.Thread(target=_watch, args=(state, done,
                                                    cfg["harness"]["sample_ms"] / 1000))
    if memtop:
        watcher.start()
    wall, cpu = time.perf_counter(), _cpu()
    out = TARGETS[name]["call"](cfg)
    wall, cpu = time.perf_counter() - wall, _cpu() - cpu
    done.set()
    if memtop:
        watcher.join()
    alloc, sites = None, []
    if memtop:
        alloc = tracemalloc.get_traced_memory()[1] / MB
        sites = [f"{s.traceback[0]}  {s.size / MB:.1f} MB"
                 for s in state["snap"].statistics("lineno")[:memtop]] if state["snap"] else []
        tracemalloc.stop()
    return {"wall_s": wall, "cpu_s": cpu, "alloc_peak_mb": alloc, "alloc_top": sites,
            "self_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            "scale": out["scale"], "bytes_in_mb": out["bytes_in"] / MB}


def main() -> None:
    """Measure the named target and write the result as JSON."""
    ap = argparse.ArgumentParser(description="Run one perf target; used by the harness.")
    ap.add_argument("target")
    ap.add_argument("--out", required=True, help="where the JSON result is written")
    ap.add_argument("--profile", help="also dump cProfile statistics to this path")
    ap.add_argument("--memtop", type=int, default=0, help="report this many allocation sites")
    ap.add_argument("--set", action="append", default=[], help="config override, dotted.key=value")
    a = ap.parse_args()
    cfg = config.load(a.set)
    if a.profile:
        prof = cProfile.Profile()
        prof.enable()
        out = measure(a.target, cfg, a.memtop)
        prof.disable()
        prof.dump_stats(a.profile)
    else:
        out = measure(a.target, cfg, a.memtop)
    Path(a.out).write_text(json.dumps(out), encoding="utf-8")


if __name__ == "__main__":
    main()
