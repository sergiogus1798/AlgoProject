"""The cloud's readings as the contract's tabs: C1 first, then A1, then A2 and A3."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.optimisation.cloud import heatmaps
from studies.optimisation.cloud.verdict import call

STATE = {"sin_dato": "info", "spike": "watch", "plateau": "pass", "middling": "info", "smooth": "pass",
         "rough": "watch", "off_centre": "watch", "persistent": "pass", "reshuffled": "watch",
         "carried": "watch", "broad": "pass", "drift_high": "watch", "drift_low": "pass"}
GLOSSARY = [
    {"term": "Rango (q)", "text": "El rango del punto elegido entre sus vecinos o en toda la nube."},
    {"term": "Compañía (π de δ)", "text": "Qué parte de los vecinos queda a menos de δ del punto elegido: "
     "su compañía."},
    {"term": "Valor encogido (M_shrunk)", "text": "El valor del punto elegido encogido hacia su vecindad: el "
     "número que se lleva aguas abajo."},
    {"term": "Índice de Sobol total", "text": "Qué parte de la varianza pasa por un parámetro, él solo "
     "o en interacción; muy por encima del de primer orden es lógica afinada."},
    {"term": "Clones rentables (f_y)", "text": "En cada periodo, qué parte de los clones gana dinero."}]


LABELS = {"sin_dato": "Sin dato", "spike": "Pico", "plateau": "Meseta", "middling": "Sin destacar",
          "smooth": "Superficie suave", "rough": "Superficie rugosa",
          "off_centre": "Óptimo descentrado", "persistent": "Orden persistente",
          "reshuffled": "Orden que se rebaraja", "carried": "Sostenida por periodos",
          "broad": "Gana en casi todos", "drift_high": "Deriva alta", "drift_low": "Deriva baja"}


def why_empty(found: dict) -> dict[str, str]:
    """Why A1 and A3 can have no data, in the numbers of this cloud (feedback 15, 2026-10-04)."""
    near, k = found["reading"]["near"]["n"], len(found["live"])
    need = 1 + 2 * k + k * (k - 1) // 2
    where = (f"Su vecindad son las variantes a {{r}} pasos de nivel o menos en cada uno de los {k} "
             f"parámetros a la vez; hay {near}, y la variante más cercana está a "
             f"{found['nearest']} pasos. No es un fallo del cálculo: con tantos parámetros ninguna "
             f"variante de la nube cae tan cerca de la elegida en todos a la vez (el grupo denso "
             f"del diseño se centra en la meseta del SPP, no en el punto elegido).")
    return {"point": "A1 compara el punto elegido con sus vecinos (su rango q y su compañía π). "
                     + where,
            "surface": f"A3 ajusta una superficie cuadrática a la vecindad y mide su rugosidad; "
                       f"con {k} parámetros necesita al menos {need} variantes en ella "
                       f"(1 + 2·{k} + {k}·{k - 1}/2) y hay {near}. " + where}


def readings(keys: list[str], found: dict, rule: str) -> list[dict]:
    """Each call as its own verdict block; `Sin dato` says why in this cloud's own numbers."""
    text = lambda k: why_empty(found)[rule].format(r=found["radius"]) if k == "sin_dato" \
        else call.MEANS[k]
    return [blocks.verdict(LABELS[k], STATE[k], text(k)) for k in keys]


DESCRIPTION = (
    "La nube de parámetros: cientos de clones del punto elegido, cada uno con sus parámetros "
    "movidos un poco dentro de un rango. El objetivo es diagnosticar, nunca elegir un clon "
    "mejor — clonar es en sí mismo una búsqueda, y quedarse con el que mejor puntúa sería "
    "sobreajustar de nuevo. Cuatro preguntas: ¿el punto elegido está en un pico o en una "
    "meseta?, ¿quién mueve el resultado?, y si la meseta entera predice mejor que el punto "
    "único solo.")


