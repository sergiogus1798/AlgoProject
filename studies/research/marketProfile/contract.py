"""The judged map as the study contract: what the window and the page draw."""

import pandas as pd

from core.study import blocks, result

SHOWN = ["symbol", "timeframe", "direction", "family", "score", "p", "multiple", "stability",
         "trades_per_year", "lead", "significant", "pays", "stable", "frequent", "passes",
         "fragile"]
GLOSSARY = [
    {"term": "score", "text": "De 0 a 100: la media de las z de las medidas de la familia "
                              "frente a su nula, recortada entre 0 y el tope."},
    {"term": "p", "text": "La p de la medida principal de la familia, ya corregida con "
                          "Benjamini-Hochberg sobre todas las pruebas del mapa."},
    {"term": "multiple", "text": "Efecto medio bruto por operación dividido entre el coste "
                                 "de ida y vuelta del tramo build. El filtro pide 2 o más."},
    {"term": "stability", "text": "Parte de los años de build en los que el efecto tiene el "
                                  "signo bueno. Más de la mitad, o la celda es frágil."},
    {"term": "passes", "text": "Alguna medida con operaciones de la familia pasa los cuatro "
                               "filtros: significativa, paga el doble del coste, estable y "
                               "con suficientes operaciones al año."}]


def _grid(table: pd.DataFrame, direction: str) -> dict:
    """The scores of one direction as a heat map: cells in rows, families in columns."""
    part = table[table["direction"] == direction]
    wide = part.pivot_table(index=["symbol", "timeframe"], columns="family", values="score",
                            sort=False)
    return {"kind": "grid", "title": f"Puntuación por familia — {direction}",
            "rows": [f"{s} {t}" for s, t in wide.index], "cols": list(wide.columns),
            "values": wide.round(1).to_numpy().tolist(), "scale": "discrete",
            "levels": [20, 40, 60, 80], "labels": None, "select": {"direccion": direction}}


def build(judged: dict, context: pd.DataFrame, cfg: dict, started: float) -> dict:
    """The contract dict of the whole map.

    Args:
        judged: What many.run() returned.
        context: One row per cell (store.load).
        cfg: The parsed config.
        started: time.time() when the run began.

    Returns:
        A validated result: the cells that pass, the score maps, how alike the families are,
        and the context of every cell.
    """
    table, corr = judged["scores"], judged["correlation"]
    good = table[table["passes"] | table["fragile"]].sort_values("multiple", ascending=False)
    whole = corr[corr["scope"] == "ALL"].sort_values("spearman", ascending=False)
    tests = len(judged["measures"])
    tabs = [
        result.tab("pasan", "Celdas que pasan", [blocks.table(
            "Familias que pasan los cuatro filtros, o que sólo fallan el de estabilidad",
            good[SHOWN], f"{int(table['passes'].sum())} de {len(table)} celdas-familia pasan; "
            f"{int(table['fragile'].sum())} frágiles. {tests} pruebas corregidas juntas.", 4)]),
        result.tab("mapa", "Puntuaciones", [_grid(table, d) for d in ("long", "short")],
                   [{"key": "direccion", "label": "Dirección", "options": ["long", "short"],
                     "default": "long"}]),
        result.tab("familias", "¿Se separan las familias?", [blocks.table(
            "Correlación entre las puntuaciones de dos familias, sobre todas las celdas",
            whole.drop(columns="scope"), "Cerca de 1: las dos familias miden lo mismo.", 3)]),
        result.tab("contexto", "Contexto", [blocks.table(
            "Deriva, agrupamiento de la volatilidad y coste frente al ATR", context,
            "No genera propuestas: dice en qué marcos se puede operar.", 4)])]
    return result.envelope("studies.research.marketProfile", None, None, cfg, started, tabs,
                           glossary=GLOSSARY,
                           summary={"cells": int(len(table)), "passes": int(table["passes"].sum()),
                                    "fragile": int(table["fragile"].sum()), "tests": tests})
