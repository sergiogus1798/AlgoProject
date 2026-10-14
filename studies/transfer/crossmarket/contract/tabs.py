"""The tabs of the travel test: what `travel.run` measured, as the contract's blocks."""

from typing import Any, cast

import pandas as pd

from core.study import blocks, identity
from core.study import result as envelope
from core.symbols import alias

# What a strategy's number is, one sentence each, in the order the proposal runs its tests
# (encargo 46, §1). The same words are the window's help on the verdict.csv columns.
MEASURES = [
    ("markets_valid", "Mercados válidos", "Mercados de la lista que pasan los controles previos."),
    ("fixed_distance", "P1 · Distancias fijas",
     "Parámetros en puntos o pips (stop, objetivo, trailing): no viajan entre mercados."),
    ("freq_off", "P2 · Mercados con otra frecuencia",
     "Mercados donde opera con una frecuencia muy distinta a la de su mercado principal."),
    ("z_conj", "P3 · z conjunta",
     "Cuántas desviaciones gana por encima del azar sumando todos los mercados. Anotada, no juzga."),
    ("z_conj_v0v2", "P3 · z en V0 + V2",
     "La misma z sumando sólo los años anteriores al build y los de oos1 del principal (V1, "
     "donde se ajustó, fuera). Es la que juzga el P3."),
    ("z_conj_v2", "z en los años de oos1",
     "La misma z, sólo en los años que el generador no vio. Anotada, no juzga."),
    ("z_minus_market", "P5 · z quitando un mercado",
     "La peor z que sale al quitar, uno a uno, cada mercado."),
    ("p_breadth", "P6 · p de amplitud",
     "Probabilidad de que tantos mercados salgan a favor sólo por suerte."),
    ("tau_half", "P7 · rendimiento en la mitad",
     "Ventaja por operación que mantiene en la mitad de los mercados, frente a casa."),
    ("worse", "P8 · mercados en contra", "Mercados donde va claramente peor que el azar."),
    ("z_beta", "P9 · z de la pendiente",
     "Cuántas desviaciones se aparta del azar la tendencia de su ventaja año a año."),
    ("e_end", "P9 · ventaja al final", "Ventaja por operación estimada para el último año."),
    ("net_t_pooled", "t conjunta sobre el neto", "Anotada, no juzga: t del neto de SQX sumado."),
    ("trades", "Operaciones", "Operaciones en los mercados válidos."),
]
GLOSSARY = [
    {"term": "R", "text": "Una unidad de riesgo: lo que arriesga una operación según la doctrina de "
                         "tamaño de la casa. Todos los mercados se suman en R."},
    {"term": "z conjunta", "text": "Cuántas desviaciones típicas del azar queda el resultado real. "
                                   "El azar son las mismas entradas movidas semanas enteras, "
                                   "igual en todos los mercados."},
    {"term": "V0, V1, V2", "text": "Ventanas: V0 lo anterior al build del principal, V1 su build, "
                                   "V2 su oos1."},
]


def mercado(feed: str) -> str:
    """A feed's name as the window prints it."""
    return alias(feed)


def strategy_tabs(row: pd.Series, markets: pd.DataFrame, d_y: list[dict], cfg: dict) -> list[dict]:
    """One strategy's three tabs: the numbers of the tests, each market, the year-by-year edge."""
    look = markets.assign(market=markets["market"].map(mercado))
    seen = look[look["valid"]]
    summary = pd.DataFrame([[label, row[col], text] for col, label, text in MEASURES],
                           columns=pd.Index(["Prueba", "Valor", "Qué mide"]))
    counted = look.drop(columns=["strategy", "identity"], errors="ignore").rename(columns={
        "market": "Mercado", "z": "z", "p": "p", "e": "Ventaja (R/op.)", "trades": "Operaciones",
        "z_freq": "z de frecuencia", "valid": "Válido", "invalid_reason": "Motivo no válido"})
    years = pd.DataFrame(
        [[f"{d['years'][0]}–{d['years'][-1]}" if len(d["years"]) > 1 else str(d["years"][0]),
          d["trades"], d["d"]] for d in d_y],
        columns=pd.Index(["Años", "Operaciones", "Ventaja frente al azar (R/op.)"]))
    bars = {"kind": "bars", "title": "z de cada mercado frente al azar", "unit": "z",
            "reference": cfg["travel"]["worse_z"],
            "items": [{"label": r.market, "value": r.z, "error": None,
                       "state": "fail" if r.z <= cfg["travel"]["worse_z"] else "info"}
                      for r in cast(Any, seen.itertuples()) if r.z == r.z]}
    return [
        envelope.tab("resumen", "Resumen", [blocks.table("Lo medido, prueba a prueba", summary,
                     "Sin dato: celda vacía, nunca 0. El juez de criteria.yaml decide.")]),
        envelope.tab("mercados", "Mercados", [
            bars, blocks.table("Cada mercado de la lista", counted,
                               "z y p frente al azar conjunto; la ventaja es por operación, en R; "
                               "la z de frecuencia compara con el mercado principal.")]),
        envelope.tab("anos", "Año a año", [blocks.table(
            "Ventaja por operación frente al azar, por año", years,
            "La serie de la que sale la pendiente de P9.")])]


def warnings(markets: pd.DataFrame, ident: str | None) -> list[dict]:
    """What to read first: the markets left out of the test, and a strategy with no identity."""
    out = [{"code": f"{mercado(r.market)}:{r.invalid_reason}", "state": "watch",
            "text": f"{mercado(r.market)} queda fuera de la prueba ({r.invalid_reason})."}
           for r in cast(Any, markets.itertuples()) if not r.valid]
    return out + identity.warning(ident)
