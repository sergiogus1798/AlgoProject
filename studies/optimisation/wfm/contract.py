"""SQX's pass/fail matrix on the corrected conditions and the cells' equity, as the contract's blocks."""

from collections.abc import Iterable
from typing import Any, cast
import re

import numpy as np
import pandas as pd

from core.study import blocks
from studies.optimisation.wfm import labels
from studies.optimisation.wfm.measure import equity

SEEN = ("El 67–79 % de este fuera de muestra es dato ya visto (build y oos1): el generador "
        "construyó la estrategia en build y el paso 8 la eligió por oos1. Las 30 celdas valen "
        "por unas pocas independientes. Esta matriz se anota y no decide.")


def _axes(mine: pd.DataFrame) -> tuple[list[int], list[int]]:
    """Rows (runs) and columns (oos_pct) in SQX's order."""
    return sorted(mine["runs"].unique()), sorted(mine["oos_pct"].unique())


def _tip(cell: pd.DataFrame, head: str) -> str:
    """One cell's hover: every condition with its value, threshold and ✓/✗."""
    lines = [f"{'✓' if r.met else '✗'} {labels.condition(r._asdict())}: {r.value:,.2f}"
             for r in cast(Iterable[Any], cell.sort_values("condition").itertuples())]
    return "\n".join([head, *lines])


def matrix(checked: pd.DataFrame, scored: pd.DataFrame, rule: dict, strategy: str,
           found: dict, sqx_failed: bool | None) -> list[dict]:
    """SQX's pass/fail matrix on the corrected conditions, its area rule, each condition's count.

    Args:
        checked: `run.read`'s `checked`: one row per cell and condition, the score read on
            the out-of-sample runs alone.
        scored: `run.read`'s `scored`, one row per cell.
        rule: `threshold_pct`, `rows`, `cols`, `min_squares` — the strategy's own.
        strategy: Which strategy to draw.
        found: `run.area` for it.
        sqx_failed: Whether SQX marked it failed, None when the export does not say.

    Returns:
        The fixed warning, the matrix (each cell «met/active», green or red, ▣ inside the
        best rectangle, the conditions on hover), what the area rule gives beside what SQX
        itself marked, and a table of how many cells meet each condition. No recommended
        cell: its parameters are optimised on oos2.
    """
    mine = cast(pd.DataFrame, scored[scored["strategy"] == strategy])
    cond = cast(pd.DataFrame, checked[checked["strategy"] == strategy])
    rows, cols = _axes(mine)
    at = mine.set_index(["runs", "oos_pct"])
    score = cast(pd.DataFrame, at["score_pct"].unstack()).reindex(index=rows, columns=cols).to_numpy()
    passed = score >= rule["threshold_pct"]
    inside = np.zeros_like(passed)
    if found["corner"] is not None:
        i, j = found["corner"]
        inside[i:i + rule["rows"], j:j + rule["cols"]] = True
    text, tips, states = [], [], []
    for i, r in enumerate(rows):
        line: list[str] = [str(r)]
        tip: list[str | None] = [None]
        state: list[str | None] = [None]
        for j, c in enumerate(cols):
            met, active = at.loc[(r, c), "met"], at.loc[(r, c), "active"]
            line.append(f"{'▣ ' if inside[i, j] else ''}{met}/{active}")
            state.append("pass" if passed[i, j] else "fail")
            tip.append(_tip(cast(pd.DataFrame, cond[(cond["runs"] == r) & (cond["oos_pct"] == c)]),
                            f"{r} pasadas · {c} % de la ventana de optimización fuera de "
                            f"muestra — {met}/{active} = {score[i, j]} % "
                            f"({'aprobada' if passed[i, j] else 'suspendida'})"))
        text.append(line)
        tips.append(tip)
        states.append(state)
    grid = pd.DataFrame(text, columns=pd.Index(["pasadas \\ % OOS"] + [f"{c}%" for c in cols]))
    where = ("" if found["corner"] is None else
             f" Mejor rectángulo {rule['rows']}×{rule['cols']} (▣): pasadas {rows[found['corner'][0]]}"
             f"-{rows[found['corner'][0] + rule['rows'] - 1]}, % OOS {cols[found['corner'][1]]}"
             f"-{cols[found['corner'][1] + rule['cols'] - 1]}, con {found['count']} aprobadas.")
    sqx = ("" if sqx_failed is None else
           f" SQX, con el score que cuenta la primera ventana optimizada, la marcó como "
           f"{'fallida' if sqx_failed else 'aprobada'}.")
    counts = (cond.groupby("condition").agg(met=("met", "sum"), cells=("met", "size"),
                                             median=("value", "median"))
              .join(cast(pd.DataFrame, cond.drop_duplicates("condition")).set_index("condition")
                    [["family", "metric", "op", "threshold"]]))
    summary = pd.DataFrame({
        "condición": [labels.condition(r) for r in counts.reset_index().to_dict("records")],
        "celdas que cumplen": [f"{m} de {n}" for m, n in zip(counts["met"], counts["cells"])],
        "mediana de las celdas": counts["median"].round(2)})
    return [
        {"kind": "callout", "state": "watch", "text": SEEN},
        {**blocks.table("Matriz Pass / Fail corregida", grid,
                        f"Cada celda: condiciones cumplidas sobre activas; aprueba con el "
                        f"{rule['threshold_pct']} %. El score se calcula sólo con las pasadas "
                        f"fuera de muestra, sin la primera ventana optimizada. Pasa el ratón "
                        f"por una celda para ver cada condición con su valor."),
         "states": states, "tips": tips, "compact": True},
        {"kind": "callout", "state": "info",
         "text": (f"Área corregida: {found['cells']} de {passed.size} celdas aprueban; "
                  f"{'encuentra' if found['passed'] else 'no encuentra'} {rule['min_squares']} "
                  f"aprobadas en un rectángulo {rule['rows']}×{rule['cols']}.{where}{sqx} "
                  f"Los umbrales de las condiciones se calibraron con el oro.")},
        blocks.table("Qué condición manda", summary,
                     "Cuántas celdas cumple cada condición: la que menos cumple es la que "
                     "suspende la matriz.")]


