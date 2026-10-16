"""Every knob, the harvest's oos1 trades, and the clock they are stamped in."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core.study import config as study_config
from ledger import thresholds
from sqx.inspect import feeds

CONFIG = Path(__file__).with_name("config.yaml")
# SQX feeds moved to <ASSET>_M1 on EETUS that day; a harvest built earlier carries the old
# broker-suffixed feed's clock, which no file records (portfolio/common/construct/inputs/backfill.py).
FEEDS_MOVED = "2026-10-01"


def config(overrides: list[str]) -> dict[str, Any]:
    """Every knob with `ledger:<key>` filled and the overrides applied; a null seed drawn fresh.

    Args:
        overrides: "section.key=value" strings, as --set gives them.

    Returns:
        The parsed config.yaml; `shuffle.seed` is an int afterwards, the root this run drew from
        OS entropy when the file says null (`knowhow/eng/nulls-seed-fresh-per-run.md`).
    """
    cfg = study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)
    if cfg["shuffle"]["seed"] is None:
        cfg["shuffle"]["seed"] = int(np.random.SeedSequence().generate_state(1)[0])
    return cfg


def oos_trades(folder: Path) -> pd.DataFrame:
    """The harvest's oos1 trades only — the calendar null is the out-of-sample one, never the IS.

    Args:
        folder: A harvest directory (studies.screening.gate.harvest's output).

    Returns:
        Rows with `sample == "OOS"` (the harvest's OOS is oos1; oos2 is never harvested).
    """
    t = pd.read_parquet(
        folder / "trades.parquet",
        columns=[
            "Open time",
            "Close time",
            "Profit/Loss",
            "Size",
            "identity",
            "sample",
        ],
    )
    if t.empty:
        raise ValueError(f"{folder}/trades.parquet holds no trade; re-run the harvest")
    return pd.DataFrame(t[t["sample"] == "OOS"]).reset_index(drop=True)


def names(folder: Path) -> pd.Series:
    """Identity to strategy name, read from the harvest's metrics (trades carry no name)."""
    return pd.Series(
        pd.read_parquet(folder / "metrics.parquet", columns=["strategy"])["strategy"]
    )


def clock(feed: str, folder: Path) -> tuple[str, list[dict]]:
    """The zone the harvest's trades are stamped in, and the warning when it may not be.

    Args:
        feed: The SQX feed the project trades, e.g. "XAUUSD_M1".
        folder: The harvest directory; its name is its date.

    Returns:
        (zone, warnings): the feed's zone in SQX's registry; one highlighted warning when the
        harvest predates FEEDS_MOVED, since its hours may then be 2-3 h off.
    """
    zone = feeds.timezone(feed)
    if folder.name >= FEEDS_MOVED:
        return zone, []
    return zone, [
        {
            "code": "old_clock",
            "state": "watch",
            "highlight": True,
            "text": f"Cosecha del {folder.name}, anterior al cambio de feeds del {FEEDS_MOVED}: "
            f"sus horas pueden venir en el reloj del feed antiguo, no en {zone}. Meses y días "
            "apenas cambian; las horas pueden salir desplazadas 2-3 h.",
        }
    ]
