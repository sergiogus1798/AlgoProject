"""One WFM export read as one result, and each mother's own reading: what the window paints."""

from typing import Any, TypedDict, cast
import time
from pathlib import Path

import pandas as pd

from core.study import blocks, draws, output, result as envelope
from studies.optimisation.wfm import contract, objectives, run as reading, tabs
from studies.optimisation.wfm.verdict import call

MODULE = "studies.optimisation.wfm"
GLOSSARY = [
    {"term": "Celda", "text": "Una combinación de cuántas pasadas y qué parte de la ventana de "
     "optimización va fuera de muestra. Las 30 reparten la misma historia: son casi copias."},
    {"term": "Exceso neto", "text": "Lo que gana una operación por encima de la deriva del "
     "mercado mientras estuvo abierta, con sus costes cobrados. En oos2, a los costes de oos2."},
    {"term": "L1", "text": "La mediana de las 30 celdas del exceso neto por año en oos2, frente "
     "a un nulo que sortea el signo de cada semana igual para todas las celdas. Es lo que decide."},
    {"term": "L2", "text": "Reoptimizar menos la madre con sus parámetros fijos, semana a "
     "semana, con los mismos sorteos. Sólo decide si se va a reoptimizar en real."},
    {"term": "p+ y p−", "text": "p+: parte de los sorteos del nulo que iguala o supera al valor "
     "real (pequeño: gana más allá del ruido). p−: la que queda igual o por debajo (pequeño: "
     "pierde más allá del ruido)."},
    {"term": "Área de SQX", "text": "La regla propia de SQX (un rectángulo de celdas aprobadas), "
     "aquí con la nota calculada sólo sobre el tramo fuera de muestra. Se anota; no juzga."},
    {"term": "Deriva", "text": "Qué parte de los parámetros de la madre cambia el optimizador "
     "de una reoptimización a la siguiente."}]


def sqx_says(message: str | None) -> str:
    """SQX's own English message, quoted after a Spanish sentence saying what it means."""
    return ("No superó el filtro de robustez del cross check. " if message and "Robustness" in message
            else "") + f"SQX dice: «{message}»"


def warnings(got: dict, cfg: dict, failed: str | None) -> list[dict]:
    """What the reader must know before trusting the call: SQX's mark, the skew, the weekends."""
    null = cfg["null"]
    return [
        # SQX's own area rule marked it and, with nothing deleted, it is still here: the
        # owner wants that raised wherever the strategy is read (2026-09-26).
        *([{"code": "failed_en_sqx", "state": "watch", "text":
            f"SQX marcó esta estrategia como fallida en la Walk Forward Matrix. {sqx_says(failed)} "
            "Su nota mira un 67–79 % de dato ya visto: no es un juez."}] if failed else []),
        *([{"code": "asimetria", "state": "watch", "text":
            f"La serie semanal tiene asimetría {tabs.num(got['skew'])} (más de "
            f"{tabs.num(null['skew_warn'], 1)}): el nulo de volteo supone semanas simétricas y "
            "su cola baja rechaza de más. Un NO PASA aquí pide mirarlo a mano."}]
          if got["skew"] > null["skew_warn"] else []),
        *([{"code": "fin_de_semana", "state": "info", "text":
            f"El {tabs.num(got['straddle'] * 100, 1)} % de las operaciones cierra tras pasar un "
            "fin de semana abierta: L1 se repite en bloques de dos semanas, anotado en su pestaña."}]
          if got["l1_blocks"] else [])]


def recorded(strategy: str, identity: str | None, got: dict, seed: int) -> list[dict]:
    """The nulls behind this mother's L1 and L2 as `core.study.draws` rows."""
    where = {"strategy": strategy, "seed": seed}
    out = [draws.record("wfm", "l1_p_mas", got["l1"]["mediana_exceso"], got["l1"]["null"],
                        identity or "", **where, p="flip.tails", unit="USD por año")]
    if got["l1_blocks"]:
        out.append(draws.record("wfm", "l1_p_mas_bloques", got["l1_blocks"]["mediana_exceso"],
                                got["l1_blocks"]["null"], identity or "", **where,
                                p="flip.tails", unit="USD por año"))
    return out + [draws.record("wfm", "l2_p_menos", got["l2"]["delta"], got["l2"]["null"],
                               identity or "", **where, p="flip.tails", unit="USD por año")]


