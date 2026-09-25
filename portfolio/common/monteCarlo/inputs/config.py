"""The single source of truth for every tunable of the study, and what N makes of it."""

from pathlib import Path

import numpy as np

from core.study import config as study_config

FILE = Path(__file__).parents[1] / "config.yaml"
# Which sub-run of the sweep is the one the gates and the report speak about. A choice
# of the study, not a result of it, which is why it is configuration and not execution.
HEADLINE = "stationary"     # its drawdown distribution is the order-luck one the gates read
BASELINE = "iid_bootstrap"  # the independence baseline of the composition family


def load(overrides: list[str] | None = None) -> dict:
    """Read config.yaml and apply command-line overrides.

    Args:
        overrides: Strings like "global.n_sims=5000"; each keeps the type of the value it
            replaces (core.study.config).

    Returns:
        The whole config. Every number the study uses comes from here; a value that is not
        in this dict is a value nobody can change from a UI, which is why none exist.
    """
    return study_config.load(FILE, overrides or [])


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
