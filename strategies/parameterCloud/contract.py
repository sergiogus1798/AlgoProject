"""The cloud's four readings as the contract's tabs: A1, A2 and A3, B2, C1."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from strategies.parameterCloud.verdict import call

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


def tabs(found: dict, calls: dict) -> list[dict]:
    """The four tabs, in the order the argument is made."""
    r = found["reading"]
    point = pd.DataFrame({k: r[k] for k in ("near", "cloud")}).T.reset_index()
    point.columns = ["dónde", "n", "q (rango)", f"π ({r['delta']:.0%})", "M_shrunk"]
    sobol = pd.DataFrame({"parámetro": [n[6:] for n in found["live"]],
                          "S": found["indices"]["first"], "S_total": found["indices"]["total"]}
                         ).sort_values("S_total", ascending=False)
    curve, model = found["curvature"], found["local"]
    periods = (found["table"].join(found["rho"].rename("rho_siguiente"))
               .join(found["drift"].rename("deriva")).reset_index())
    blend = found["blend"]
    both = pd.DataFrame({"punto único": blend["single"], "mezcla": blend["blended"]}).T
    return [
        envelope.tab("point", "A1 · Dónde está el punto elegido", [
            *readings([calls["point"]]),
            blocks.table("En su vecindad y en la nube", point,
                         f"Valor original {r['original']:.3f}. M_shrunk es el número a llevar "
                         f"aguas abajo.")],
            note="El rango solo no decide nada: un rango alto con compañía es una meseta, "
                 "que es la forma buena; el mismo rango solo es un pico."),
        envelope.tab("surface", "A2 y A3 · Quién mueve el resultado", [
            *readings(calls["surface"]),
            {"kind": "bars", "title": "Sobol total por parámetro", "unit": "",
             "reference": None,
             "items": [{"label": p, "value": float(t), "error": None, "state": "info"}
                       for p, t in zip(sobol["parámetro"], sobol["S_total"])]},
            blocks.table("Índices de Sobol", sobol),
            blocks.table("¿Hay superficie que leer?", pd.DataFrame(
                [["suavidad r²", model["r2"]], ["rugosidad residual", model["roughness"]],
                 ["desacuerdo entre vecinos (IQR)", found["roughness"]],
                 ["pendiente en el origen", curve["slope"]],
                 ["autovalores", np.array2string(curve["eigenvalues"], precision=1)]],
                columns=["", "valor"]))],
            note="Un índice total muy por encima del de primer orden es interacción: la forma "
                 "de la lógica afinada."),
        envelope.tab("stability", "B2 · La superficie, periodo a periodo", [
            *readings(calls["temporal"]),
            {"kind": "lines", "title": "Parte de los clones que gana, por periodo",
             "unit": "", "x": [str(p) for p in periods.iloc[:, 0]],
             "series": [{"label": "f_y", "values": list(periods["f_y"]), "role": "real"}]},
            blocks.table("Periodo a periodo", periods,
                         f"Mediana rho {np.median(found['rho']):+.3f} · mediana deriva "
                         f"{np.median(found['drift']):.3f} · peor periodo f_y "
                         f"{found['table']['f_y'].min():.3f}.")],
            note="Nivel, orden y dónde estuvo la región buena fallan por separado: una familia "
                 "puede ganar en todos los periodos con su orden interno hecho ruido."),
        envelope.tab("ensemble", "C1 · La meseta entera contra el punto elegido", [
            blocks.table("Punto único contra mezcla", both.reset_index(),
                         f"Meseta de {len(found['pool'])} variantes, {blend['k']} con curva, "
                         f"a 1/{blend['k']} del riesgo. Diferencia de Sharpe "
                         f"{blend['gap']:+.3f}: a favor del punto único es sobreajuste medido, "
                         f"no un argumento para quedárselo.")])]
