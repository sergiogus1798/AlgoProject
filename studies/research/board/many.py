"""The board: the cells the prior or the measurements let in, ordered, each factor beside its rank."""

from datetime import datetime

import pandas as pd

from studies.research.board import factors, inputs, prior
from studies.research.board.inputs import CELL


def run(scores: pd.DataFrame, memory: dict, cfg: dict, sweep: pd.DataFrame | None = None) -> dict:
    """Gate and order the cells.

    Args:
        scores: The profile's `scores.csv`.
        memory: `inputs.memory()`.
        cfg: `inputs.CONFIG`.
        sweep: The sweep's `best.csv` (`inputs.sweep()`); None or empty when it was not run.

    Returns:
        The page as plain data: `cells` (best first, each with `rank`, `points`, the factors
        with their raw values, `entered_by`, `evidence`, the prior's level, `trades_per_year`
        — None when nothing measured admits the cell — and the provisional-costs mark),
        `gated_out` and the weights used. Gate (owner, 2026-10-02): the prior rates the cell
        Alta, OR it passes the four filters naked, OR a sweep variant passes on a plateau.
        Never a family whose lead needs the clock; the coverage gap orders, it lets nothing in.
    """
    marks, values = cfg["marks"], cfg["evidence"]["values"]
    found = {} if sweep is None else {tuple(r[c] for c in CELL): r for r in sweep.to_dict("records")}
    cells = []
    for r in scores[~scores["needs_clock"]].to_dict("records"):
        key = tuple(r[c] for c in CELL)
        said = prior.of(*key, cfg["prior"]["pullback_as"])
        swept = found.get(key)
        seen = factors.evidence(r, swept)
        entered = [name for name, ok in (("prior", said["level"] == "Alta"), ("desnudo", seen == "naked"),
                                         ("barrido", bool(swept and swept["plateau_any"]))) if ok]
        if not entered:
            continue
        measured = swept if seen == "plateau" else (r if seen == "naked" else None)
        klass = inputs.asset_class(r["symbol"])
        tried = inputs.attempts_in(memory["attempts"], *key)
        spent = inputs.ideas_spent(memory["spent"], *key)
        rate = factors.past(memory["by_family"], r["family"], klass,
                            cfg["past"]["prior_strength"], cfg["past"]["interval"])
        multiple = measured["multiple"] if measured is not None else 0.0
        parts = {"prior": cfg["prior"]["values"][said["level"]], "evidence": values[seen],
                 "signal": factors.signal(multiple, cfg["signal"]["cap"]),
                 "gap": factors.gap(tried), "past": rate["rate"],
                 "brake": factors.brake(spent, cfg["brake"]["half"]),
                 "against": cfg["evidence"]["against_brake"] if seen == "against" else 1.0}
        cells.append({
            **dict(zip(CELL, key)), "asset_class": klass,
            "taxonomy_family": cfg["taxonomy_family"][r["family"]],
            "points": round(factors.points(parts, cfg["weights"]), 1),
            "factors": {k: round(v, 3) for k, v in parts.items()},
            "prior": said["level"], "pullback": said["pullback"], "evidence": seen,
            "entered_by": entered, "multiple": round(multiple, 2), "attempts": tried,
            "ideas_spent": spent,
            "past": {k: round(v, 3) if isinstance(v, float) else v for k, v in rate.items()},
            "trades_per_year": round(measured["trades_per_year"], 1) if measured is not None else None,
            "variant": (f"{swept['entry']} {swept['param']:g} {swept['exit']}"
                        if seen == "plateau" else ""),
            "provisional_costs": r["symbol"] in marks["provisional_costs"],
            "lead": r["lead"], "p": round(r["p"], 4), "stability": round(r["stability"], 2),
            "score": round(r["score"], 1)})
    cells.sort(key=lambda c: (-c["points"], -c["multiple"], c["symbol"], c["timeframe"]))
    for n, c in enumerate(cells, 1):
        c["rank"] = n
    return {"generated": datetime.now().isoformat(timespec="seconds"), "cells": cells,
            "cell_families": int(len(scores)), "gated_out": int(len(scores) - len(cells)),
            "closed_runs": sum(r["closed"] for r in memory["by_family"]),
            "weights": cfg["weights"], "signal_cap": cfg["signal"]["cap"],
            "brake_half": cfg["brake"]["half"], "interval": cfg["past"]["interval"],
            "rows": cfg["page"]["rows"], "evidence_values": values,
            "against_brake": cfg["evidence"]["against_brake"],
            "pullback_as": cfg["prior"]["pullback_as"]}
