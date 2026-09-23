"""The numbers, under a given rung: the real run and its thousands of imaginary ones.

It chooses no model -- the rung arrives as a key -- and judges nothing: every number leaves
here with no threshold applied to it."""

import numpy as np
import pandas as pd

from nulls import barrier, calibrate, inputs, model, stats


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


def real(kept: dict, names: list[str]) -> dict:
    """The statistics of the run that actually happened, priced the same way as the nulls.

    Args:
        kept: What fixed() returned.
        names: statistics.report.

    Returns:
        One scalar per statistic. Priced from the bars rather than read from SQX's P/L on
        purpose: the comparison has to be between two numbers the same three lines produced,
        and `checks` is what says the two agree.
    """
    located = kept["located"]
    leave, price = barrier.exits(located["entry"], located["hold"], kept["bars"],
                                 kept["levels"], "pessimistic")
    pnl = barrier.pnl(located["entry"], leave, price, located["size"],
                      kept["bars"]["enter_px"], kept["cost"], kept["value"])
    return {name: float(value[0]) for name, value in stats.measure(pnl[None, :], names).items()}


def nulls(kept: dict, rung: str, cfg: dict) -> dict:
    """Every null run under one rung, in batches.

    Args:
        kept: What fixed() returned.
        rung: A key of model.RUNGS.
        cfg: What inputs.config() returned.

    Returns:
        One array per statistic, each of length nulls.draws. Batched because the barrier
        scan allocates one boolean of shape (runs x trades, max hold): at the shipped
        chunk of 500 runs that is ~127 MB, and unchunked it would be gigabytes.
    """
    knobs, names = cfg["nulls"], cfg["statistics"]["report"]
    rng = np.random.default_rng([knobs["seed"], abs(hash(rung)) % (2 ** 32)])
    out = {name: [] for name in names}
    done = 0
    while done < knobs["draws"]:
        batch = min(knobs["chunk"], knobs["draws"] - done)
        drawn = model.RUNGS[rung](kept["located"], batch, rng)
        flat = {key: value.ravel() for key, value in drawn.items()}
        leave, price = barrier.exits(flat["entries"], flat["holds"], kept["bars"],
                                     kept["levels"], cfg["barrier"]["intrabar"])
        pnl = barrier.pnl(flat["entries"], leave, price, flat["sizes"],
                          kept["bars"]["enter_px"], np.tile(kept["cost"], batch), kept["value"])
        for name, value in stats.measure(pnl.reshape(batch, -1), names).items():
            out[name].append(value)
        done += batch
    return {name: np.concatenate(parts) for name, parts in out.items()}
