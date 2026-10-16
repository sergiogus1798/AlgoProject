"""Every knob, and the harvest this study reads: gate's harvest (step 8) or a strategy export."""

from pathlib import Path
from typing import Any

import pandas as pd

from core.study import config as study_config
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict[str, Any]:
    """Every knob, with command-line overrides applied.

    Args:
        overrides: "section.key=value" strings, as --set gives them.

    Returns:
        The parsed config.yaml, every `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares (`min_edge_spreads`, `action`). Each override
        keeps the type of the value it replaces (core.study.config).
    """
    cfg = thresholds.fill(study_config.load(CONFIG, []))
    return study_config.apply(cfg, overrides)


def trades(folder: Path) -> pd.DataFrame:
    """One harvest's trades, exactly as the gate wrote them.

    Args:
        folder: A harvest directory (studies.screening.gate.harvest's output).

    Returns:
        One row per trade, carrying `identity` and `sample` ("IS"/"OOS") — this study never
        re-stages a `.sqx`, it only reads what the gate already took out of SQX.
    """
    return pd.read_parquet(folder / "trades.parquet")


def names(folder: Path) -> pd.Series:
    """Identity to strategy name, read from the harvest's metrics (trades carry no name).

    Args:
        folder: A harvest directory.

    Returns:
        Series indexed by identity; the retest (OOS) databank's own name for it.
    """
    return pd.Series(
        pd.read_parquet(folder / "metrics.parquet", columns=["strategy"])["strategy"]
    )


def timeframe(folder: Path) -> str:
    """The bars this harvest's strategies were priced on, e.g. "M30".

    Args:
        folder: A harvest directory.

    Returns:
        The build databank's `TimeFrame [IS]` column — the whole point of one project is
        one timeframe, so a single value is expected and read once, not per strategy.
    """
    col = pd.read_parquet(folder / "metrics.parquet", columns=["TimeFrame [IS]"])
    return col["TimeFrame [IS]"].iloc[0]
