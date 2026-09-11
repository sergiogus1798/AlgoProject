"""Run one simulated sub-test across every core, and say how far along it is while it does."""

import multiprocessing
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from strategies.monteCarlo import draws, metrics, stress

ARRAYS = ("pnl", "cost", "spread", "mae")

_POOL = None   # the one pool this process ever builds; see pool()

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
        context = multiprocessing.get_context("forkserver")
        context.set_forkserver_preload(["strategies.monteCarlo.engine"])
        _POOL = ProcessPoolExecutor(max_workers=cfg["global"]["max_workers"] or os.cpu_count(),
                                    mp_context=context)
    return _POOL


def _batch(job: tuple) -> dict[str, np.ndarray]:
    """One worker's share of the simulations.

    Args:
        job: (kind, model, block, simulations, payload, starting equity, family_c config).

    Returns:
        One array per statistic. The generator is seeded from the operating system inside
        the worker, so every batch draws independent fresh entropy and no two workers can
        share a stream. Runs are deliberately not reproducible — section 9 measures the
        run-to-run spread instead of hiding it behind a seed.
    """
    kind, model, block, n, data, equity0, cfg_c = job
    rng = np.random.default_rng()
    if kind == "draw":
        pnl = data["pnl"][draws.DRAWS[model](n, data["pnl"].size, rng, block)]
    else:
        pnl = stress.STRESS[model](data, n, rng, cfg_c)
    return metrics.paths(pnl, equity0)


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
    return _batch((kind, model, block, n_sims, data, cfg["global"]["starting_equity"],
                   cfg["family_c"]))


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
        One array of length n_sims per statistic of metrics.NAMES. Chunking is a memory
        decision and not a statistical one: the percentile engine runs once, in the parent,
        over the whole pool.
    """
    g = cfg["global"]
    chunks = [min(g["chunk"], n_sims - i) for i in range(0, n_sims, g["chunk"])]
    jobs = [("draw" if kind == "draw" else "stress", model, block, c, data,
             g["starting_equity"], cfg["family_c"]) for c in chunks]
    started, done, out = time.time(), 0, []
    workers = pool(cfg)
    futures = {workers.submit(_batch, j): j[3] for j in jobs}
    for f in as_completed(futures):
        out.append(f.result())
        done += futures[f]
        _progress(done, n_sims, title, started, g["progress_update_pct"])
    if sys.stdout.isatty():
        print()
    return {k: np.concatenate([o[k] for o in out]) for k in metrics.NAMES}
