"""What the «Investigar» panel reads: the profile's map, one cell's measures, the memory, the board."""

import json

import pandas as pd

from core.researchpaths import research_profiles_dir
from studies.research.board import inputs, many
from studies.research.marketProfile import familias
from studies.research.marketProfile import inputs as profile
from studies.research.memory import queries
from studies.research.memory.sources import CONFIG as MEMORY
from ui.daemon.research import explain

FUNNEL = MEMORY["stages"] + ["survivors"]


def records(frame: pd.DataFrame) -> list[dict]:
    """Rows as JSON-safe dicts: NaN becomes null."""
    return json.loads(frame.to_json(orient="records"))


SEEN = {"naked": "pasa los cuatro filtros", "plateau": "una variante del barrido pasa en meseta",
        "weak": "significativa, paga menos de 2×", "none": "sin evidencia medida",
        "against": "MEDIDO EN CONTRA"}


def profile_map() -> dict:
    """The map: per asset × timeframe, the cell-families that are on the board, best first.

    Returns:
        `symbols`, `timeframes`, `families`, `levels` (the legend) and `cells`, keyed
        `SYMBOL|TF`: `passing` (every cell-family of the board there, most points first, each
        with `entered_by` — prior, desnudo, barrido —, `prior`, `evidence` and its Spanish
        `state`, `multiple`, `level` 1-3 and `trades_per_year`, None when nothing measured
        admits it) — empty for a grey cell, which then carries `best`, its highest score.
    """
    scores = inputs.scores()
    on = {}
    for c in board()["cells"]:
        on.setdefault((c["symbol"], c["timeframe"]), []).append(
            {"family": c["family"], "direction": c["direction"], "multiple": c["multiple"],
             "level": explain.level(c["multiple"])[0], "trades_per_year": c["trades_per_year"],
             "entered_by": c["entered_by"], "prior": c["prior"], "evidence": c["evidence"],
             "state": SEEN[c["evidence"]], "points": c["points"]})
    cells = {}
    for (symbol, tf), rows in scores.groupby(["symbol", "timeframe"]):
        top = rows.sort_values("score", ascending=False).iloc[0]
        cells[f"{symbol}|{tf}"] = {"passing": on.get((symbol, tf), []),
                                   "best": {"family": top["family"], "direction": top["direction"],
                                            "score": round(float(top["score"]), 1)}}
    return {"symbols": list(MEMORY["asset_class"]), "timeframes": MEMORY["timeframes"],
            "families": MEMORY["families"], "cells": cells,
            "provisional": inputs.CONFIG["marks"]["provisional_costs"],
            "levels": [{"level": n, "label": label} for _, n, label in explain.LEVELS]}


def cell(symbol: str, timeframe: str) -> dict:
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


def memory() -> dict:
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


def board() -> dict:
    """The board as `many.run` orders it now."""
    return many.run(inputs.scores(), inputs.memory(), inputs.CONFIG, inputs.sweep())
