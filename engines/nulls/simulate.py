"""The numbers, under a given rung: the real run and its thousands of imaginary ones.

It chooses no model -- the rung arrives as a key -- and judges nothing: every number leaves
here with no threshold applied to it."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import parent_process
from typing import cast

import numpy as np
import pandas as pd

from core import fanout
from engines.market import calibrate
from engines.nulls import inputs, kernel, model


def fixed(trades: pd.DataFrame, frame: pd.DataFrame, cfg: dict) -> inputs.Fixed:
    """Everything that is the same for the real run and for every null one.

    Args:
        trades: One strategy's trades on one sample.
        frame: The bars they were priced on.
        cfg: What inputs.config() returned.

    Returns:
        The located trades, the bar arrays, the measured point value and per-trade cost, the
        price barriers, and the reconciliation that says whether any of it can be believed.
    """
    located = inputs.on_grid(
        trades, cast(pd.DatetimeIndex, frame.index), cfg["barrier"]["max_hold"]
    )
    value = calibrate.point_value(trades)
    cost = calibrate.charged(trades, value)
    checks = calibrate.convention(trades, frame, located, value, cost)
    enter, leave = calibrate.CONVENTIONS[checks["fill"]]
    arrays = {
        "low": frame["Low"].to_numpy(np.float64),
        "high": frame["High"].to_numpy(np.float64),
        "enter_px": frame[enter].to_numpy(np.float64),
        "leave_px": frame[leave].to_numpy(np.float64),
    }
    return {
        "located": located,
        "bars": arrays,
        "value": value,
        "cost": cost,
        "atr": calibrate.atr(frame, cfg["barrier"]["atr_bars"]),
        "checks": checks,
    }


def warm(frame: pd.DataFrame, cfg: dict) -> None:
    """Compute the ATR of these bars once, before a population study forks or loops.

    Args:
        frame: The bars every strategy of the study is priced on.
        cfg: What inputs.config() returned.

    Returns:
        Nothing. `fixed()` needs the same ATR over the same bars once per strategy and it
        depends on nothing else, so calling this first turns 234 x 39 ms into 39 ms.
    """
    calibrate.atr(frame, cfg["barrier"]["atr_bars"])


def prime(kept: inputs.Fixed, cfg: dict) -> None:
    """Compile every specialisation of the kernel here, before a population study forks.

    Args:
        kept: What fixed() returned for any one strategy.
        cfg: What inputs.config() returned.

    Returns:
        Nothing. Each rung hands the kernel differently laid-out arrays and each layout is
        its own compilation; done once in the parent, every forked worker inherits the
        machine code instead of compiling or loading it again.
    """
    small = {**cfg, "nulls": {**cfg["nulls"], "draws": 2}}
    real(kept, cfg["statistics"]["report"])
    for rung in model.RUNGS:
        nulls(kept, rung, small, "prime")


def real(kept: inputs.Fixed, names: list[str]) -> dict[str, float]:
    """The statistics of the run that actually happened, priced the same way as the nulls.

    Args:
        kept: What fixed() returned.
        names: statistics.report.

    Returns:
        One scalar per statistic. Priced from the bars rather than read from SQX's P/L on
        purpose, and by the very code that prices the nulls: the comparison has to be
        between two numbers the same arithmetic produced, and `checks` is what says the
        reconstruction agrees with SQX.
    """
    located = kept["located"]
    bars, got = kept["bars"], np.empty((1, len(kernel.NAMES)))
    kernel.runs(
        located["entry"][None, :],
        located["hold"][None, :],
        located["size"][None, :],
        bars["enter_px"],
        bars["leave_px"],
        kept["cost"],
        kept["value"],
        got,
    )
    got = got[0]
    return {name: float(got[kernel.NAMES.index(name)]) for name in names}


def nulls(
    kept: inputs.Fixed, rung: str, cfg: dict, key: str, threads: int | None = None
) -> dict[str, np.ndarray]:
    """Every null run under one rung, in blocks, each drawn from its own seeded stream.

    Args:
        kept: What fixed() returned.
        rung: A key of model.RUNGS.
        cfg: What inputs.config() returned.
        key: The strategy's name (what `monkey.one` passes). It enters the seed.
        threads: Threads to spread the blocks over; None for every physical core, or one
            inside a child process -- a fanout worker already has its core.

    Returns:
        One array per statistic, each of length nulls.draws. Block `i` draws from
        `SeedSequence([root, _stable(key), TAG, i])` -- the same for every rung, which is
        what makes the rungs share their uniforms (model._rung) -- where `root` is `cfg["nulls"]["seed"]`
        as `inputs.config()` resolved it -- a fresh one per run by default, or the explicit
        int a caller asked to reproduce. A strategy's monkeys depend on nothing but these
        three: not on the process or the thread it ran in, not on which other strategies were
        in the batch, and on `nulls.draws` only through the last partial block -- raising it
        appends blocks and leaves the full ones as they were; the uniforms of a partial last
        block are a prefix of a full one's, but `timing_holds` and `free` redraw its holds
        after them, whose batch size changes what the stream yields. The block holds `chunk_trades` trade valuations: 🔬 swept
        2026-09-25, that is what keeps the kernel's working set in cache, and it is a count
        of trades rather than of runs because the cache sees bytes. Changing it changes the
        streams, which is why it is a constant of the config. Each block writes its own
        rows from its own stream, so the threads change nothing but the wall time: numpy
        releases the GIL to draw and the kernel is `nogil`.
    """
    knobs, names = cfg["nulls"], cfg["statistics"]["report"]
    root = [knobs["seed"], _stable(key), TAG]
    located, bars, (lo, hi) = kept["located"], kept["bars"], kept["located"]["window"]
    block = max(1, knobs["chunk_trades"] // located["entry"].size)
    out = np.empty((knobs["draws"], len(kernel.NAMES)))

    def one(i: int) -> None:
        """Draw and price block `i` of the draws into its rows of `out`."""
        rows = out[i * block : (i + 1) * block]
        rng = np.random.default_rng(root + [i])
        drawn = model.RUNGS[rung](located, len(rows), rng, placed=False)
        kernel.ladder(
            drawn["u"],
            drawn["holds"],
            drawn["sizes"],
            bars["enter_px"],
            bars["leave_px"],
            kept["cost"],
            kept["value"],
            lo,
            hi,
            rows,
        )

    blocks = range(-(-knobs["draws"] // block))
    threads = min(len(blocks), threads or (1 if parent_process() else fanout.CORES))
    if threads <= 1:
        for i in blocks:
            one(i)
    else:
        with ThreadPoolExecutor(threads) as pool:
            list(pool.map(one, blocks))
    return {name: out[:, kernel.NAMES.index(name)] for name in names}


# numpy pads a seed tuple with zeros, so [seed, k] == [seed, k, 0]: this tag keeps the monkeys' stream
# off `resample.stream(seed, key)` (levels 3a/b) when a replay pins both seeds to one number.
TAG = 0x4D4F4E4B


def _stable(key: str) -> int:
    """A 64-bit integer from a string, the same in every process.

    Args:
        key: Any text.

    Returns:
        The first eight bytes of its BLAKE2b digest. `hash()` is salted per interpreter --
        history now, but it is why `nulls.seed` fixed nothing until 2026-09-25: the rung
        name went through it, and two runs of the gate over the same files kept 227 and 229
        strategies. `_stable` is what makes a fixed `nulls.seed` reproduce a run today, and
        what makes two strategies in the same run draw different monkeys under a fresh root.
    """
    return int.from_bytes(hashlib.blake2b(key.encode(), digest_size=8).digest(), "big")
