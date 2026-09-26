"""Every knob, and the harvest this study reads: gate's harvest (step 8) or a strategy export."""

from pathlib import Path

import pandas as pd

from core.paths import DATA
from core.study import config as study_config
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict:
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


def newest(project: str, databank: str) -> Path:
    """The most recent harvest of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        Its folder. Harvests are dated and immutable, so the newest is the current one.
    """
    folder = DATA / "harvest" / project / databank.replace(" ", "_")
    return sorted(p for p in folder.iterdir() if p.is_dir())[-1]


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
    return pd.read_parquet(folder / "metrics.parquet", columns=["strategy"])["strategy"]
