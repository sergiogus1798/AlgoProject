"""Families C, D and E as tabs: execution, regime, and whether the edge could be zero."""

import pandas as pd

from core.study import blocks, result as envelope
from strategies.monteCarlo.contract import headline, shapes
from strategies.monteCarlo.contract.words import MODELS_ES
from strategies.monteCarlo.model import regime, stress
from strategies.monteCarlo.verdict import gates


def family_c(result: dict, verdict: dict, cfg: dict) -> dict:
    """Execution luck: the same trades filled worse, charged more, or not taken at all."""
    fired = {f["test"] for f in gates.check(result, cfg) if f["family"] == "C"}
    rows = pd.DataFrame([[stress.TITLES[k], MODELS_ES[k], v["median_net"], v["keep"],
                          v["net_5"], v["pf_5"], "falla" if k in fired else "pasa"]
                         for k, v in result["C"].items()],
                        columns=["prueba", "qué hace", "beneficio mediano (USD)", "queda",
                                 "beneficio p5 (USD)", "PF p5", ""])
    figs = []
    for k, v in result["C"].items():
        figs.append(shapes.distribution(v["shapes"]["net"], v["table"]["net"], "net",
                                        f"Beneficio neto — {stress.TITLES[k]}"))
        figs += shapes.overlay(result["degrade"][f"C.{k}"], stress.TITLES[k])
    return envelope.tab(
        "familyC", "Familia C — suerte de ejecución",
        [headline.fired(verdict, "C"), blocks.table("Las cuatro pruebas", rows), *figs],
        note="Las mismas operaciones peor ejecutadas. Las cuatro tienen que pasar: no se "
             "promedian, y se ejecutan siempre aunque alguna ya haya fallado.")


def _bars(title: str, labels: list[str], values: list[float], note: str) -> dict:
    """Bars in USD, green above zero and red below."""
    return {"kind": "bars", "title": title, "unit": "USD", "reference": 0.0, "note": note,
            "items": [{"label": str(k), "value": v, "error": None,
                       "state": "pass" if v == v and v > 0 else "fail"}
                      for k, v in zip(labels, values)]}


def family_d(result: dict, verdict: dict, cfg: dict) -> dict:
    """Regime luck: where in the calendar and in market volatility the edge lived."""
    d, months = result["D"], cfg["family_d"]["window_months"]
    over, segs, rg = d["overlapping"], d["nonoverlapping"], d["regime"]
    buckets = rg["buckets"]
    series = rg["series"]
    out = [headline.fired(verdict, "D"),
           _bars(f"Ventanas móviles de {months} meses — beneficio percentil 5",
                 [w["start"][:7] for w in over], [w["net_5"] for w in over],
                 f"{gates.passing(over):.0%} de las ventanas en positivo."),
           blocks.table("Bloques que no se solapan", pd.DataFrame(
               [[w["start"], w["n"], w["median_net"], w["net_5"], w["pf_5"]] for w in segs],
               columns=["desde", "operaciones", "mediana (USD)", "percentil 5 (USD)",
                        "PF p5"]),
               "Las ventanas solapadas suavizan; estos bloques no comparten ni una operación, "
               "así que un periodo malo de verdad aparece aquí.")]
    out += [shapes.distribution(w["shape"], None, "net", f"Beneficio remuestreado — bloque "
                                f"desde {w['start']}") for w in segs if w["shape"] is not None]
    curve = d["equity"]["curve"]
    out.append({"kind": "lines", "title": "Curva de equity", "unit": "USD",
                "x": list(range(len(curve))),
                "series": [{"label": "equity real", "values": curve, "role": "real"}],
                "note": "Los bloques de la tabla empiezan en las operaciones "
                        + ", ".join(str(m) for m in d["equity"]["marks"]) + "."})
    out += [{"kind": "lines", "title": title, "unit": unit, "x": series["dates"],
             "series": [{"label": title, "values": series[key], "role": "real"}],
             "note": f"{rg['model']}; terciles cortados en {rg['edges'][0]:,.2f} y "
                     f"{rg['edges'][1]:,.2f}, cobertura {rg['coverage']:.1%}. {rg['note']}"}
            for key, title, unit in (("price", "Precio diario", ""),
                                     ("vol", "Volatilidad diaria", ""))]
    out.append(_bars("Beneficio mediano remuestreado por tercil de volatilidad",
                     list(regime.BUCKETS), [buckets[b]["median_net"] for b in regime.BUCKETS],
                     f"El {rg['concentration']:.0%} del beneficio sale de un tercil."))
    out.append(blocks.table("Por tercil", pd.DataFrame(
        [[b, v["n"], v["net"], v["median_net"], v["net_5"], v["pf_5"]]
         for b, v in buckets.items()],
        columns=["tercil", "operaciones", "beneficio real (USD)", "mediana (USD)",
                 "percentil 5 (USD)", "PF p5"])))
    out += [shapes.distribution(buckets[b]["shape"], None, "net",
                                f"Beneficio remuestreado — tercil {b}")
            for b in regime.BUCKETS]
    out.append(blocks.table("El peor camino posible", pd.DataFrame(
        [[f"{q * 100:.0f}%", v["dd_pct"] * 100, v["net"], v["segments"]]
         for q, v in d["stitch"].items()],
        columns=["percentil por bloque", "drawdown (%)", "beneficio neto (USD)",
                 "bloques cosidos"]),
        f"Un mal tramo de cada bloque de {months} meses cosido en uno, a varias severidades. "
        f"No es un veto. Drawdown real {result['observed']['dd_pct']:.1%}; percentil 95 "
        f"reordenando {result['A']['dd_pct_95']:.1%}."))
    month = d["calendar"]["month"]
    out.append(_bars("Beneficio por mes del año", [str(k) for k in month],
                     list(month.values()), "Sólo diagnóstico: con doce meses, el mejor de un "
                                           "reparto al azar ya parece notable."))
    out += shapes.overlay(result["degrade"]["D"], "Beneficio remuestreado")
    return envelope.tab("familyD", "Familia D — suerte de régimen", out,
                        note="Las familias A a C dan por hecho que el edge es el mismo "
                             "siempre. Ésta mira dónde vivió, en el calendario y en la "
                             "volatilidad del mercado.")


def family_e(result: dict, verdict: dict, cfg: dict) -> dict:
    """Significance: could the true edge be zero, given N and the shape of the returns."""
    e, f = result["E"], cfg["family_e"]
    rows = [["PSR", e["psr"]], ["Objetivo", f["psr_target"]], ["Veto", f["psr_gate"]],
            ["Sharpe por operación", e["sharpe"]], ["Asimetría", e["skew"]],
            ["Curtosis", e["kurtosis"]], ["Operaciones", e["n"]],
            ["P(Sharpe>0) remuestreando", e["bootstrap"]],
            ["Diferencia analítica vs remuestreo", e["gap"]]]
    return envelope.tab(
        "familyE", "Familia E — significación",
        [headline.fired(verdict, "E"),
         blocks.table("PSR y su comprobación cruzada",
                      pd.DataFrame(rows, columns=["qué", "valor"]),
                      "Si las dos últimas filas coinciden, la conclusión no depende de la "
                      "aproximación normal. No hay Deflated Sharpe: haría falta saber cuántas "
                      "estrategias se probaron, y ese número no existe en esta fase.")],
        note="La PSR es la probabilidad de que el Sharpe real supere cero, contando cuántas "
             "operaciones hay y la forma de su distribución: castiga la concentración que el "
             "Sharpe solo no ve.")
