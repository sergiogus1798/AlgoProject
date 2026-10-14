"""Every strategy of one harvest read by calendar, and whether the block shows more calendar than chance."""

import time
from typing import Any, TypedDict

import pandas as pd

from core.study import blocks, result as envelope
from core.study.result import progress
from studies.readings.seasonality import cells as cal, one, verdict

MODULE = one.MODULE


class Population(TypedDict):
    """The population's contract result and the per-strategy panel."""

    population: dict[str, Any]
    panel: pd.DataFrame


def run(
    trades: pd.DataFrame,
    names: pd.Series,
    zone: str,
    cfg: dict,
    warnings: list[dict],
) -> Population:
    """Every strategy's calendar reading, then the count against what chance would name.

    Args:
        trades: `inputs.oos_trades()` — oos1 rows of every strategy.
        names: Identity -> strategy name.
        zone: The feed's clock.
        cfg: What `inputs.config()` returned (its `shuffle.seed` is the run's root).
        warnings: The clock warnings, carried onto every page.

    Returns:
        {"population", "panel" (one row per strategy: name, identity, trades, tested, found,
        verdict, cell, rest_pnl)}. A strategy's own page is drawn on demand (`--strategy`).
    """
    started = time.time()
    rows = []
    groups = list(trades.groupby("identity", sort=True))
    for i, (identity, own) in enumerate(groups):
        name = str(names.get(identity, identity))
        placed = cal.place(own, zone)
        got = one.run(name, placed, cfg, str(identity), warnings)
        rows.append({"strategy": name, "identity": identity, **got["summary"]})
        progress(int(100 * (i + 1) / len(groups)), name)
    panel = pd.DataFrame(rows)
    q_max = cfg["verdict"]["fdr_q"]
    judged = panel[panel["verdict"] != "sin_datos"] if len(panel) else panel
    found = int((judged["found"] > 0).sum()) if len(judged) else 0
    p_block = verdict.beyond_chance(found, len(judged), q_max)
    counts = panel["verdict"].value_counts() if len(panel) else pd.Series(dtype=int)
    share = {w: int(counts[w]) if w in counts.index else 0 for w in verdict.STATES}
    hits = pd.Series(
        [
            c
            for cs in (panel["found_cells"] if "found_cells" in panel else [])
            for c in cs
        ],
        dtype=object,
    ).value_counts()
    lede = (
        f"{found} de {len(judged)} estrategias con alguna celda descubierta; el azar, con "
        f"BH a q ≤ {q_max}, no pasaría de {q_max * len(judged):.1f} (binomial p = {p_block:.3g})."
    )
    tally = {
        "kind": "bars",
        "title": "Estrategias por lectura",
        "unit": "",
        "reference": None,
        "items": [
            {"label": w, "value": n, "error": None, "state": verdict.STATES[w]}
            for w, n in share.items()
        ],
        "note": lede,
    }
    recurring = {
        "kind": "bars",
        "title": "Celdas que pagan más que el resto, por nº de estrategias",
        "unit": "",
        "reference": q_max * len(judged),
        "items": [
            {"label": str(k), "value": int(v), "error": None, "state": "info"}
            for k, v in hits.head(20).items()
        ],
        "note": "Una celda que se repite en muchas estrategias es una dependencia del bloque "
        "entero, no de una estrategia. La línea es el techo del azar para el bloque.",
    }
    shown = panel.drop(columns=["found_cells"], errors="ignore")
    table = blocks.table("Cada estrategia por calendario", shown, lede)
    table["states"] = [
        [verdict.STATES[v]] * len(shown.columns) for v in shown["verdict"]
    ]
    population = envelope.envelope(
        MODULE,
        None,
        None,
        cfg,
        started,
        [
            envelope.tab(
                "panel",
                "La población por calendario",
                [tally, recurring, table],
                note=lede,
            )
        ],
        blocks.verdict(
            "más calendario que el azar" if p_block <= q_max else "como el azar",
            "watch" if p_block <= q_max else "pass",
            lede,
        ),
        warnings,
        one.GLOSSARY,
        summary={"found": found, "judged": len(judged), "p_block": p_block, **share},
    )
    return {"population": population, "panel": shown}
