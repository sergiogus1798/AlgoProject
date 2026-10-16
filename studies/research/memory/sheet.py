"""The hypothesis sheet: what an idea predicts before its build, its seal, and what the build did."""

import hashlib
import json
from pathlib import Path
from typing import Any, TypedDict

import pandas as pd

from core import metrics
from core.paths import export_dir
from core.researchpaths import research_memory_dir
from studies.research.memory.sources import CONFIG

NUMBERS = ("trades_per_year", "holding_hours")
TEXTS = ("not_where", "kills")
BLANK = {
    "sheet_trades_per_year": "",
    "built_trades_per_year": "",
    "trades_ratio": "",
    "sheet_holding_hours": "",
    "built_holding_hours": "",
    "holding_ratio": "",
    "hypothesis": "",
}


def problems(sheet: dict) -> list[str]:
    """Why a sheet is not one, in Spanish; empty when it is.

    Args:
        sheet: `trades_per_year` and `holding_hours` (numbers above zero: the median built
            strategy's in-sample trades a year and hours from entry to exit, by the clock),
            `not_where` (where the idea should NOT work) and `kills` (the result that kills it).
    """
    out = [
        f"la hoja no dice «{k}» con un número mayor que cero"
        for k in NUMBERS
        if not (isinstance(sheet.get(k), (int, float)) and sheet[k] > 0)
    ]
    return out + [
        f"la hoja no dice «{k}»" for k in TEXTS if not str(sheet.get(k, "")).strip()
    ]


def seal(sheet: dict) -> str:
    """A sheet's fingerprint: its four fields hashed, so a prediction moved after the build shows."""
    fields = {k: sheet[k] for k in NUMBERS + TEXTS}
    return hashlib.sha256(
        json.dumps(fields, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


def proposals_dir() -> Path:
    """`AlgoData/research/proposals/`, where the board saves each stamped proposal."""
    return research_memory_dir().parent / "proposals"


def sealed(idea: str) -> dict | None:
    """The sheet the newest proposal sealed for an idea of that name, None when none did.

    Returns:
        `sheet` and `intact`: whether it still matches the seal the proposal stamped.
    """
    for path in sorted(proposals_dir().glob("[0-9]*.json"), reverse=True):
        for i in json.loads(path.read_text(encoding="utf-8"))["ideas"]:
            if i["name"] == idea and "sheet" in i:
                return {
                    "sheet": i["sheet"],
                    "intact": seal(i["sheet"]) == i["sheet_seal"],
                }
    return None


class Built(TypedDict):
    """What the build produced: trades per year and holding hours of the median strategy."""

    trades_per_year: float
    holding_hours: float


def built(trades: pd.DataFrame) -> Built:
    """What a build produced, as the sheet's two numbers.

    Args:
        trades: The build databank's exported trades: `strategy`, `Open time`, `Close time`,
            `Sample type`.

    Returns:
        `trades_per_year` and `holding_hours` of the median strategy over its in-sample
        trades. The years are the span from the population's first in-sample entry to its
        last exit, a little under the build window; the hours are by the clock, weekends in.
    """
    mine = pd.DataFrame(trades[trades["Sample type"].astype(str).str.startswith("IS")])
    years = (mine["Close time"].max() - mine["Open time"].min()).total_seconds() / (
        metrics.YEAR_DAYS * 86400
    )
    hours = (mine["Close time"] - mine["Open time"]).dt.total_seconds() / 3600
    by = mine["strategy"].astype(str)
    return {
        "trades_per_year": float((by.value_counts() / years).median()),
        "holding_hours": float(hours.groupby(by).median().median()),
    }


def compare(sheet: dict, got: Built, tolerance: float | str) -> dict[str, Any]:
    """The sheet against the build.

    Args:
        sheet: The sealed sheet.
        got: `built`.
        tolerance: The factor either way that counts as a mismatch, or "pending" while the
            owner has not set it: then the ratios are reported and nothing is judged.

    Returns:
        The two predicted numbers, the two built ones, `trades_ratio` and `holding_ratio`
        (built ÷ predicted) and `hypothesis`: pending, match or mismatch.
    """
    ratio = {k: got[k] / sheet[k] for k in NUMBERS}
    off = tolerance != "pending" and any(
        r > float(tolerance) or r < 1 / float(tolerance) for r in ratio.values()
    )
    return {
        "sheet_trades_per_year": sheet["trades_per_year"],
        "built_trades_per_year": round(got["trades_per_year"], 1),
        "trades_ratio": round(ratio["trades_per_year"], 2),
        "sheet_holding_hours": sheet["holding_hours"],
        "built_holding_hours": round(got["holding_hours"], 1),
        "holding_ratio": round(ratio["holding_hours"], 2),
        "hypothesis": "pending"
        if tolerance == "pending"
        else "mismatch"
        if off
        else "match",
    }


def reading(idea: str, project: str) -> dict[str, Any]:
    """An attempt's sheet columns: `compare` for an idea with a sealed sheet whose build was
    exported; `hypothesis` is `altered` when the sheet no longer matches its seal, `no_data`
    when the build's trades were never exported, '' when the idea has no sheet."""
    found = sealed(idea)
    if found is None:
        return dict(BLANK)
    if not found["intact"]:
        return BLANK | {"hypothesis": "altered"}
    cfg = CONFIG["sheet"]
    exports = sorted(
        export_dir(project, cfg["databank"], "x").parent.glob("*/trades.parquet")
    )
    if not exports:
        return (
            BLANK
            | {"hypothesis": "no_data"}
            | {f"sheet_{k}": found["sheet"][k] for k in NUMBERS}
        )
    return compare(
        found["sheet"], built(pd.read_parquet(exports[-1])), cfg["tolerance"]
    )
