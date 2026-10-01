"""One matrix per WFM objective — each condition against its threshold, and the WF metrics SQX shows."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.optimisation.wfm import labels

KEY = "objetivo"


def _grid(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Rows runs, columns oos_pct, the value rounded to two decimals."""
    wide = frame.pivot_table(index="runs", columns="oos_pct", values=column, aggfunc="first")
    out = wide.round(2).reset_index()
    out.columns = ["pasadas \\ % OOS"] + [f"{c}%" for c in wide.columns]
    return out


def _conditions(cond: pd.DataFrame) -> list[tuple[str, dict]]:
    """One table per condition, each cell green where it holds."""
    out = []
    for i, g in cond.groupby("condition"):
        first = g.iloc[0]
        label = f"C{i + 1} · {labels.condition(first.to_dict())}"
        states = [[None] + ["pass" if m else "fail" for m in row]
                  for row in g.pivot_table(index="runs", columns="oos_pct", values="met",
                                           aggfunc="first").to_numpy()]
        out.append((label, {**blocks.table(
            label, _grid(g, "value"),
            f"Cumple en {int(g['met'].sum())} de {len(g)} celdas. "
            f"{labels.meaning(first['family'], first['metric'])}"), "states": states}))
    return out


def _shown(objectives: pd.DataFrame, taken: set[tuple[str, str]]) -> list[tuple[str, dict]]:
    """The WF metrics SQX shows whatever the conditions, the ones already a condition left out."""
    out = []
    for column in objectives.columns.drop(["strategy", "result", "oos_pct", "runs"]):
        family, _, metric = column.partition("_")
        if (family, metric) in taken or objectives[column].isna().all():
            continue
        own = column == "param_stability"
        label = "Estabilidad de parámetros (SQX)" if own else labels.name(family, metric)
        out.append((label, blocks.table(label, _grid(objectives, column),
                                        labels.MEANING[column] if own
                                        else labels.meaning(family, metric))))
    return out


def tab(checked: pd.DataFrame, objectives: pd.DataFrame | None, strategy: str) -> dict:
    """The «Objetivos» tab for one strategy.

    Args:
        checked: `run.read`'s `checked`, every cell against every condition.
        objectives: `run.read`'s `objectives`, None for an export older than 2026-10-01.
        strategy: Which strategy.

    Returns:
        A tab with one selector over the conditions first, then the other WF metrics.
    """
    cond = checked[checked["strategy"] == strategy]
    pairs = _conditions(cond)
    if objectives is not None:
        pairs += _shown(objectives[objectives["strategy"] == strategy],
                        set(zip(cond["family"], cond["metric"])))
    names = [name for name, _ in pairs]
    return envelope.tab(
        "objectives", "Los objetivos", [b | {"select": {KEY: n}} for n, b in pairs],
        selectors=[{"key": KEY, "label": "Objetivo", "options": names, "default": names[0]}],
        note="Cada objetivo en su matriz: filas, número de pasadas; columnas, % fuera de "
             "muestra. Las condiciones (C1…) llevan su verde/rojo; el resto son las métricas "
             "walk-forward que SQX enseña, sin umbral.")
