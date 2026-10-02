"""The cloud's readings as the contract's tabs: C1 first, then A1, then A2 and A3."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.optimisation.cloud.verdict import call

STATE = {"spike": "watch", "plateau": "pass", "middling": "info", "smooth": "pass",
         "rough": "watch", "off_centre": "watch", "persistent": "pass", "reshuffled": "watch",
         "carried": "watch", "broad": "pass", "drift_high": "watch", "drift_low": "pass"}
GLOSSARY = [
    {"term": "q", "text": "El rango del punto elegido entre sus vecinos o en toda la nube."},
    {"term": "π(δ)", "text": "Qué parte de los vecinos queda a menos de δ del punto elegido: "
     "su compañía."},
    {"term": "M_shrunk", "text": "El valor del punto elegido encogido hacia su vecindad: el "
     "número que se lleva aguas abajo."},
    {"term": "Sobol total", "text": "Qué parte de la varianza pasa por un parámetro, él solo "
     "o en interacción; muy por encima del de primer orden es lógica afinada."},
    {"term": "f_y", "text": "En cada periodo, qué parte de los clones gana dinero."}]


def readings(keys: list[str]) -> list[dict]:
    """Each call as its own verdict block."""
    return [blocks.verdict(k, STATE[k], call.MEANS[k]) for k in keys]


DESCRIPTION = (
    "La nube de parámetros: dos mil clones del punto elegido, cada uno con sus parámetros "
    "movidos un poco dentro de un rango. El objetivo es diagnosticar, nunca elegir un clon "
    "mejor — clonar es en sí mismo una búsqueda, y quedarse con el que mejor puntúa sería "
    "sobreajustar de nuevo. Cuatro preguntas: ¿el punto elegido está en un pico o en una "
    "meseta?, ¿quién mueve el resultado?, y si la meseta entera predice mejor que el punto "
    "único solo.")


def tabs(found: dict, calls: dict) -> list[dict]:
    """The tabs, C1 first (feedback §8.1, 2026-09-30)."""
    r = found["reading"]
    point = pd.DataFrame({k: r[k] for k in ("near", "cloud")}).T.reset_index()
    point.columns = ["dónde", "n", "q (rango)", f"π ({r['delta']:.0%})", "M_shrunk"]
    sobol = pd.DataFrame({"parámetro": [n[6:] for n in found["live"]],
                          "S": found["indices"]["first"], "S_total": found["indices"]["total"]}
                         ).sort_values("S_total", ascending=False)
    curve, model = found["curvature"], found["local"]
    blend = found["blend"]
    both = pd.DataFrame({"punto único": blend["single"], "mezcla": blend["blended"]}).T
    where = blocks.distribution(
        "¿Dónde está el punto elegido?", "", found["values"][found["near_mask"]],
        r["original"], "Vecindad del punto elegido (radio de niveles configurado); la línea "
        "marca su propio valor. Una barra alta alrededor de la línea es una meseta; la línea "
        "sola en el extremo es un pico.")
    return [
        envelope.tab("ensemble", "C1 · La meseta entera contra el punto elegido", [
            blocks.table("Punto único contra mezcla", both.reset_index(),
                         f"Meseta de {len(found['pool'])} variantes, {blend['k']} con curva, "
                         f"a 1/{blend['k']} del riesgo. Diferencia de Sharpe "
                         f"{blend['gap']:+.3f}: a favor del punto único es sobreajuste medido, "
                         f"no un argumento para quedárselo.")],
            note=DESCRIPTION),
        envelope.tab("point", "A1 · Dónde está el punto elegido", [
            *readings([calls["point"]]),
            where,
            blocks.table("En su vecindad y en la nube", point,
                         f"Valor original {r['original']:.3f}. M_shrunk es el número a llevar "
                         f"aguas abajo.")],
            note="El rango solo no decide nada: un rango alto con compañía es una meseta, "
                 "que es la forma buena; el mismo rango solo es un pico."),
        envelope.tab("surface", "A2 y A3 · Quién mueve el resultado", [
            *readings(calls["surface"]),
            {"kind": "bars", "title": "Sobol total por parámetro", "unit": "",
             "reference": None, "help": "Fracción de la varianza del resultado que pasa por "
             "ese parámetro, solo o en interacción con otros (índice de Sobol total).",
             "items": [{"label": p, "value": float(t), "error": None, "state": "info"}
                       for p, t in zip(sobol["parámetro"], sobol["S_total"])]},
            {**blocks.table("Índices de Sobol", sobol),
             "help": [None, "Primer orden: el parámetro solo.",
                      "Total: solo más sus interacciones con los demás."]},
            blocks.table("¿Hay superficie que leer?", pd.DataFrame(
                [["suavidad r²", model["r2"]], ["rugosidad residual", model["roughness"]],
                 ["desacuerdo entre vecinos (IQR)", found["roughness"]],
                 ["pendiente en el origen", curve["slope"]],
                 ["autovalores", np.array2string(curve["eigenvalues"], precision=1)]],
                columns=["", "valor"]))],
            note="Un índice total muy por encima del de primer orden es interacción: la forma "
                 "de la lógica afinada.")]
