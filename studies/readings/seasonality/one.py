"""One strategy's oos1 result broken down by UTC month, weekday and hour, each cell against the calendar null."""

import time
import zlib
from typing import Any

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.seasonality import cells as cal, null, verdict

MODULE = "seasonality"
SIZES = {"mes": 12, "día": 7, "hora": 24}
TITLES = {"mes": "Por mes", "día": "Por día de la semana", "hora": "Por hora (UTC)"}
MEANINGS = {
    "fragil": "Una celda del calendario rinde más que el resto más allá del azar, y sin sus "
    "operaciones el neto de oos1 es cero o negativo: el resultado ES esa celda. Fragilidad a "
    "reportar; no se convierte en filtro horario (regla 15, D-1).",
    "concentrado": "Alguna celda se aparta del resto más allá del azar, pero sin ella la "
    "estrategia sigue ganando. Se informa; no es fragilidad.",
    "repartido": "Ninguna celda se aparta del resto más de lo que lo haría repartiendo las "
    "mismas operaciones al azar: el calendario no explica el resultado.",
    "sin_datos": "Ninguna dimensión tiene dos celdas con el mínimo de operaciones: no hay "
    "nada que comparar.",
}
GLOSSARY = [
    {
        "term": "P&L por lote",
        "text": "Beneficio de la operación dividido entre su tamaño: lo que el nulo baraja, para "
        "que el tamaño que crece con el capital no parezca una estación.",
    },
    {
        "term": "p (nulo de calendario)",
        "text": "Probabilidad de que una celda se aparte tanto del resto si las mismas "
        "operaciones se repartieran al azar: horas y días barajados dentro de cada mes real, "
        "meses reasignados como bloques enteros de un mes.",
    },
    {
        "term": "q (Benjamini-Hochberg)",
        "text": "La p corregida por todas las celdas probadas a la vez de esta estrategia "
        "(meses, días y horas, en apertura y en cierre): con decenas de celdas alguna destaca "
        "por azar, y q lo descuenta.",
    },
    {
        "term": "sin datos suficientes",
        "text": "Celda con menos operaciones que el mínimo del dueño: se enseña, pero no se "
        "prueba ni entra en la corrección.",
    },
]


def measure(placed: pd.DataFrame, draws: int, rng: np.random.Generator) -> pd.DataFrame:
    """Every calendar cell of one strategy with its numbers and its null p.

    Args:
        placed: `cells.place()`'s output for one strategy.
        draws: Shuffles per null.
        rng: Seeded generator.

    Returns:
        One row per (dimension, anchor, cell) that holds a trade: `key`, `dimension`,
        `anchor`, `cell`, `label`, `n`, `mean` (per lot), `excess` (mean minus the rest's
        mean, per lot), `pnl` (account currency), `win` (share > 0), `p` (NaN only for a
        cell with no trade, which is not listed).
    """
    values = placed["per_lot"].to_numpy()
    pnl = placed["pnl"].to_numpy()
    families = [(a, d) for a in cal.ANCHORS for d in cal.DIMENSIONS]
    codes = {
        (a, d): placed[f"{d}·{a}"].to_numpy() - (1 if d == "mes" else 0)
        for a, d in families
    }
    shuffled = [f for f in families if f[1] != "mes"]
    pooled = null.within_strata(
        values,
        placed["stratum"].to_numpy(),
        np.hstack([null.onehot(codes[f], SIZES[f[1]]) for f in shuffled]),
        draws,
        rng,
    )
    starts = np.cumsum([0] + [SIZES[f[1]] for f in shuffled])
    p = {f: pooled[starts[i] : starts[i + 1]] for i, f in enumerate(shuffled)}
    for a in cal.ANCHORS:
        p[(a, "mes")] = null.relabel_blocks(
            values,
            placed[f"block·{a}"].to_numpy(),
            null.onehot(codes[(a, "mes")], 12),
            draws,
            rng,
        )
    rows = []
    for anchor, dimension in families:
        own = codes[(anchor, dimension)]
        for c in np.unique(own):
            inside = own == c
            cell = int(c) + 1 if dimension == "mes" else int(c)
            rows.append(
                {
                    "key": f"{dimension}·{anchor}·{cal.label(dimension, cell)}",
                    "dimension": dimension,
                    "anchor": anchor,
                    "cell": cell,
                    "label": cal.label(dimension, cell),
                    "n": int(inside.sum()),
                    "mean": float(values[inside].mean()),
                    "excess": float(values[inside].mean() - values[~inside].mean())
                    if (~inside).any()
                    else 0.0,
                    "pnl": float(pnl[inside].sum()),
                    "win": float((values[inside] > 0).mean()),
                    "p": float(p[(anchor, dimension)][c]),
                }
            )
    return pd.DataFrame(rows)


def _rng(seed: int, identity: str) -> np.random.Generator:
    """One strategy's generator: the run's root seed and its identity, so its page and its row
    in the population draw exactly the same shuffles."""
    return np.random.default_rng([seed, zlib.crc32(identity.encode())])


