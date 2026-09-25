"""Run one simulated sub-test across every core, and say how far along it is while it does."""

import multiprocessing
import os
import sys
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from portfolio.common.monteCarlo.simulate import metrics, tiles

ARRAYS = ("pnl", "cost", "spread", "mae")

_POOL = None   # the one pool this process ever builds; see pool()
# True inside a worker that already is one strategy's whole process: run() then walks its
# chunks here instead of asking a pool, so the parallelism is across strategies and never
# a pool nested inside a pool.
SERIAL = False

# The interactive panel points this at a function(done, total, title) to get the progress
# the terminal would print. The command leaves it None and the bar goes to the terminal.
# One sub-test runs at a time, so one hook is enough.
PROGRESS = None


def payload(stream: dict, positions: np.ndarray | None = None) -> dict:
    """The part of a stream a worker process needs.

    Args:
        stream: What stream.build() returned.
        positions: Trades to keep, or None for all of them. Subsets are how the IS/OOS
            comparison, the rolling windows and the regime buckets reuse the same engine.

    Returns:
        Only the numeric arrays. The source frame stays in the parent: sending a pandas
        frame to ninety-six workers costs more than the simulation it carries.
    """
    if positions is None:
        return {k: stream[k] for k in ARRAYS}
    return {k: stream[k][positions] for k in ARRAYS}


def pool(cfg: dict) -> ProcessPoolExecutor:
    """The process pool, built once and reused for the life of the process.

    Args:
        cfg: The whole config; its max_workers cap is read the first time only.

    Returns:
        The pool. Two reasons it is not built per sub-test. It was costing a pool of ninety-six
        workers for each of the nineteen sub-tests of every strategy; and the panel runs its
        jobs on a thread, where the default `fork` start method can inherit a held lock and
        deadlock the whole run — which it did. `forkserver` forks the workers from a clean
        single-threaded process instead, and preloading this module means they start with
        numpy already imported.
    """
    global _POOL
    if _POOL is None:
        # Windows has no forkserver (get_all_start_methods() there is just ["spawn"]) --
        # tested: get_context("forkserver") raises ValueError: cannot find context for
        # 'forkserver'. spawn starts each worker from a clean interpreter too, so it is not
        # exposed to the held-lock deadlock fork was replaced for; it just cannot preload a
        # module, so the workers import numpy on first use instead of at start-up.
        method = ("forkserver" if "forkserver" in multiprocessing.get_all_start_methods()
                  else "spawn")
        context = multiprocessing.get_context(method)
        if method == "forkserver":
            context.set_forkserver_preload(["portfolio.common.monteCarlo.simulate.engine"])
        _POOL = ProcessPoolExecutor(max_workers=cfg["global"]["max_workers"] or os.cpu_count(),
                                    mp_context=context)
    return _POOL


def mapped(fn: Callable, *iterables: Iterable, cfg: dict) -> list:
    """`map` over the pool, or right here inside a worker that already is one strategy's.

    Args:
        fn: A module-level function.
        iterables: Its arguments, one iterable per parameter.
        cfg: The whole config, for the pool's size.

    Returns:
        The results, in order.
    """
    return list(map(fn, *iterables) if SERIAL else pool(cfg).map(fn, *iterables))


def close() -> None:
    """Shut the pool down, so this process can fork without a pool's threads inside it."""
    global _POOL
    if _POOL is not None:
        _POOL.shutdown()
        _POOL = None


