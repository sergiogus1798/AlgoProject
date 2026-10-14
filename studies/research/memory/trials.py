"""What the research spent on one ledger study: the hypotheses measured before any search row."""

import json
from typing import TypedDict

from core.researchpaths import research_profiles_dir
from studies.research.memory.sources import CONFIG

DIRECTIONS = ("long", "short")
PROFILE_LEDGERS = ("ledger.jsonl", "sweep/ledger.jsonl")


def directions(family: str, templates: dict[str, dict]) -> tuple:
    """The directions a ledger study trades: its template's, both when its family is no template."""
    shape = templates.get(family, {}).get("shape", "")
    return tuple(d for d in DIRECTIONS if d in shape) or DIRECTIONS


class Spent(TypedDict):
    """The looks taken at one study: hypotheses measured, ideas, idea files, directions counted."""

    hypotheses: int
    ideas: int
    files: int
    directions: tuple[str, ...]


def spent(
    ideas: list[dict],
    templates: dict[str, dict],
    symbol: str,
    timeframe: str,
    family: str,
) -> Spent:
    """The looks the ideaExpert took at the data of one ledger study (owner, 2026-10-02).

    Args:
        ideas: `ideas.index()`.
        templates: `sources.templates()`.
        symbol, timeframe: The study's.
        family: The study's third part: a template name, or a label that is not one.

    Returns:
        `hypotheses` (each idea file's own count, once per file — the trials the deflated
        Sharpe is owed), `ideas`, `files` and the `directions` counted. An idea counts when it
        is on that asset and timeframe, in the study's direction, and its board family is the
        study's or either is unknown: a look with no family yet was a look at all of them.
    """
    board = {
        n: CONFIG["archetype_family"].get(t["archetype"], "")
        for n, t in templates.items()
    }
    dirs = directions(family, templates)
    mine = [
        i
        for i in ideas
        if (i["symbol"], i["timeframe"]) == (symbol, timeframe)
        and i["direction"] in dirs + ("",)
        and (
            not board.get(i["idea"])
            or not board.get(family)
            or board[i["idea"]] == board[family]
        )
    ]
    files = {i["file"]: i["hypotheses_measured"] or 0 for i in mine}
    return {
        "hypotheses": sum(files.values()),
        "ideas": len(mine),
        "files": len(files),
        "directions": dirs,
    }


def profile_looks(symbol: str, timeframe: str, dirs: tuple) -> int:
    """Distinct measures the market profile and its sweep tested there, in those directions.

    Informative only: they are corrected among themselves and never enter the study's N. A
    rerun appends the same criteria again, so rows are not looks; distinct criteria are.
    """
    mark = f'"study": "{symbol}_{timeframe}_marketProfile"'
    total = 0
    for name in PROFILE_LEDGERS:
        path = research_profiles_dir() / name
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            seen = {json.loads(line)["criterion"] for line in handle if mark in line}
        total += sum(c.rsplit("/", 1)[-1] in dirs for c in seen)
    return total
