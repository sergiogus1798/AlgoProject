"""The pooled profile as the study contract: what the window and the page draw."""

from typing import Any
import pandas as pd

from core.study import blocks, result
from studies.research.pooledProfile.many import Judged

TESTS = ["group", "timeframe", "direction", "family", "measure", "assets", "stat", "p", "q",
         "mean_excess", "tau", "i2"]
ASSETS = ["group", "timeframe", "direction", "measure", "symbol", "z", "p", "multiple", "excess",
          "se", "shrunk_excess", "shrunk_multiple", "trades_per_year", "significant_alone",
          "strict"]
GLOSSARY = [
    {"term": "stat", "text": "La suma de las z de los activos del grupo entre la raíz de "
                             "cuántos son, comparada con la misma suma en la nula conjunta."},
    {"term": "q", "text": "La p del grupo corregida con Benjamini-Hochberg sobre todas las "
                          "pruebas de grupo."},
    {"term": "mean_excess", "text": "Media del grupo (efectos aleatorios) del exceso por "
                                    "operación sobre la nula, en costes de ida y vuelta."},
    {"term": "tau", "text": "Cuánto difieren de verdad los activos entre sí, en las mismas "
                            "unidades; 0: el grupo es homogéneo."},
    {"term": "shrunk_multiple", "text": "El múltiplo del activo encogido hacia la media del "
                                        "grupo según lo ruidoso que es; comparable con "
                                        "multiple, el suyo en bruto."},
    {"term": "strict", "text": "El efecto encogido paga 2 costes, es estable por años y da "
                               "las operaciones mínimas al año."},
    {"term": "new", "text": "La celda-familia no está hoy en el tablero."}]


def build(judged: Judged, cfg: dict, started: float) -> dict[str, Any]:
    """The contract dict of the study.

    Args:
        judged: What many.run() returned.
        cfg: The parsed config.
        started: time.time() when the run began.

    Returns:
        A validated result; its summary carries the counts the decision reads.
    """
    tests, assets, cells = judged["tests"], judged["assets"], judged["board"]
    fake = judged["placebo"]
    named = pd.DataFrame(tests[tests["significant"]]).sort_values("q")
    shown = assets.merge(named[["group", "timeframe", "direction", "measure"]])
    counts = {"group_tests": len(tests), "named": len(named), "cells": len(cells),
              "cells_strict": int(cells["strict"].sum()), "cells_new": int(cells["new"].sum()),
              "cells_new_strict": int((cells["new"] & cells["strict"]).sum()),
              "cells_alone": int(cells["alone"].sum())}
    tabs = [
        result.tab("grupos", "Grupos que pasan", [blocks.table(
            "Pruebas de grupo significativas", pd.DataFrame(named[TESTS]),
            f"{len(named)} de {len(tests)} pruebas de grupo, corregidas juntas al "
            f"{cfg['judge']['alpha']:.0%}.", 3)]),
        result.tab("activos", "Cada activo, en bruto y encogido", [blocks.table(
            "Los activos de los grupos que pasan", pd.DataFrame(shown[ASSETS]),
            "multiple es el efecto del activo solo; shrunk_multiple, encogido hacia su grupo.",
            3)]),
        result.tab("tablero", "Celdas que entrarían al tablero", [blocks.table(
            "Celdas-familia de los grupos que pasan", cells,
            f"{counts['cells']} por la vía amplia, {counts['cells_strict']} por la estricta; "
            f"nuevas: {counts['cells_new']} y {counts['cells_new_strict']}. Este estudio sólo "
            "cuenta: la compuerta del tablero no cambia.", 3)]),
        result.tab("falsas", "Falsas alarmas", [blocks.table(
            "Sorteos de la nula juzgados como si fueran la serie real",
            pd.DataFrame([fake]), "any_named: parte de los mundos sin nada en los que el "
            "procedimiento nombra algún grupo.", 3)])]
    return result.envelope("studies.research.pooledProfile", None, None, cfg, started, tabs,
                           glossary=GLOSSARY, summary={**counts, **fake})