def _progress(done: int, total: int, title: str, started: float, step: int) -> None:
    """Print how far the current sub-test has got.

    Args:
        done: Simulations finished.
        total: Simulations requested.
        title: What is running, in the words the report uses.
        started: time.time() when it started.
        step: Report granularity in percent.

    Returns:
        Nothing. Writes a bar to a terminal and a plain line to a redirected stream, so a
        headless run on the server leaves a readable log instead of thousands of controls.
    """
    if PROGRESS is not None:
        PROGRESS(done, total, title)
        return
    share = done / total
    left = (time.time() - started) * (1 - share) / max(share, 1e-9)
    counts = f"{done:>{len(f'{total:,}')},}/{total:,}"
    if sys.stdout.isatty():
        bar = "#" * int(share * 24)
        print(f"\r  {title:<46.46} |{bar:<24}| {share:5.1%} {counts} {left:4.0f}s",
              end="", flush=True)
    elif done == total or int(share * 100) % max(step, 1) == 0:
        print(f"  {title} {share:.0%} {counts}", flush=True)


def single(data: dict, kind: str, model: str, block: int, n_sims: int, cfg: dict) -> dict:
    """Simulate one small sub-test here, without starting a pool.

    Args:
        data: What payload() returned.
        kind: "draw" or "stress".
        model: Key of draws.DRAWS or stress.STRESS.
        block: Block length, ignored by the models that have none.
        n_sims: Simulations to run.
        cfg: The whole config.

    Returns:
        The same arrays run() returns. Fifty rolling windows of two thousand draws each are
        cheaper in this process than fifty process pools are to start.
    """
    g = cfg["global"]
    return tiles.batch((kind, model, block, n_sims, data, g["starting_equity"],
                        cfg["family_c"], g["tile_bytes"]))


def sequential(data: dict, kind: str, model: str, block: int, n_sims: int, cfg: dict) -> dict:
    """Simulate one sub-test here, in chunks, without starting a pool.

    Args:
        data: What payload() returned.
        kind: "draw" or "stress".
        model: Key of draws.DRAWS or stress.STRESS.
        block: Block length, ignored by the models that have none.
        n_sims: Simulations to run.
        cfg: The whole config.

    Returns:
        The same arrays run() returns. It still walks the count in chunks so that this path
        and run() ask the kernel for the same shape of batch; what bounds the memory is the
        strip inside tiles.batch(), and it bounds it here exactly as it does in a worker —
        stability.py runs eight of these at once inside their own processes.
    """
    g = cfg["global"]
    chunks = [min(g["chunk"], n_sims - i) for i in range(0, n_sims, g["chunk"])]
    out = [tiles.batch((kind, model, block, c, data, g["starting_equity"], cfg["family_c"],
                        g["tile_bytes"])) for c in chunks]
    return {k: np.concatenate([o[k] for o in out]) for k in metrics.NAMES}


def run(data: dict, kind: str, model: str, block: int, n_sims: int, cfg: dict,
        title: str) -> dict:
    """Simulate one sub-test and collect its statistics.

    Args:
        data: What payload() returned.
        kind: "draw" for a reordering or resampling model, "stress" for a Family C one.
        model: Key of draws.DRAWS or stress.STRESS.
        block: Block length, ignored by the models that have none.
        n_sims: Simulations to run.
        cfg: The whole config.
        title: What to call this sub-run on the progress bar.

    Returns:
        One array of length n_sims per statistic of metrics.NAMES. Chunking is task
        granularity and not a statistical decision: the percentile engine runs once, in the
        parent, over the whole pool. What a worker costs in memory is tile_bytes, not chunk.
    """
    if SERIAL:
        return sequential(data, kind, model, block, n_sims, cfg)
    g = cfg["global"]
    chunks = [min(g["chunk"], n_sims - i) for i in range(0, n_sims, g["chunk"])]
    jobs = [("draw" if kind == "draw" else "stress", model, block, c, data,
             g["starting_equity"], cfg["family_c"], g["tile_bytes"]) for c in chunks]
    started, done, out = time.time(), 0, []
    workers = pool(cfg)
    futures = {workers.submit(tiles.batch, j): j[3] for j in jobs}
    for f in as_completed(futures):
        out.append(f.result())
        done += futures[f]
        _progress(done, n_sims, title, started, g["progress_update_pct"])
    if sys.stdout.isatty():
        print()
    return {k: np.concatenate([o[k] for o in out]) for k in metrics.NAMES}
