"""Independent tasks across processes, the costliest first, each result handed back as it lands."""

from collections.abc import Callable, Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context

from threadpoolctl import threadpool_limits


def run(work: Callable, costs: dict, workers: int) -> Iterator[tuple]:
    """Run `work(key)` for every key, the most expensive first, on up to `workers` processes.

    Args:
        work: A module-level function of one task key. It reads whatever else it needs from
            module state the caller set before calling this, which `fork` hands every worker
            without pickling.
        costs: Task key to its expected cost, in any unit; only the order matters.
        workers: Most processes to use.

    Returns:
        (key, result) pairs in the order they finish. The queue is fed longest-first, the
        LPT rule. 🔬 2026-09-25, from 24 processes up `crossmarket.report` on 96 strategies
        was bounded by its single largest task, 453 s alone; a task that long started late
        adds its whole length to the tail, and started first it overlaps everything else.

        One BLAS thread per process: OpenBLAS starts 64 in each, and 96 forked workers
        would otherwise contend with 6,144 of them the moment any calls into it.
    """
    order = sorted(costs, key=costs.get, reverse=True)
    with threadpool_limits(1), ProcessPoolExecutor(
            max_workers=max(1, min(workers, len(order))), mp_context=get_context("fork")) as pool:
        pending = {pool.submit(work, key): key for key in order}
        for done in as_completed(pending):
            yield pending[done], done.result()
