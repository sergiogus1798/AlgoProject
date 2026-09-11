"""The single source of truth for every tunable of the study, and what N makes of it."""

from pathlib import Path

import numpy as np
import yaml

FILE = Path(__file__).with_name("config.yaml")


def load(overrides: list[str] | None = None) -> dict:
    """Read config.yaml and apply command-line overrides.

    Args:
        overrides: Strings like "global.n_sims=5000", dotted key then value. Values are
            parsed as YAML, so 0.05, true and [1, 2] all arrive as the right type.

    Returns:
        The whole config. Every number the study uses comes from here; a value that is not
        in this dict is a value nobody can change from a UI, which is why none exist.
    """
    cfg = yaml.safe_load(FILE.read_text(encoding="utf-8"))
    for item in overrides or []:
        key, value = item.split("=", 1)
        node = cfg
        *path, leaf = key.split(".")
        for step in path:
            node = node[step]
        node[leaf] = yaml.safe_load(value)
    return cfg


def block_sizes(n_trades: int, cfg: dict) -> list[int]:
    """The block lengths the reordering and resampling sweeps are run at.

    Args:
        n_trades: Trades in the stream.
        cfg: What load() returned.

    Returns:
        Evenly spaced block lengths from block_min to floor(N / min_blocks), endpoints
        included; empty when N cannot support even the smallest block over min_blocks
        blocks. Empty means the sweep is skipped and flagged, never run degenerate.
    """
    b = cfg["blocks"]
    top = n_trades // b["min_blocks"]
    if top < b["block_min"]:
        return []
    return sorted({int(round(x)) for x in
                   np.linspace(b["block_min"], top, b["n_block_sizes"])})


def stationary_block(n_trades: int) -> int:
    """Mean block length of the stationary bootstrap.

    Args:
        n_trades: Trades in the stream.

    Returns:
        round(N^(1/3)), the Politis-Romano rule of thumb. The geometric draw around it is
        what stops one imposed dependence length deciding the answer.
    """
    return max(2, int(round(n_trades ** (1 / 3))))
