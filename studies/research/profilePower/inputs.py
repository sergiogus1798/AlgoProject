"""What the power study is run on: its config, the profile's, the cut-off, and a cell's bars."""

from pathlib import Path

import numpy as np
import pandas as pd

from core.researchpaths import research_profiles_dir
from core.study import config as study_config
from studies.research.marketProfile import inputs as profile

CONFIG = Path(__file__).with_name("config.yaml")


def map_cut() -> float:
    """The raw p the full map's correction demands today: the largest p it named significant."""
    measures = pd.read_csv(research_profiles_dir() / "measures.csv", usecols=["p", "significant"])
    return float(measures.loc[measures["significant"], "p"].max())


def config(overrides: list[str] | None = None) -> dict:
    """The parsed config.yaml with its overrides, the profile's own config under `profile`.

    Returns:
        The config; a null seed becomes a fresh, recorded root and a null `judge.cut` the
        cut-off of the map on disk. `profile` is marketProfile's config untouched but for the
        seed: its null, its block and its four filters are the ones this study judges with.
    """
    cfg = study_config.load(CONFIG, overrides or [])
    if cfg["run"]["seed"] is None:
        cfg["run"]["seed"] = int(np.random.SeedSequence().entropy % 2 ** 32)
    if cfg["judge"]["cut"] is None:
        cfg["judge"]["cut"] = map_cut()
    cfg["profile"] = profile.config([f"nulls.seed={cfg['run']['seed']}"])
    return cfg


def cells(cfg: dict) -> list[tuple[str, str]]:
    """The (symbol, timeframe) pairs of `run.cells`."""
    return [tuple(c.split("/")) for c in cfg["run"]["cells"]]


def bars(symbol: str, timeframe: str) -> pd.DataFrame:
    """A cell's bars, build segment only: they enter through the profile's own `cut`."""
    return profile.bars(profile.minute_bars(symbol, 0), timeframe)


def cost_log(asset: dict, opens: np.ndarray) -> np.ndarray:
    """One round trip's cost at each bar, as a log return.

    Args:
        asset: What core.assetdata.load() returned.
        opens: Log open of every bar.
    """
    price = np.exp(opens)
    return profile.cost(asset, price) / price
