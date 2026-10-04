"""One WFM export read as one result, and each strategy's own reading: what the window paints."""

import time
from pathlib import Path

import pandas as pd

from core.study import blocks, output, result as envelope
from studies.optimisation.wfm import assetview, contract, objectives, run as reading
from studies.optimisation.wfm.verdict import call

MODULE = "studies.optimisation.wfm"
STATE = {call.PREDICTS: "pass", call.BLIND: "watch", call.PERVERSE: "fail"}
GLOSSARY = [
    {"term": "Celda", "text": "Una combinación de cuántos tramos y qué parte fuera de muestra. "
     "Es la unidad de observación: todas reparten la misma historia."},
    {"term": "ρ por celda", "text": "Dentro de una celda, Spearman entre el resultado que un "
     "tramo tuvo al optimizarse (ventana IS) y el que ese mismo tramo tuvo después, corriendo "
     "de verdad (ventana OOS) — no compara celdas entre sí, ni qué tramos fueron buenos en "
     "distintas métricas. Bajo: ni siquiera dentro de esa celda el parámetro que ganó en IS "
     "tendía a ganar en OOS, así que esa celda concreta no sostiene su propio veredicto."},
    {"term": "Blind ρ", "text": "El veredicto de la estrategia: ρ es la media (en z de Fisher) de "
     "los ρ por celda — en cada celda, Spearman entre lo que cada tramo logró al optimizarse "
     "(IS) y lo que logró después (OOS) — con un intervalo de confianza que remuestrea celdas. "
     "Blind (ciego): el intervalo incluye 0, optimizar mejor no dice nada de lo que viene. "
     "Predicts: está por encima de 0. Perverse: por debajo, lo que optimiza mejor va peor."},
    {"term": "Veredicto de SQX", "text": "La regla del área de SQX (un rectángulo de celdas "
     "aprobadas en la matriz Pass / Fail). Es el juicio propio de SQX, aparte del nuestro (ρ)."},
    {"term": "Deriva", "text": "Qué parte de los parámetros cambia el optimizador de un tramo "
     "al siguiente, en desviaciones típicas de cada uno."}]


def sqx_says(message: str | None) -> str:
    """SQX's own English message, quoted after a Spanish sentence saying what it means."""
    return ("No superó el filtro de robustez del cross check. " if message and "Robustness" in message
            else "") + f"SQX dice: «{message}»"


def pct(share: float) -> str:
    """A share as the owner reads it: 0.3333 -> «33,3 %»."""
    return f"{share * 100:.1f} %".replace(".", ",")


def grid(cells: pd.DataFrame, strategy: str) -> dict:
    """One strategy's ρ per cell: runs down, out-of-sample share across."""
    mine = cells[cells["strategy"] == strategy].pivot_table(index="runs", columns="oos_pct",
                                                           values="rho", observed=True)
    return {"kind": "grid", "title": f"Correlación IS→OOS dentro de la celda (Spearman) — {strategy}",
            "help": "Dentro de cada celda, Spearman entre lo que cada tramo logró al optimizarse "
                    "(ventana IS) y lo que logró después (ventana OOS), sobre la métrica leída. "
                    "Alto (verde): el tramo que mejor optimizó tendió a ir mejor después. Cerca "
                    "de 0: optimizar no predice. Negativo (rojo): optimizar mejor fue peor después.",
            "rows": [str(r) for r in mine.index], "cols": [f"{c}%" for c in mine.columns],
            "values": [[None if pd.isna(v) else float(v) for v in row]
                       for row in mine.to_numpy()],
            "scale": "diverging", "levels": [-0.6, -0.4, -0.2, -0.05, 0.05, 0.2, 0.4, 0.6],
            "labels": [[None if pd.isna(v) else f"{v:+.2f}".replace(".", ",") for v in row]
                       for row in mine.to_numpy()], "note": "Filas: número de tramos. Columnas: parte fuera de muestra."}


