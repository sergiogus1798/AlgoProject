"""The pass/fail matrix as SQX paints it and the cells' equity, as the contract's blocks (encargo 37)."""

import numpy as np
import pandas as pd

from core.study import blocks
from studies.optimisation.wfm import labels
from studies.optimisation.wfm.measure import equity, gaterule

PARTIAL = ("Export anterior al 2026-10-01: solo guarda {n} de las 10 condiciones (las `oos`), "
           "leídas de `_build.yaml`. Con menos condiciones activas el umbral del {pct} % es más "
           "fácil de alcanzar que en SQX: esto es un mínimo, no el filtro que corrió. Vuelve a "
           "exportar (`sqx.export.export_wfm`) para ver las diez.")


def _axes(mine: pd.DataFrame) -> tuple[list[int], list[int]]:
    """Rows (runs) and columns (oos_pct) in SQX's order."""
    return sorted(mine["runs"].unique()), sorted(mine["oos_pct"].unique())


def _tip(cell: pd.DataFrame, head: str) -> str:
    """One cell's hover: every condition with its value, threshold and ✓/✗."""
    lines = [f"{'✓' if r.met else '✗'} {labels.condition(r._asdict())}: {r.value:,.2f}"
             for r in cell.sort_values("condition").itertuples()]
    return "\n".join([head, *lines])


def matrix(checked: pd.DataFrame, scored: pd.DataFrame, rule: dict, strategy: str,
           sqx_failed: bool | None, partial: bool) -> list[dict]:
    """The pass/fail table for one strategy's cells, the area rule, and each condition's count.

    Args:
        checked: `run.read`'s `checked`, one row per cell and condition.
        scored: `run.read`'s `scored`, one row per cell.
        rule: `threshold_pct`, `rows`, `cols`, `min_squares` — the strategy's own.
        strategy: Which strategy to draw.
        sqx_failed: Whether SQX marked it failed, None when the export does not say.
        partial: The export predates the ten conditions.

    Returns:
        A callout when the reading is partial, the matrix (each cell «met/active», green or
        red, ▣ inside the best rectangle, ◆ on the recommended cell, the conditions on
        hover), the verdict of the area rule set against SQX's own mark, and a table of
        how many cells meet each condition.
    """
    mine, cond = scored[scored["strategy"] == strategy], checked[checked["strategy"] == strategy]
    rows, cols = _axes(mine)
    at = mine.set_index(["runs", "oos_pct"])
    score = at["score_pct"].unstack().reindex(index=rows, columns=cols).to_numpy()
    passed = score >= rule["threshold_pct"]
    got = gaterule.area(passed, score, rule["rows"], rule["cols"], rule["min_squares"])
    inside = np.zeros_like(passed)
    if got["corner"] is not None:
        i, j = got["corner"]
        inside[i:i + rule["rows"], j:j + rule["cols"]] = True
    text, tips, states = [], [], []
    for i, r in enumerate(rows):
        line, tip, state = [str(r)], [None], [None]
        for j, c in enumerate(cols):
            met, active = at.loc[(r, c), "met"], at.loc[(r, c), "active"]
            mark = "◆ " if (i, j) == got["centre"] else "▣ " if inside[i, j] else ""
            line.append(f"{mark}{met}/{active}")
            state.append("pass" if passed[i, j] else "fail")
            tip.append(_tip(cond[(cond["runs"] == r) & (cond["oos_pct"] == c)],
                            f"{r} pasadas · {c} % fuera de muestra — {met}/{active} = "
                            f"{score[i, j]} % ({'aprobada' if passed[i, j] else 'suspendida'})"))
        text.append(line)
        tips.append(tip)
        states.append(state)
    grid = pd.DataFrame(text, columns=["pasadas \\ % OOS"] + [f"{c}%" for c in cols])
    ci, cj = got["centre"]
    where = ("" if got["corner"] is None else
             f" Mejor rectángulo {rule['rows']}×{rule['cols']} (▣): pasadas {rows[got['corner'][0]]}"
             f"-{rows[got['corner'][0] + rule['rows'] - 1]}, % OOS {cols[got['corner'][1]]}"
             f"-{cols[got['corner'][1] + rule['cols'] - 1]}, con {got['count']} aprobadas.")
    sqx = ("" if sqx_failed is None or partial else
           " Coincide con lo que marcó SQX." if sqx_failed != got["passed"] else
           " ⚠️ NO coincide con lo que marcó SQX: avisa, la reconstrucción tiene un fallo.")
    counts = (cond.groupby("condition").agg(met=("met", "sum"), cells=("met", "size"),
                                             median=("value", "median"))
              .join(cond.drop_duplicates("condition").set_index("condition")
                    [["family", "metric", "op", "threshold"]]))
    summary = pd.DataFrame({
        "condición": [labels.condition(r) for r in counts.reset_index().to_dict("records")],
        "celdas que cumplen": [f"{m} de {n}" for m, n in zip(counts["met"], counts["cells"])],
        "mediana de las celdas": counts["median"].round(2)})
    return [
        *([{"kind": "callout", "state": "watch", "text": PARTIAL.format(
            n=int(mine["active"].iloc[0]), pct=rule["threshold_pct"])}] if partial else []),
        {**blocks.table("Matriz pasa / no pasa", grid,
                        f"Cada celda: condiciones cumplidas sobre activas; aprueba con el "
                        f"{rule['threshold_pct']} %. Pasa el ratón por una celda para ver cada "
                        f"condición con su valor."), "states": states, "tips": tips},
        {"kind": "callout", "state": "pass" if got["passed"] else "fail",
         "text": (f"{'Aprueba' if got['passed'] else 'No aprueba'}: necesita "
                  f"{rule['min_squares']} celdas aprobadas en un rectángulo {rule['rows']}×"
                  f"{rule['cols']}.{where} Combinación recomendada (◆, el centro de ese "
                  f"rectángulo): {rows[ci]} pasadas con {cols[cj]} % fuera de muestra.{sqx}")},
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