def member(strategy: str, result: dict, cfg: dict, started: float, failed: str | None,
           identity: str | None = None) -> dict[str, Any]:
    """One mother's state and its tabs; `facts` rides on the result for the autopilot."""
    got, said = result["measured"][strategy], result["facts"][strategy]
    verdict, found, mode = result["verdicts"][strategy], result["area"][strategy], cfg["modo_real"]
    equity_one, selectors = contract.equity_versus(result["trades"], result["original"],
                                                   result["windows"], strategy)
    drifted = result["drift"].set_index("strategy").loc[strategy].to_dict()
    stable = result["stability"][result["stability"]["strategy"] == strategy]
    one, two = said["l1"], said["l2"]
    out = envelope.envelope(
        MODULE, strategy, identity, cfg, started,
        [tabs.l1(got, said, cfg), tabs.l2(got, said, mode),
         envelope.tab("matrix", "Área de SQX corregida", [
             *contract.matrix(result["checked"], result["scored"],
                              result["rules"].loc[strategy].to_dict(), strategy, found,
                              result["sqx_failed"].get(strategy)),
             *contract.equity_blocks(result["trades"], strategy), *equity_one],
             selectors=selectors),
         tabs.drift(drifted, stable), tabs.segments(got["segments"]),
         objectives.tab(result["checked"], result["objectives"], strategy)],
        blocks.verdict(verdict["label"], call.STATE[verdict["verdict"]],
                       call.sentence(verdict, said, mode), one["mediana_exceso"], [
            {"label": "L1 · p−", "state": "fail" if one["p_menos"] <= cfg["null"]["alpha"] else "info",
             "value": one["p_menos"], "note": "Parte de los sorteos del nulo que queda igual o "
             "por debajo de la mediana real. Pequeño: pierde más allá del ruido."},
            {"label": "L1 · p+", "state": "pass" if one["p_mas"] <= cfg["null"]["alpha"] else "info",
             "value": one["p_mas"], "note": "Parte de los sorteos que iguala o supera a la real. "
             "Pequeño: gana más allá del ruido."},
            {"label": "L2 · reoptimizar − madre fija", "state": "info", "value": two["delta"],
             "shown": f"{tabs.num(two['delta'])} {tabs.UNIT}", "note": "Positivo: reoptimizar "
             f"gana a congelar en oos2 (p− {tabs.num(two['p_menos'], 3)})."},
            {"label": "Celdas efectivas", "state": "info", "value": said["celdas_efectivas"],
             "shown": tabs.num(said["celdas_efectivas"], 1),
             "note": "Por cuántas curvas independientes valen las 30 celdas."},
            {"label": "Área de SQX (sólo OOS)", "state": "info", "value": found["cells"],
             "shown": f"{found['cells']} celdas · {'pasa' if found['passed'] else 'no pasa'}",
             "note": "La regla de SQX con la nota recalculada sobre el tramo fuera de muestra. "
             "Anotada; no decide."}]),
        warnings(got, cfg, failed), GLOSSARY,
        summary=cast(dict, blocks.plain({
            "verdict": verdict["verdict"], "why": ", ".join(verdict["why"]), "modo_real": mode,
            "l1_mediana_exceso": one["mediana_exceso"], "l1_p_mas": one["p_mas"],
            "l1_p_menos": one["p_menos"], "l2_delta": two["delta"], "l2_p_menos": two["p_menos"],
            "centro_exceso_oos2": said["centro"]["exceso_oos2"],
            "celdas_efectivas": said["celdas_efectivas"],
            "frac_celdas_positivas": said["frac_celdas_positivas"], "deriva": said["deriva"],
            "area_celdas": found["cells"], "area_pasa": bool(found["passed"]),
            "asimetria": got["skew"], "recobro_oos2": got["recharged"]["money"],
            "sqx_failed": bool(failed)})))
    return out | {"facts": blocks.plain(said),
                  "draws": recorded(strategy, identity, got, cfg["null"]["seed"])}


