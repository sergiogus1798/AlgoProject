"""What the study is run on: its knobs, one strategy's trades on the harvest, and its identity."""

from pathlib import Path

import numpy as np
import pandas as pd

from core.study import config as study_config

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them; each keeps
            the type of the value it replaces (core.study.config).

    Returns:
        What config.yaml holds.
    """
    return study_config.load(CONFIG, overrides)


def identity_of(folder: Path, strategy: str) -> str:
    """One strategy's identity, read from the harvest's own join.

    Args:
        folder: A harvest day folder (`metrics.parquet` inside it).
        strategy: Its name exactly as the harvest spells it.

    Returns:
        The SHA-256 the harvest already keyed it by — the gate joined build and retest on
        it, so it does not need re-deriving from a live `.sqx` (`studies/screening/gate`).
    """
    metrics = pd.read_parquet(folder / "metrics.parquet", columns=["strategy"])
    return metrics.index[metrics["strategy"] == strategy][0]


def located(folder: Path, strategy: str, cfg: dict, frame: pd.DataFrame) -> dict:
    """One strategy's trades on the sample being read, placed on the bar grid.

    Args:
        folder: A harvest day folder (`trades.parquet`, `metrics.parquet` inside it).
        strategy: Its name exactly as the harvest spells it.
        cfg: The `run` block of config.yaml.
        frame: The bars of the timeframe the strategy was built on.

    Returns:
        `identity`, `trades` (one sample, open-time order), `entry` bar index, `day`
        (entry's calendar day, normalised) and `weekday` (its English day name — Monday
        through Friday on every asset seen so far).
    """
    identity = identity_of(folder, strategy)
    trades = pd.read_parquet(folder / "trades.parquet")
    trades = trades[(trades["identity"] == identity)
                    & (trades["Sample type"] == cfg["sample"])].sort_values("Open time")
    trades = trades.reset_index(drop=True)
    entry = frame.index.searchsorted(trades["Open time"].to_numpy())
    day = pd.DatetimeIndex(trades["Open time"]).normalize()
    return {"identity": identity, "trades": trades, "entry": entry, "day": day,
            "weekday": day.day_name().to_numpy()}
