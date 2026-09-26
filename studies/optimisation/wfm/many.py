"""One WFM export read as one result, and each strategy's own reading: what the window paints."""

import time
from pathlib import Path

import pandas as pd

from core.study import blocks, output, result as envelope
from studies.optimisation.wfm import run as reading
from studies.optimisation.wfm.verdict import call

MODULE = "studies.optimisation.wfm"
STATE = {call.PREDICTS: "pass", call.BLIND: "watch", call.PERVERSE: "fail"}
GLOSSARY = [
    {"term": "Celda", "text": "Una combinación de cuántos tramos y qué parte fuera de muestra. "
     "Es la unidad de observación: todas reparten la misma historia."},
    {"term": "ρ por celda", "text": "Spearman entre lo que cada tramo rindió al optimizar y lo "
     "que rindió después, dentro de una celda."},
    {"term": "Deriva", "text": "Qué parte de los parámetros cambia el optimizador de un tramo "
     "al siguiente, en desviaciones típicas de cada uno."}]


def grid(cells: pd.DataFrame, strategy: str) -> dict:
    """One strategy's ρ per cell: runs down, out-of-sample share across."""
    mine = cells[cells["strategy"] == strategy].pivot_table(index="runs", columns="oos_pct",
                                                           values="rho", observed=True)
    return {"kind": "grid", "title": f"ρ por celda — {strategy}",
            "rows": [str(r) for r in mine.index], "cols": [f"{c}%" for c in mine.columns],
            "values": [[None if pd.isna(v) else float(v) for v in row]
                       for row in mine.to_numpy()],
            "scale": "diverging", "levels": [-0.6, -0.4, -0.2, -0.05, 0.05, 0.2, 0.4, 0.6],
            "labels": None, "note": "Filas: número de tramos. Columnas: parte fuera de muestra."}


def member(strategy: str, got: dict, result: dict, cfg: dict, started: float,
           failed: str | None) -> dict:
    """One strategy's verdict and its matrix, flagged when SQX itself failed it."""
    comp = result["companions"]
    return envelope.envelope(
        MODULE, strategy, None, cfg, started,
        [envelope.tab("matrix", "La matriz", [
            grid(result["cells"], strategy),
            blocks.table("La misma correlación en otras métricas",
                         comp[comp["strategy"] == strategy].drop(columns=["strategy"]),
                         "Un veredicto que sólo se sostiene en la métrica con la que se leyó "
                         "es una propiedad de esa métrica, no de la estrategia.")])],
        blocks.verdict(got["verdict"], STATE[got["verdict"]],
                       call.sentence(got, result["warning"]).replace("**", ""), got["rho"],
                       [{"label": "celdas con ρ negativo", "state": "info",
                         "value": got["share_negative"], "note": ""},
                        {"label": "parámetros que cambian por tramo",
                         "state": "watch" if got["drift_high"] else "info",
                         "value": got["share_changed"], "note": ""}]),
        # SQX's own area rule failed it and, with nothing deleted, it is still here: the
        # owner wants that raised wherever the strategy is read (2026-09-26).
        [{"code": "failed_en_sqx", "state": "fail",
          "text": f"SQX la marcó como FAILED en la Walk-Forward Matrix: {failed}"}] if failed else None,
        glossary=GLOSSARY, summary={k: v for k, v in got.items() if k != "verdict"}
        | {"verdict": got["verdict"], "sqx_failed": bool(failed)})


def run(directory: Path, cfg: dict) -> dict:
    """The whole export, and each strategy.

    Args:
        directory: The export's `wfm/` folder.
        cfg: What config.load() returned.

    Returns:
        {"population", "members", "table", "cells"}: the export's result, one result per
        strategy, the verdict table with identity, and the per-cell correlations.
    """
    started = time.time()
    result = reading.read(directory, cfg)
    i = result["independence"]
    names = list(result["verdicts"])
    ident = output.identify(directory, names)
    status = directory / "status.parquet"
    failed = ({} if not status.exists() else
              pd.read_parquet(status).query("sqx_failed").set_index("strategy")["sqx_filter"]
              .to_dict())
    members = [member(s, g, result, cfg, started, failed.get(s))
               for s, g in result["verdicts"].items()]
    table = pd.DataFrame([{"strategy": s, "identity": ident.get(s), **g}
                          for s, g in result["verdicts"].items()])
    table = table[["strategy", "identity", "verdict"]
                  + [c for c in table.columns if c not in ("strategy", "identity", "verdict")]]
    counts = table["verdict"].value_counts()
    population = envelope.envelope(
        MODULE, None, None, cfg, started,
        [envelope.tab("verdicts", "Veredicto por estrategia", [
            blocks.table("Cada estrategia", table.drop(columns=["identity"])),
            *[{**grid(result["cells"], s), "select": {"estrategia": s}} for s in names]],
            selectors=[{"key": "estrategia", "label": "Estrategia", "options": names,
                        "default": names[0]}]),
         envelope.tab("geometry", "Qué permite afirmar este export", [
             blocks.table("La geometría de las ventanas", pd.DataFrame(
                 [["celdas", i["cells"]], ["tramos", i["steps_total"]],
                  ["años de historia", i["history_years"]],
                  ["solapes de ejecución dentro de una celda", i["oos_overlaps_within_cell"]],
                  ["solape medio de optimización", i["is_overlap_mean"]],
                  ["años IS", f"{i['is_years_range'][0]:.1f} a {i['is_years_range'][1]:.1f}"],
                  ["años OOS", f"{i['oos_years_range'][0]:.1f} a "
                               f"{i['oos_years_range'][1]:.1f}"]], columns=["", "valor"]),
                 "La unidad es la celda y no el tramo: agrupar todos los tramos en un solo ρ "
                 "daría un intervalo varias veces más estrecho de lo que el dato soporta.")]),
         envelope.tab("drift", "Deriva del óptimo", [
             blocks.table("Cuánto re-decide el optimizador", result["drift"]),
             blocks.table("Los parámetros sobre los que más se repite",
                          result["stability"].groupby("strategy").head(3),
                          "Candidatos a congelar en cualquier diseño.")]),
         envelope.tab("axes", "Los dos ejes de la matriz", [
             blocks.table("Por número de tramos", result["by_runs"]),
             blocks.table("Por porcentaje fuera de muestra", result["by_oos"],
                          "Cada nivel son pocas celdas y todas reparten la misma historia: std "
                          "describe la dispersión, no es un error estándar.")],
             note=result["warning"] or "")],
        blocks.verdict(f"{int(counts.get(call.PREDICTS, 0))} de {len(table)} predicen",
                       "pass" if counts.get(call.PREDICTS, 0) else "watch",
                       "; ".join(f"{k} {v}" for k, v in counts.items()) + ". Leído sobre "
                       f"{result['metric']}."),
        [{"code": "ventanas", "state": "watch", "text": result["warning"]}]
        if result["warning"] else [], GLOSSARY)
    return {"population": population, "members": members, "table": table,
            "cells": result["cells"]}
