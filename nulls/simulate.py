"""The numbers, under a given rung: the real run and its thousands of imaginary ones.

It chooses no model -- the rung arrives as a key -- and judges nothing: every number leaves
here with no threshold applied to it."""

import hashlib

import numpy as np
import pandas as pd

from nulls import barrier, calibrate, inputs, kernel, model, stats


def fixed(trades: pd.DataFrame, frame: pd.DataFrame, cfg: dict) -> dict:
    """Everything that is the same for the real run and for every null one.

    Args:
        trades: One strategy's trades on one sample.
        frame: The bars they were priced on.
        cfg: What inputs.config() returned.

    Returns:
        The located trades, the bar arrays, the measured point value and per-trade cost, the
        price barriers, and the reconciliation that says whether any of it can be believed.
        `levels` is empty for a strategy with neither stop nor target, which is the whole
        XAUUSD corpus of 2026-09; `barrier.exits()` then takes its fast path.
    """
    located = inputs.on_grid(trades, frame.index, cfg["barrier"]["max_hold"])
    value = calibrate.point_value(trades)
    cost = calibrate.charged(trades, value)
    checks = calibrate.convention(trades, frame, located, value, cost)
    enter, leave = calibrate.CONVENTIONS[checks["fill"]]
    arrays = {"low": frame["Low"].to_numpy(np.float64),
              "high": frame["High"].to_numpy(np.float64),
              "enter_px": frame[enter].to_numpy(np.float64),
              "leave_px": frame[leave].to_numpy(np.float64)}
    return {"located": located, "bars": arrays, "value": value, "cost": cost, "levels": {},
            "atr": calibrate.atr(frame, cfg["barrier"]["atr_bars"]), "checks": checks}


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


def _priced(kept: dict, drawn: dict, intrabar: str) -> np.ndarray:
    """Every statistic of a batch of runs, in kernel.NAMES order.

    Args:
        kept: What fixed() returned.
        drawn: Keys `entries`, `holds`, `sizes`, each (runs, trades).
        intrabar: barrier.intrabar, read only when the strategy carries price barriers.

    Returns:
        A (runs, 5) array. With no barriers -- the whole corpus of 2026-09 -- the compiled
        kernel prices and measures in one pass; with barriers the numpy path does, since
        which barrier wins inside a bar is a convention the kernel does not carry.
    """
    bars, out = kept["bars"], np.empty((drawn["entries"].shape[0], len(kernel.NAMES)))
    if not kept["levels"]:
        kernel.runs(drawn["entries"], drawn["holds"], drawn["sizes"], bars["enter_px"],
                    bars["leave_px"], kept["cost"], kept["value"], out)
        return out
    flat = {key: np.ascontiguousarray(value).ravel() for key, value in drawn.items()}
    batch = drawn["entries"].shape[0]
    leave, price = barrier.exits(flat["entries"], flat["holds"], bars, kept["levels"], intrabar)
    pnl = barrier.pnl(flat["entries"], leave, price, flat["sizes"], bars["enter_px"],
                      np.tile(kept["cost"], batch), kept["value"])
    got = stats.measure(pnl.reshape(batch, -1), list(kernel.NAMES))
    return np.column_stack([got[name] for name in kernel.NAMES])


def prime(kept: dict, cfg: dict) -> None:
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


def real(kept: dict, names: list[str]) -> dict:
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
    got = _priced(kept, {"entries": located["entry"][None, :], "holds": located["hold"][None, :],
                         "sizes": located["size"][None, :]}, "pessimistic")[0]
    return {name: float(got[kernel.NAMES.index(name)]) for name in names}


def nulls(kept: dict, rung: str, cfg: dict, key: str) -> dict:
    """Every null run under one rung, in blocks, each drawn from its own seeded stream.

    Args:
        kept: What fixed() returned.
        rung: A key of model.RUNGS.
        cfg: What inputs.config() returned.
        key: What identifies this strategy -- its name or its identity. It enters the seed.

    Returns:
        One array per statistic, each of length nulls.draws. Block `i` draws from
        `SeedSequence([seed, hash(key), rung id, i])`, so a strategy's monkeys depend on
        nothing but these four: not on the process or the thread it ran in, not on which
        other strategies were in the batch, and not on `nulls.draws` -- raising it appends
        blocks and leaves the first ones as they were. The block holds `chunk_trades` trade
        valuations: 🔬 swept 2026-09-25, that is what keeps the kernel's working set in
        cache, and it is a count of trades rather than of runs because the cache sees bytes.
        Changing it changes the streams, which is why it is a constant of the config.
    """
    knobs, names = cfg["nulls"], cfg["statistics"]["report"]
    root = [knobs["seed"], _stable(key), model.RUNG_ID[rung]]
    block = max(1, knobs["chunk_trades"] // kept["located"]["entry"].size)
    out = np.empty((knobs["draws"], len(kernel.NAMES)))
    for i, done in enumerate(range(0, knobs["draws"], block)):
        batch = min(block, knobs["draws"] - done)
        drawn = model.RUNGS[rung](kept["located"], batch, np.random.default_rng(root + [i]))
        out[done:done + batch] = _priced(kept, drawn, cfg["barrier"]["intrabar"])
    return {name: out[:, kernel.NAMES.index(name)] for name in names}


def _stable(key: str) -> int:
    """A 64-bit integer from a string, the same in every process.

    Args:
        key: Any text.

    Returns:
        The first eight bytes of its BLAKE2b digest. `hash()` is salted per interpreter,
        which is how `nulls.seed` fixed nothing until 2026-09-25: the rung name went through
        it, and two runs of the gate over the same files kept 227 and 229 strategies.
    """
    return int.from_bytes(hashlib.blake2b(key.encode(), digest_size=8).digest(), "big")