def tabs(found: dict, calls: dict) -> list[dict]:
    """The tabs, C1 first (feedback §8.1, 2026-09-30)."""
    r = found["reading"]
    point = pd.DataFrame({k: r[k] for k in ("near", "cloud")}).T
    point.index = ["Vecindad del punto", "Nube entera"]
    point = point.reset_index()
    point.columns = ["Dónde", "Variantes", "Rango q", f"Compañía π (δ = {r['delta'] * 100:g} %)",
                     "Valor encogido"]
    sobol = pd.DataFrame({"Parámetro": [n[6:] for n in found["live"]],
                          "Primer orden": found["indices"]["first"],
                          "Total": found["indices"]["total"]}
                         ).sort_values("Total", ascending=False)
    curve, model = found["curvature"], found["local"]
    blend = found["blend"]
    both = pd.DataFrame({"Punto único": blend["single"], "Mezcla": blend["blended"]}).T
    both.columns = ["Net Profit", "Sharpe", "Drawdown máximo"]
    both = both.rename_axis("").reset_index()
    alone = r["near"]["n"] < 2     # a histogram of one variant says nothing: draw the whole cloud
    where = blocks.distribution(
        "¿Dónde está el punto elegido?", "",
        found["values"] if alone else found["values"][found["near_mask"]], r["original"],
        ("Sin vecindad que dibujar, se muestra la nube entera. " if alone else
         "Vecindad del punto elegido (radio de niveles configurado). ") +
        "La línea marca su propio valor. Una barra alta alrededor de la línea es una meseta; "
        "la línea sola en el extremo es un pico.")
    surface = [] if calls["surface"] == ["sin_dato"] else [blocks.table(
        "¿Hay superficie que leer?", pd.DataFrame(
            [["Suavidad (R²)", model["r2"]], ["Rugosidad residual", model["roughness"]],
             ["Desacuerdo entre vecinos (IQR)", found["roughness"]],
             ["Pendiente en el origen", curve["slope"]],
             ["Autovalores", np.array2string(curve["eigenvalues"], precision=1)]],
            columns=["", "Valor"]))]
    data = found["data"]
    maps = heatmaps.pairs(data["frame"], found["live"], found["values"],
                          found["indices"]["total"], "Ret/DD Ratio (build)")
    return [
        envelope.tab("ensemble", "C1 · La meseta entera contra el punto elegido", [
            blocks.table("Punto único contra mezcla", both,
                         f"Meseta de {len(found['pool'])} variantes, {blend['k']} con curva, "
                         f"a 1/{blend['k']} del riesgo. Diferencia de Sharpe "
                         f"{blend['gap']:+.3f}: a favor del punto único es sobreajuste medido, "
                         f"no un argumento para quedárselo.")],
            note=DESCRIPTION),
        envelope.tab("point", "A1 · Dónde está el punto elegido", [
            *readings([calls["point"]], found, "point"),
            where,
            {**blocks.table("En su vecindad y en la nube", point,
                            f"Valor original {r['original']:.3f}. El valor encogido es el número "
                            f"a llevar aguas abajo."),
             "help": [None, "Cuántas variantes hay en ese conjunto.",
                      "Rango q: dónde queda el punto elegido entre ellas, de 0 (el peor) a 1 "
                      "(el mejor).",
                      "Compañía π: qué parte de las variantes rinde a menos de δ por debajo "
                      "del punto elegido; baja es un pico.",
                      "El valor del punto encogido hacia su conjunto."]}],
            note="El rango solo no decide nada: un rango alto con compañía es una meseta, "
                 "que es la forma buena; el mismo rango solo es un pico."),
        envelope.tab("surface", "A2 y A3 · Quién mueve el resultado", [
            *readings(calls["surface"], found, "surface"),
            {"kind": "bars", "title": "Índice de Sobol total por parámetro", "unit": "",
             "reference": None, "help": "Fracción de la varianza del resultado que pasa por "
             "ese parámetro, solo o en interacción con otros (índice de Sobol total).",
             "items": [{"label": p, "value": float(t), "error": None, "state": "info"}
                       for p, t in zip(sobol["Parámetro"], sobol["Total"])]},
            {**blocks.table("Índices de Sobol", sobol),
             "help": [None, "Primer orden: el parámetro solo.",
                      "Total: solo más sus interacciones con los demás."]},
            *surface, *maps],
            note="A2 (Sobol) ajusta una superficie a toda la nube y sí tiene dato: está en las "
                 "barras de abajo. A3 (¿hay superficie que leer?) la ajusta solo a la vecindad "
                 "del punto elegido. Un índice total muy por encima del de primer orden es "
                 "interacción: la forma de la lógica afinada. Los mapas de calor cruzan los "
                 f"{heatmaps.TOP} parámetros de mayor índice de Sobol total, de dos en dos.")]
