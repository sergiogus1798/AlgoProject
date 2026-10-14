"""What the pooled profile is run on: its config, the groups, and each group's shared bars."""

from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from core.study import config as study_config
from studies.research.marketProfile import inputs as profile
from studies.research.memory.sources import CONFIG as MEMORY

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str] | None = None) -> dict[str, Any]:
    """The parsed config.yaml with its overrides, the profile's own config under `profile`.

    Returns:
        The config; a null seed becomes a fresh root. `profile` is marketProfile's config
        with that seed and, unless `judge.clock`, without its clock measures.
    """
    cfg = study_config.load(CONFIG, overrides or [])
    if cfg["run"]["seed"] is None:
        cfg["run"]["seed"] = int(cast("int", np.random.SeedSequence().entropy) % 2**32)
    cfg["profile"] = profile.config([f"nulls.seed={cfg['run']['seed']}"])
    if not cfg["judge"]["clock"]:
        cfg["profile"]["measures"] = [
            m for m in cfg["profile"]["measures"] if not m.get("clock", False)
        ]
    return cfg


def groups(cfg: dict) -> dict[str, list[str]]:
    """Group name to its assets, from the results memory's `groups.by` map."""
    out = {}
    for symbol, group in MEMORY[cfg["groups"]["by"]].items():
        out.setdefault(group, []).append(symbol)
    return out


def shared(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Each asset's bars on the instants every asset of the group has.

    Args:
        frames: Asset to its bars at one timeframe.

    Returns:
        The same frames cut to the common bar times, so one resampling of positions is one
        resampling of TIME for the whole group: bar k is the same instant in every asset.
    """
    index = None
    for frame in frames.values():
        index = frame.index if index is None else index.intersection(frame.index)
    return {s: f.loc[index] for s, f in frames.items()}


def bars(
    symbols: list[str], timeframes: list[str]
) -> dict[str, dict[str, pd.DataFrame]]:
    """A group's bars at each timeframe, build segment only, on their shared instants.

    Returns:
        {timeframe: {symbol: bars}}. Every asset enters through the profile's own `cut`; the
        group is then judged on the overlap of its assets' build windows.
    """
    m1 = {s: profile.minute_bars(s, 0) for s in symbols}
    return {t: shared({s: profile.bars(m1[s], t) for s in symbols}) for t in timeframes}
