"""What the «Investigar» panel reads: the profile's map, one cell's measures, the memory, the board."""

import json
from typing import Any, TypedDict, cast

import pandas as pd

from core.researchpaths import research_profiles_dir
from studies.research.board import inputs, many
from studies.research.marketProfile import familias
from studies.research.marketProfile import inputs as profile
from studies.research.memory import queries
from studies.research.memory.sources import CONFIG as MEMORY
from ui.daemon.research import explain

FUNNEL = MEMORY["stages"] + ["survivors"]


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Rows as JSON-safe dicts: NaN becomes null."""
    return json.loads(cast("str", frame.to_json(orient="records")))


SEEN = {"naked": "pasa los cuatro filtros", "plateau": "una variante del barrido pasa en meseta",
        "weak": "significativa, paga menos de 2×", "none": "sin evidencia medida",
        "against": "Medido en contra"}


class BestCell(TypedDict):
    """The highest-scoring family of a grey cell."""

    family: str
    direction: str
    score: float


class MapCell(TypedDict):
    """One asset × timeframe of the map: the cell-families on the board, and the best score."""

    passing: list[dict[str, Any]]
    best: BestCell


class ProfileMap(TypedDict):
    """The research map: the axes, the legend and one `MapCell` per `SYMBOL|TF`."""

    symbols: list[str]
    timeframes: list[str]
    families: list[str]
    cells: dict[str, MapCell]
    provisional: Any
    levels: list[dict[str, Any]]


class CellView(TypedDict):
    """One asset × timeframe: family scores, every measure with its explanation, its context."""

    symbol: str
    timeframe: str
    measures: list[dict[str, Any]]
    families: list[dict[str, Any]]
    context: dict[str, Any]
    columns: Any
    context_help: Any


class Coverage(TypedDict):
    """How much of the grid the memory has touched."""

    cells: int
    untouched: int
    closed: int


class MemoryView(TypedDict):
    """The memory: every attempt with its funnel, survivors per family, ideas spent, coverage."""

    attempts: list[dict[str, Any]]
    by_family: Any
    spent: Any
    ideas: int
    stages: list[str]
    coverage: Coverage


def profile_map() -> ProfileMap:
    """The map: per asset × timeframe, the cell-families that are on the board, best first.

    Returns:
        `symbols`, `timeframes`, `families`, `levels` (the legend) and `cells`, keyed
        `SYMBOL|TF`: `passing` (every cell-family of the board there, most points first, each
        with `entered_by` — prior, desnudo, barrido —, `prior`, `evidence` and its Spanish
        `state`, `multiple`, `level` 1-3 and `trades_per_year`, None when nothing measured
        admits it) — empty for a grey cell, which then carries `best`, its highest score.
    """
    scores = inputs.scores()
    on: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for c in board()["cells"]:
        on.setdefault((c["symbol"], c["timeframe"]), []).append(
            {"family": c["family"], "direction": c["direction"], "multiple": c["multiple"],
             "level": explain.level(c["multiple"])[0], "trades_per_year": c["trades_per_year"],
             "entered_by": c["entered_by"], "prior": c["prior"], "evidence": c["evidence"],
             "state": SEEN[c["evidence"]], "points": c["points"]})
    cells: dict[str, MapCell] = {}
    for pair, rows in scores.groupby(["symbol", "timeframe"]):
        symbol, tf = cast("tuple[str, str]", pair)
        top = rows.sort_values("score", ascending=False).iloc[0]
        cells[f"{symbol}|{tf}"] = {"passing": on.get((symbol, tf), []),
                                   "best": {"family": top["family"], "direction": top["direction"],
                                            "score": round(float(top["score"]), 1)}}
    return {"symbols": list(MEMORY["asset_class"]), "timeframes": MEMORY["timeframes"],
            "families": MEMORY["families"], "cells": cells,
            "provisional": inputs.CONFIG["marks"]["provisional_costs"],
            "levels": [{"level": n, "label": label} for _, n, label in explain.LEVELS]}


def cell(symbol: str, timeframe: str) -> CellView:
    """One asset × timeframe: its family scores, every measure with its explanation, its context."""
    top = research_profiles_dir()
    here = lambda f: f[(f["symbol"] == symbol) & (f["timeframe"] == timeframe)]  # noqa: E731
    measures = here(pd.read_csv(top / "measures.csv")).drop(columns=["per_year"])
    rows = records(measures.sort_values(["passes", "multiple"], ascending=False))
    cfg = profile.config()
    for r in rows:
        r["explanation"] = explain.MEASURES.get(r["measure"]) or familias.describe(r["measure"], cfg)
    context = records(here(pd.read_csv(top / "context.csv")))
    return {"symbol": symbol, "timeframe": timeframe, "measures": rows,
            "families": records(here(inputs.scores()).sort_values("score", ascending=False)),
            "context": context[0] if context else {}, "columns": explain.COLUMNS,
            "context_help": explain.CONTEXT}


def memory() -> MemoryView:
    """The memory: coverage, the funnel of every attempt, survivors per family, ideas spent."""
    got = inputs.memory()
    attempts = [{**{k: a[k] for k in ("project", "template", "family", "symbol", "timeframe",
                                      "direction", "date", "outcome", "verdict",
                                      "custodian_hours")},
                 "funnel": [{"stage": s, "n": a[s]} for s in FUNNEL if a[s] not in ("", None)]}
                for a in got["attempts"]]
    grid = len(queries.grid())
    return {"attempts": attempts, "by_family": got["by_family"], "spent": got["spent"],
            "ideas": len(got["ideas"]), "stages": FUNNEL,
            "coverage": {"cells": grid, "untouched": len(queries.untouched_cells(got["attempts"])),
                         "closed": sum(r["closed"] for r in got["by_family"])}}


def board() -> dict[str, Any]:
    """The board as `many.run` orders it now."""
    return many.run(inputs.scores(), inputs.memory(), inputs.CONFIG, inputs.sweep())