def equity_blocks(trades: pd.DataFrame, strategy: str) -> list[dict]:
    """The cells' out-of-sample equity together, and one table aggregating them.

    Args:
        trades: `run.read`'s `trades` table.
        strategy: Which strategy to draw.

    Returns:
        A "cone" block (the median cell marked, bands 2.5-97.5 and 25-75 across cells) and
        the aggregate table, or nothing when fewer than two cells traded. The bands are the
        spread across cells, not a Monte Carlo — said in the note.
    """
    names, curves = equity.oos_curves(trades, strategy)
    if len(curves) < 2:
        return []
    stats = equity.per_cell(trades, strategy)
    return [blocks.cone(
        f"Equity de las {len(curves)} celdas fuera de muestra", "USD",
        list(range(equity.POINTS)), curves, list(np.median(curves, axis=0))) | {
        "note": "Eje: % de operaciones fuera de muestra completadas, no fecha — las celdas "
                "no comparten calendario. La línea marcada es la mediana entre celdas; las "
                "bandas, p2,5-p97,5 y p25-p75 entre celdas. No hay un único equity que sea "
                "'la' WFM."},
        blocks.table("El conjunto de las celdas", equity.aggregate(stats),
                     "Una fila por métrica: cómo se reparte entre las celdas. Sharpe clásico "
                     "sobre todo el tramo fuera de muestra de la celda: P/L diario en días "
                     "laborables (los días sin operaciones cuentan como 0), media / desviación "
                     "× √252. Las celdas reparten la misma historia: la dispersión describe, "
                     "no es un error estándar.")]


def cell_name(cell: str) -> str:
    """«WF: 6 runs : 20 % OOS» as the reader says it."""
    runs, pct = re.findall(r"\d+", cell)
    return f"{runs} pasadas · {pct} % fuera de muestra"


def equity_versus(trades: pd.DataFrame, original: pd.DataFrame | None, windows: pd.DataFrame,
                  strategy: str) -> tuple[list[dict], list[dict]]:
    """One chart per cell, the cell's OOS equity against the original's, picked by a selector.

    Args:
        trades: `run.read`'s `trades`.
        original: `run.read`'s `original`, None for an export older than 2026-10-01.
        windows: `run.read`'s `windows` (the steps' run windows).
        strategy: Which strategy to draw.

    Returns:
        The 30 `lines` blocks, each tagged `select: celda`, and the tab's one selector;
        both empty when the export holds no original trades.
    """
    if original is None:
        return [], []
    got = equity.versus_original(trades, original, windows, strategy)
    names = {c: cell_name(c) for c in sorted(got, key=lambda c: [int(n) for n in re.findall(r"\d+", c)])}
    out = [{"kind": "lines", "title": f"Equity de la celda ({names[c]}) frente a la original",
            "unit": "USD", "x": v["x"], "select": {"celda": names[c]},
            "series": [{"label": f"celda ({v['n_cell']} operaciones)", "role": "real",
                        "values": v["cell"]},
                       {"label": f"original ({v['n_original']} operaciones)", "role": "reference",
                        "values": v["original"]}],
            "note": "Las dos curvas ganan sólo en los mismos tramos fuera de muestra de esta celda "
                    "(los huecos entre tramos no cuentan para ninguna) y parten de 0 en el primero. "
                    "La celda es la estrategia re-optimizada en cada tramo; la original, con los "
                    "parámetros fijos del backtest. Si la celda queda por debajo, reoptimizar "
                    "no compensó."} for c, v in got.items() if c in names]
    return out, [{"key": "celda", "label": "Celda", "options": list(names.values()),
                  "default": next(iter(names.values()), "")}]
