"""Where the pooled profile lives on disk: one file pair per asset of a group, and the tables."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.researchpaths import research_profiles_dir
from studies.research.pooledProfile.one import Run


def folder() -> Path:
    """`AlgoData/research/pooled/`, with its `cells/`, created on first use."""
    path = research_profiles_dir().parent / "pooled"
    (path / "cells").mkdir(parents=True, exist_ok=True)
    return path


def stem(group: str, timeframe: str, symbol: str) -> Path:
    """The path, without suffix, of one asset's rows and null draws."""
    return folder() / "cells" / f"{group}_{timeframe}_{symbol}"


def seed(fresh: int, force: bool) -> int:
    """The seed every cell of this map is drawn with: the stored one unless starting over.

    Joint resampling holds only while every asset of a group uses the same root, so a
    resumed run must not draw a new one.
    """
    path = folder() / "seed.json"
    if force or not path.exists():
        path.write_text(json.dumps({"seed": fresh}), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))["seed"]


def save(group: str, timeframe: str, symbol: str, got: Run) -> None:
    """Write one asset's rows (parquet) and its null statistics (npy)."""
    np.save(stem(group, timeframe, symbol).with_suffix(".npy"), got["sims"])
    got["rows"].to_parquet(
        stem(group, timeframe, symbol).with_suffix(".parquet"), index=False
    )


def load(
    group: str, timeframe: str, symbols: list[str]
) -> tuple[list[pd.DataFrame], np.ndarray]:
    """A group's cell: each asset's rows, and the null statistics as assets x draws x tests."""
    rows = [
        pd.read_parquet(stem(group, timeframe, s).with_suffix(".parquet"))
        for s in symbols
    ]
    return rows, np.array(
        [np.load(stem(group, timeframe, s).with_suffix(".npy")) for s in symbols]
    )


def write(tables: dict[str, pd.DataFrame]) -> Path:
    """Each judged table as `<name>.csv`; returns the folder."""
    for name, table in tables.items():
        table.to_csv(folder() / f"{name}.csv", index=False)
    return folder()
