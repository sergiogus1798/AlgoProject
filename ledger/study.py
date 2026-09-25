"""What a study is, and where its ledger lives."""

import json
import re
from pathlib import Path

import pandas as pd

from core.paths import ledger_file

SAFE = re.compile(r"[^A-Za-z0-9]+")

# Contract L1: what every search leaves behind. Order is reading order, not importance.
COLUMNS = ("study", "ts", "step", "launched_by", "config_hash", "symbol", "timeframe",
           "segment", "window_from", "window_to", "n_in", "n_out", "criterion",
           "thresholds", "sharpe_mean", "sharpe_std", "sharpe_max", "n_scored",
           "score_unit", "seeds", "note")



def study_id(symbol: str, timeframe: str, family: str) -> str:
    """The identity of one study: an asset, a clock and a template family.

    Args:
        symbol: Asset as `assets/symbols/` spells it, e.g. "XAUUSD".
        timeframe: The grid the strategies were built on, e.g. "M30".
        family: The template or family of templates the population came from.

    Returns:
        The three joined by underscores, anything else collapsed. A study is the unit the
        multiple-testing correction is owed to: every search that ever touched this asset
        with this template belongs to one count, whichever step of the workflow ran it.
    """
    parts = [SAFE.sub("_", part).strip("_") for part in (symbol, timeframe, family)]
    return "_".join(p for p in parts if p)


def path(study: str) -> Path:
    """Where that study's ledger file is.

    Args:
        study: What `study_id` returned.

    Returns:
        Its `.jsonl` under the data root, whether or not it exists yet.
    """
    return ledger_file(study)


def read(study: str) -> pd.DataFrame:
    """Every search ever recorded for one study, oldest first.

    Args:
        study: What `study_id` returned.

    Returns:
        One row per search, in the order they were appended. An empty frame with the
        contract's columns when the study has no ledger yet -- a study nobody has searched
        is not an error, it is a study about to start.
    """
    file = path(study)
    if not file.exists():
        return pd.DataFrame(columns=list(COLUMNS))
    rows = [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    return pd.DataFrame(rows)


def studies() -> list[str]:
    """Every study that has a ledger.

    Returns:
        Their ids, sorted.
    """
    folder = path("x").parent
    return sorted(f.stem for f in folder.glob("*.jsonl")) if folder.exists() else []