def member(strategy: str, got: dict, result: dict, cfg: dict, started: float,
           failed: str | None, identity: str | None = None) -> dict:
    """One strategy's verdict and its matrix, flagged when SQX itself failed it."""
    comp = result["companions"]
    shown = contract.matrix(result["checked"], result["scored"],
                            result["rules"].loc[strategy].to_dict(), strategy,
                            result["sqx_failed"].get(strategy), result["objectives"] is None)
    at = next(i for i, b in enumerate(shown) if b["kind"] == "table")
    # the ρ matrix to the right of the Pass / Fail one
    shown.insert(at + 1, grid(result["cells"], strategy) | {"beside": True})
    equity_one, selectors = contract.equity_versus(result["trades"], result["original"],
                                                   result["windows"], strategy)
    sqx = result["sqx_failed"].get(strategy)
    return envelope.envelope(
        MODULE, strategy, identity, cfg, started,
        [envelope.tab("matrix", "La matriz", [
            *shown,
            *contract.equity_blocks(result["trades"], strategy),
            *equity_one,
            blocks.table("La misma correlación en otras métricas",
                         comp[comp["strategy"] == strategy].drop(columns=["strategy"]).rename(columns={
                             "metric": "Métrica", "low": "Límite inferior", "high": "Límite superior",
                             "share_negative": "Celdas con ρ negativo"}),
                         "Un veredicto que sólo se sostiene en la métrica con la que se leyó "
                         "es una propiedad de esa métrica, no de la estrategia.")],
                      selectors=selectors),
         objectives.tab(result["checked"], result["objectives"], strategy),
         *([assetview.tab(result["benchmark"][strategy])]
           if strategy in result["benchmark"] else [])],
        blocks.verdict(f"{got['verdict'].capitalize()} ρ", STATE[got["verdict"]],
                       call.sentence(got, result["warning"]).replace("**", ""), got["rho"],
                       [*([{"label": "SQX: Failed" if failed or sqx else "SQX: Pass", "state": "fail" if failed or sqx else "pass",
                            "value": None,
                            "note": "El juicio propio de SQX (regla del área de la matriz), "
                                    "aparte de nuestro ρ. "
                                    + (f"No pasó. {sqx_says(failed)}" if failed else "Pasó.")}]
                          if sqx is not None or failed else []),
                        {"label": "Celdas con ρ negativo", "state": "info",
                         "value": got["share_negative"], "shown": pct(got["share_negative"]),
                         "note": "De las celdas de la matriz, cuántas tienen Spearman IS→OOS bajo 0."},
                        {"label": "Parámetros que cambian por tramo",
                         "state": "watch" if got["drift_high"] else "info",
                         "value": got["share_changed"], "shown": pct(got["share_changed"]),
                         "note": "Qué parte de los parámetros re-decide el optimizador de un "
                                 "tramo al siguiente."}]),
        # SQX's own area rule failed it and, with nothing deleted, it is still here: the
        # owner wants that raised wherever the strategy is read (2026-09-26).
        [{"code": "failed_en_sqx", "state": "fail",
          "text": f"SQX marcó esta estrategia como fallida en la Walk Forward Matrix. {sqx_says(failed)}"}]
        if failed else None,
        glossary=GLOSSARY, summary={k: v for k, v in got.items() if k != "verdict"}
        | {"verdict": got["verdict"], "sqx_failed": bool(failed)})


def failures(directory: Path) -> dict[str, str]:
    """The strategies SQX's own area rule failed, with the filter that failed them."""
    status = directory / "status.parquet"
    return ({} if not status.exists() else
            pd.read_parquet(status).query("sqx_failed").set_index("strategy")["sqx_filter"]
            .to_dict())


def one(directory: Path, cfg: dict, strategy: str) -> dict:
    """One strategy of the export alone, the same result the whole export gives it.

    Args:
        directory: The export's `wfm/` folder.
        cfg: What config.load() returned.
        strategy: Its name as the export spells it.

    Returns:
        The contract dict, its identity resolved.
    """
    started = time.time()
    result = reading.read(directory, cfg, strategy)
    if strategy not in result["verdicts"]:
        raise SystemExit(f"{strategy} no tiene celdas con pasos suficientes en {directory}")
    return member(strategy, result["verdicts"][strategy], result, cfg, started,
                  failures(directory).get(strategy),
                  output.identify(directory, [strategy]).get(strategy))


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
    failed = failures(directory)
    members = [member(s, g, result, cfg, started, failed.get(s), ident.get(s))
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
