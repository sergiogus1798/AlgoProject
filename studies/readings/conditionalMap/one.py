"""One strategy's conditional map, returned as the contract's data: descriptive, no verdict."""

import time
from pathlib import Path

import numpy as np

from core import barstore
from core.study import result as envelope
from studies.readings.conditionalMap import contract, inputs, regime

MODULE = "studies.readings.conditionalMap"
# The window's «Muestra» selector: the configured sample, and the whole harvest beside it
# (owner, 2026-10-01) — IS + OOS1, so the session x weekday cells clear the floor.
FULL = "Completa"


def read(folder: Path, strategy: str, cfg: dict) -> dict:
    """Every measurement for one strategy, with nothing judged and nothing printed.

    Args:
        folder: A harvest day folder (`studies.screening.gate.harvest`'s output).
        strategy: Its name exactly as the harvest spells it.
        cfg: What `inputs.config` returned.

    Returns:
        The trades located on the grid, their P&L, and their volatility and trend tercile
        against the build segment's own frozen edges.
    """
    run = cfg["run"]
    frame = barstore.read(run["feed"], run["timeframe"])
    found = inputs.located(folder, strategy, run, frame, cfg["sessions"])
    day = regime.daily(frame)
    span = regime.build_span(run["symbol"])
    vol = regime.volatility(day, cfg["volatility"]["atr_period"])
    trend = regime.efficiency(day, cfg["trend"]["window"])
    vol_edges = regime.frozen_edges(vol, span)
    trend_edges = regime.frozen_edges(trend, span)
    return {"found": found, "pnl": found["trades"]["Profit/Loss"].to_numpy(np.float64),
            "vol_idx": regime.bucket(vol, vol_edges, found["day"]),
            "trend_idx": regime.bucket(trend, trend_edges, found["day"]),
            "vol_edges": vol_edges, "trend_edges": trend_edges}


def samples(got: dict, sample: str) -> dict:
    """The readings the selector offers, each the measurements cut to its trades.

    Args:
        got: What `read` returned, every harvested trade in it.
        sample: `run.sample` — the `Sample type` the map opens on, e.g. "OOS1".

    Returns:
        {option: got restricted to its trades}: `sample`, then `FULL` with every trade.
        The tercile edges stay the build segment's in both, so a trade reads the same cell
        whichever option it is counted under.
    """
    def cut(keep: np.ndarray) -> dict:
        """`got` with every per-trade array narrowed to `keep`."""
        found = got["found"]
        return {**got, "pnl": got["pnl"][keep], "vol_idx": got["vol_idx"][keep],
                "trend_idx": got["trend_idx"][keep],
                "found": {**found, "session": found["session"][keep],
                          "weekday": found["weekday"][keep], "sample": found["sample"][keep]}}

    return {sample: cut(got["found"]["sample"] == sample),
            FULL: cut(np.ones(len(got["pnl"]), dtype=bool))}


def run(strategy: str, folder: Path, cfg: dict) -> dict:
    """Where on the market-state grid one strategy earns, if anywhere in particular.

    Args:
        strategy: Its name exactly as the harvest spells it.
        folder: A harvest day folder.
        cfg: What `inputs.config` returned.

    Returns:
        The contract dict: two tabs, each with a «Muestra» selector over `run.sample` and
        the whole harvest, no verdict — it describes, the owner decides whether anything
        here is worth registering as a new, revalidated filter.
    """
    started = time.time()
    by_sample = samples(read(folder, strategy, cfg), cfg["run"]["sample"])
    head = by_sample[cfg["run"]["sample"]]
    classified = int(((head["vol_idx"] >= 0) & (head["trend_idx"] >= 0)).sum())
    return envelope.envelope(
        MODULE, strategy, head["found"]["identity"], cfg, started,
        [contract.regime_tab(by_sample, cfg), contract.calendar_tab(by_sample, cfg)],
        warnings=[contract.MULTIPLE_COMPARISONS], glossary=contract.GLOSSARY,
        summary={"trades": len(head["pnl"]), "clasificadas": classified,
                 "sample": cfg["run"]["sample"], "trades_completa": len(by_sample[FULL]["pnl"])})