def _state(row: pd.Series) -> str:
    """A cell's colour word: discovery paying more (pass) or less (fail), tested, or no data."""
    if not bool(row["tested"]):
        return "none"
    if bool(row["discovery"]):
        return "pass" if float(row["excess"]) > 0 else "fail"
    return "info"


def tabs(judged: pd.DataFrame, min_trades: int, q_max: float) -> list[dict]:
    """One tab per dimension, a selector for the anchor (open or close)."""
    out = []
    for dimension in cal.DIMENSIONS:
        shown = []
        for anchor in cal.ANCHORS:
            part = judged[
                (judged["dimension"] == dimension) & (judged["anchor"] == anchor)
            ]
            states = [_state(r) for _, r in part.iterrows()]
            bars = {
                "kind": "bars",
                "title": f"P&L medio por lote, {TITLES[dimension].lower()} de {anchor}",
                "unit": "USD",
                "reference": 0.0,
                "items": [
                    {"label": r["label"], "value": r["mean"], "error": None, "state": s}
                    for (_, r), s in zip(part.iterrows(), states, strict=True)
                ],
                "note": f"Verde/rojo: la celda paga más/menos que el resto con q ≤ {q_max}. "
                f"Gris: menos de {min_trades} operaciones, sin probar.",
                "select": {"anclaje": anchor},
            }
            frame = pd.DataFrame(
                {
                    "celda": part["label"],
                    "operaciones": part["n"],
                    "P&L medio por lote": part["mean"],
                    "exceso sobre el resto": part["excess"],
                    "P&L total": part["pnl"],
                    "% ganadoras": 100 * part["win"],
                    "p": pd.Series(part["p"]).where(pd.Series(part["tested"])),
                    "q": part["q"],
                    "lectura": [
                        {
                            "pass": "paga más",
                            "fail": "paga menos",
                            "info": "como el resto",
                        }.get(s, "sin datos suficientes")
                        for s in states
                    ],
                }
            )
            table = blocks.table(
                f"{TITLES[dimension]}, {anchor}",
                frame,
                f"p del nulo de calendario y q tras Benjamini-Hochberg sobre todas las celdas "
                f"probadas; una celda con menos de {min_trades} operaciones no se prueba.",
            )
            table["states"] = [[s] * len(frame.columns) for s in states]
            table["select"] = {"anclaje": anchor}
            shown += [bars, table]
        out.append(
            envelope.tab(
                dimension,
                TITLES[dimension],
                shown,
                selectors=[
                    {
                        "key": "anclaje",
                        "label": "hora de",
                        "options": list(cal.ANCHORS),
                        "default": "apertura",
                    }
                ],
            )
        )
    return out


def run(
    strategy: str,
    placed: pd.DataFrame,
    cfg: dict,
    identity: str | None = None,
    warnings: list[dict] | None = None,
) -> dict[str, Any]:
    """One strategy's calendar reading.

    Args:
        strategy: Its name in the export.
        placed: `cells.place()`'s output for this strategy's oos1 trades.
        cfg: What `inputs.config()` returned.
        identity: SHA-256 of its normalised XML, read from the harvest; with the run's
            root seed it seeds the shuffles, so its page and its population row agree.
        warnings: The caller's warnings (clock, dropped times), carried onto the page.

    Returns:
        The contract dict; `summary` carries verdict, cell, rest_pnl, tested and found.
    """
    started = time.time()
    lost = placed.attrs.get("dropped", 0)
    if lost:
        warnings = [
            *(warnings or []),
            {
                "code": "dst_dropped",
                "state": "info",
                "text": f"{lost} operaciones caen en una hora que el cambio de hora salta o "
                "repite: fuera de la lectura, no se adivinan.",
            },
        ]
    min_trades, q_max = cfg["verdict"]["min_trades"], cfg["verdict"]["fdr_q"]
    judged = verdict.judge(
        measure(
            placed,
            cfg["shuffle"]["draws"],
            _rng(cfg["shuffle"]["seed"], identity or strategy),
        ),
        min_trades,
        q_max,
    )
    said = verdict.call(judged, float(placed["pnl"].sum()))
    rest = said["rest_pnl"]
    meaning = MEANINGS[said["verdict"]]
    if said["cell"]:
        meaning += f" Celda: {said['cell']}; neto de oos1 sin ella: {rest:,.0f}."
    head = blocks.verdict(said["verdict"], verdict.STATES[said["verdict"]], meaning)
    return envelope.envelope(
        MODULE,
        strategy,
        identity,
        cfg,
        started,
        tabs(judged, min_trades, q_max),
        head,
        warnings,
        GLOSSARY,
        summary={
            "verdict": said["verdict"],
            "cell": said["cell"],
            "rest_pnl": rest,
            "trades": len(placed),
            "tested": int(judged["tested"].sum()),
            "found": int(judged["discovery"].sum()),
            "found_cells": judged.loc[
                judged["discovery"] & (judged["excess"] > 0), "key"
            ].tolist(),
        },
    )
