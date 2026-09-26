"""One strategy's conditional map, returned as the contract's data: descriptive, no verdict."""

import time
from pathlib import Path

import numpy as np

from core import barstore
from core.study import output, result as envelope
from studies.readings.conditionalMap import contract, inputs, regime

MODULE = "studies.readings.conditionalMap"


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
    found = inputs.located(folder, strategy, run, frame)
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


def run(strategy: str, folder: Path, cfg: dict) -> dict:
    """Where on the market-state grid one strategy earns, if anywhere in particular.

    Args:
        strategy: Its name exactly as the harvest spells it.
        folder: A harvest day folder.
        cfg: What `inputs.config` returned.

    Returns:
        The contract dict: two tabs, no verdict — it describes, the owner decides whether
        anything here is worth registering as a new, revalidated filter.
    """
    started = time.time()
    got = read(folder, strategy, cfg)
    classified = int(((got["vol_idx"] >= 0) & (got["trend_idx"] >= 0)).sum())
    return envelope.envelope(
        MODULE, strategy, got["found"]["identity"], cfg, started,
        [contract.regime_tab(got, cfg), contract.calendar_tab(got, cfg)],
        warnings=[contract.MULTIPLE_COMPARISONS], glossary=contract.GLOSSARY,
        summary={"trades": len(got["pnl"]), "clasificadas": classified,
                 "sample": cfg["run"]["sample"]})
