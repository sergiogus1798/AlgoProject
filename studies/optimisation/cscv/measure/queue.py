"""One queue for every CSCV of a run: mothers x (real, null on net and on gross, each planted Sharpe) x draws."""

import resource
import time
from collections.abc import Callable, Hashable
from typing import Any, TypedDict, TypeVar

import numpy as np
import pandas as pd

from core import fanout
from studies.optimisation.cscv.measure import cscv, null, outputs

Mother = TypeVar("Mother", bound=Hashable)   # the batch folder (Path) in the report, a name in the tests
REAL = -1
TASKS_PER_WORKER = 4        # pieces each kind's draws are cut into per process: evens the tail
MB = 1024.0                 # ru_maxrss is in kilobytes on Linux

# What the workers read, set before the fork: nothing is pickled or copied.
_SHARED: dict = {}


def label(delta: float) -> str:
    """A planted annual Sharpe as its fact key: 0.1 -> `d01`."""
    return f"d{round(delta * 10):02d}"


def kinds(deltas: list[float]) -> dict[int, str]:
    """Every kind of draw and the name its numbers are filed under."""
    return {null.NET: "nulo", null.GROSS: "nulo_bruto"} | {
        null.PLANTED + i: label(d) for i, d in enumerate(deltas)}


def _work(key: tuple) -> tuple:
    """One task: a mother's real CSCVs, or a run of draws of one kind.

    Args:
        key: (mother, kind, first draw, one past the last).

    Returns:
        (the real run's records on net and its summary on gross, or one summary per draw; CPU
        seconds spent; the process's peak resident memory in MB).
    """
    name, kind, start, stop = key
    got, knobs, member = _SHARED["panels"][name], _SHARED["knobs"], _SHARED["member"]
    began = time.process_time()
    if kind == REAL:
        def real(side: str, track: int | None) -> dict[str, Any]:
            """The CSCV on the real cells of one side."""
            return cscv.run(cscv.sums(got[side], knobs["blocks"]), member, knobs["chunk"],
                            knobs["bins"], knobs["reach"], track)
        out = {"net": real("net", got["track"]),
               "gross": outputs.summary(real("gross", None), knobs["tolerance"])}
    else:
        delta = knobs["deltas"][kind - null.PLANTED] if kind >= null.PLANTED else 0.0
        shared = got["std_gross" if kind == null.GROSS else "std_net"]
        out = [null.draw(shared, member, knobs["seed"], kind, i, delta, knobs)
               for i in range(start, stop)]
    return out, time.process_time() - began, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / MB


class Panel(TypedDict):
    """One mother's panel: the kept variants, the screen's counts, the track and the cells."""

    names: np.ndarray
    counts: dict[str, Any]
    track: int | None
    net: np.ndarray
    gross: np.ndarray


class Knobs(TypedDict):
    """The study's config flattened to what a worker reads."""

    blocks: int
    seed: int
    block_weeks: int
    deltas: list[float]
    share: float
    chunk: int
    bins: int
    reach: int
    tolerance: float


def knobs_of(cfg: dict) -> Knobs:
    """The study's config flattened to what a worker reads."""
    return {"blocks": cfg["cscv"]["blocks"], "seed": cfg["cscv"]["seed"],
            "block_weeks": cfg["null"]["block_weeks"], "deltas": list(cfg["power"]["deltas"]),
            "share": cfg["power"]["share"], "chunk": cfg["perf"]["chunk"],
            "bins": cfg["dominance"]["bins"], "reach": cfg["dominance"]["reach"],
            "tolerance": cfg["dominance"]["tolerance"]}


def run(panels: dict[Mother, Panel], cfg: dict,
        progress: Callable[[float], None] | None = None) -> tuple[dict[Mother, dict], dict]:
    """Every mother's real CSCV, null and power draws, through one queue of processes.

    Args:
        panels: Mother -> `net` and `gross` (weeks x variants arrays, the same columns, every
            column moving) and `track` (the mother's column, or None).
        cfg: The study's config.
        progress: Called with the share of the tasks done as they land.

    Returns:
        (mother -> `net` (the real run's records, `cscv.run`), `gross` (its summary on the
        gross cells), `draws` (kind name -> one row per draw, in draw order) and `cpu_s` (kind
        name -> CPU seconds, `real` among them); the queue's own numbers: `wall_s`,
        `procesos`, `sorteos`, `tareas`, `mem_padre_mb`, `mem_proceso_max_mb`).

        Each draw seeds its own stream from (root seed, kind, draw), so the numbers are the
        same for any number of processes, any cut of the draws and any set of mothers.
    """
    knobs, total = knobs_of(cfg), cfg["null"]["draws"]
    names = kinds(knobs["deltas"])
    workers = max(1, min(cfg["perf"]["workers"], fanout.CORES))
    size = max(1, total // (TASKS_PER_WORKER * workers))
    _SHARED.update(knobs=knobs, member=cscv.partitions(knobs["blocks"]), panels={
        name: got | {"std_net": null.standard(got["net"]),
                     "std_gross": null.standard(got["gross"])}
        for name, got in panels.items()})
    costs = {}
    for name, got in panels.items():
        width = got["net"].shape[1]
        costs[(name, REAL, 0, 1)] = 2 * width
        costs |= {(name, kind, at, min(total, at + size)): width * (min(total, at + size) - at)
                  for kind in names for at in range(0, total, size)}
    began = time.time()
    found = {name: {"draws": {k: {} for k in names.values()},
                    "cpu_s": dict.fromkeys(["real", *names.values()], 0.0)} for name in panels}
    peak = 0.0
    for done, (key, (out, cpu, rss)) in enumerate(fanout.run(_work, costs, workers), 1):
        name, kind, start, _ = key
        peak = max(peak, rss)
        if kind == REAL:
            found[name] |= out
        else:
            found[name]["draws"][names[kind]] |= {start + i: row for i, row in enumerate(out)}
        found[name]["cpu_s"]["real" if kind == REAL else names[kind]] += cpu
        if progress:
            progress(done / len(costs))
    _SHARED.clear()
    for got in found.values():
        got["draws"] = {k: pd.DataFrame.from_dict(rows, orient="index").sort_index()
                        for k, rows in got["draws"].items()}
    return found, {"wall_s": time.time() - began, "procesos": workers, "sorteos": total,
                   "tareas": len(costs),
                   "mem_padre_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / MB,
                   "mem_proceso_max_mb": float(np.float64(peak))}