def failures(directory: Path) -> dict[str, str]:
    """The strategies SQX's own area rule marked, with the filter that marked them."""
    status = directory / "status.parquet"
    return ({} if not status.exists() else
            pd.read_parquet(status).query("sqx_failed").set_index("strategy")["sqx_filter"]
            .to_dict())


def one(directory: Path, cfg: dict, strategy: str) -> dict[str, Any]:
    """One mother of the export alone, the same result the whole export gives it.

    Args:
        directory: The export's `wfm/` folder.
        cfg: What config.load() returned.
        strategy: Its name as the export spells it.

    Returns:
        The contract dict plus `facts`, its identity resolved, and `draws` (the report pops it).
    """
    started = time.time()
    result = reading.read(directory, cfg, strategy)
    return member(strategy, result, cfg, started, failures(directory).get(strategy),
                  output.identify(directory, [strategy]).get(strategy))


class Population(TypedDict):
    """The export judged: the population's result, each mother's, the table, cells and draws."""

    population: dict[str, Any]
    members: list[dict[str, Any]]
    table: pd.DataFrame
    cells: pd.DataFrame
    draws: list[Any]


def run(directory: Path, cfg: dict) -> Population:
    """The whole export, and each mother.

    Args:
        directory: The export's `wfm/` folder.
        cfg: What config.load() returned.

    Returns:
        {"population", "members", "table", "cells", "draws"}: the export's result, one result
        per mother, the verdict table with identity, each cell's excess per segment, and the
        mothers' nulls as `core.study.draws` rows.
    """
    started = time.time()
    result = reading.read(directory, cfg)
    names = list(result["verdicts"])
    ident, failed = output.identify(directory, names), failures(directory)
    members = [member(s, result, cfg, started, failed.get(s), ident.get(s)) for s in names]
    kept = [d for m in members for d in m.pop("draws")]
    table = pd.DataFrame([{"strategy": m["strategy"], "identity": ident.get(m["strategy"]),
                           **m["summary"]} for m in members])
    table = cast(pd.DataFrame, table[["strategy", "identity", "verdict"]
                  + [c for c in table.columns if c not in ("strategy", "identity", "verdict")]])
    counts = cast(pd.Series, table["verdict"]).value_counts()
    cells = pd.concat([result["measured"][s]["segments"].rename_axis("cell").reset_index()
                       .assign(strategy=s) for s in names], ignore_index=True)
    shown = table.drop(columns=["identity", "why", "modo_real"]).rename(columns={
        "strategy": "estrategia", "verdict": "estado"})
    population = envelope.envelope(
        MODULE, None, None, cfg, started,
        [envelope.tab("verdicts", "Estado por estrategia", [
            blocks.table("Cada madre en oos2", shown,
                         "l1_*: la mediana de las celdas del exceso neto por año y sus dos "
                         "colas en el nulo. l2_*: reoptimizar menos la madre fija. El área de "
                         "SQX va corregida y sólo se anota."),
            *[{**tabs.heat(result["measured"][s]["per_year"], result["measured"][s]["centre"]),
               "select": {"estrategia": s}} for s in names]],
            selectors=[{"key": "estrategia", "label": "Estrategia", "options": names,
                        "default": names[0]}],
            note=f"Juzgado en modo «{cfg['modo_real']}». Los costes de oos2 se han cobrado "
                 f"sobre un export corrido a los de {cfg['recharge']['charged']}.")],
        blocks.verdict(f"{int(cast(int, counts.get(call.PASA, 0)))} de {len(table)} pasan",
                       "pass" if counts.get(call.PASA, 0) else "watch",
                       "; ".join(f"{k} {v}" for k, v in counts.items()) + "."),
        [], GLOSSARY)
    return {"population": population, "members": members, "table": table, "cells": cells,
            "draws": kept}
