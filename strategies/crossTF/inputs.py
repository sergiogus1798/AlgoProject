"""What the study is run on: its knobs, which cell each result block is, and the bars."""

from pathlib import Path

import pandas as pd
import yaml

from core.barstore import read as read_bars
from core.paths import ROOT

CONFIG = ROOT / "strategies" / "crossTF" / "config.yaml"


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them.

    Returns:
        What config.yaml holds, each override parsed as YAML so numbers stay numbers.
    """
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for item in overrides:
        dotted, raw = item.split("=", 1)
        section, key = dotted.split(".", 1)
        cfg[section][key] = yaml.safe_load(raw)
    return cfg


def plan(scaling: pd.DataFrame, blocks: list[str]) -> pd.DataFrame:
    """Which (strategy, block) pairs are a cell, and what each one means.

    Four roles, and the two that are easy to forget are the point of the design. `control`
    is the scaled strategy run back on its own source timeframe: it isolates what the
    parameter change cost on its own, so a dead `scaled` cell can be blamed on the right
    thing. `unscaled` is the mother read on another timeframe, which is a different
    question -- whether the market is self-similar -- and never a robustness failure.

    Args:
        scaling: The manifest `sqx.variants.scale` wrote.
        blocks: Timeframe per result block, block 0 first.

    Returns:
        One row per cell: `strategy`, `block`, `timeframe`, `role`, `mother`.
    """
    rows = []
    for mother in sorted(scaling["mother"].unique()):
        for index, timeframe in enumerate(blocks):
            rows.append({"strategy": mother, "block": index, "timeframe": timeframe,
                         "role": "baseline" if index == 0 else "unscaled",
                         "mother": mother})
    for row in scaling.itertuples():
        rows.append({"strategy": row.name, "block": blocks.index(row.target_tf),
                     "timeframe": row.target_tf, "role": "scaled", "mother": row.mother})
        rows.append({"strategy": row.name, "block": 0, "timeframe": blocks[0],
                     "role": "control", "mother": row.mother})
    return pd.DataFrame(rows)


def trades(packed: Path) -> pd.DataFrame:
    """Every strategy's trades of one `data=all` retest export.

    Args:
        packed: The `trades.parquet` `sqx/export/export_retest.py` wrote.

    Returns:
        The packed frame, `block` separating the result blocks of each strategy.
    """
    return pd.read_parquet(packed)


def bars(feed: str, timeframes: list[str]) -> dict[str, pd.DataFrame]:
    """The bars of every timeframe a cell is priced on.

    Args:
        feed: SQX symbol without the timeframe suffix.
        timeframes: Which to load; resampled from M1 and cached on first use.

    Returns:
        Timeframe to its frame. Each cell's null is drawn on its own grid, which is the
        whole reason this is a dict and not one frame.
    """
    return {tf: read_bars(feed, tf) for tf in timeframes}
