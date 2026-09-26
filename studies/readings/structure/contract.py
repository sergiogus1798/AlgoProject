"""The three readings as the contract's tabs: each condition's ΔM, the inversion, the controls."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.readings.structure import reading

LEG = "tramo"


def _selector(legs: list[str]) -> list[dict]:
    """The one drop-down every tab carries: which leg is on screen."""
    return [{"key": LEG, "label": "Tramo", "options": legs, "default": legs[0]}]


def _tag(block: dict, leg: str, **more: str) -> dict:
    """A block marked as belonging to one leg (and whatever other selector it names)."""
    return block | {"select": {LEG: leg, **more}}


def _word(label: str, subject: str = "") -> dict:
    """One label with its state and its meaning, as a verdict block, prefixed by what it judges."""
    state, meaning = reading.MEANS[label]
    return blocks.verdict(f"{subject} — {label}" if subject else label, state, meaning)


def conditions_tab(found: dict) -> dict:
    """What each entry condition adds, per trade, on each leg."""
    legs, content = list(found), []
    for leg, f in found.items():
        rows = []
        for a in f["ablations"]:
            e, s = a["null"]["expectancy"], a["null"]["sharpe"]
            rows.append([a["block"], a["label"], a["mother"]["n"], a["ablation"]["n"],
                         a["mother"]["expectancy"], a["ablation"]["expectancy"],
                         a["delta"]["expectancy"], e["p"], a["mother"]["sharpe"],
                         a["ablation"]["sharpe"], a["delta"]["sharpe"], s["p"], a["twins"]])
        content.append(_tag(blocks.table(
            "ΔM por condición", pd.DataFrame(rows, columns=[
                "condición quitada", "lectura", "ops madre", "ops sin ella", "esperanza madre",
                "esperanza sin ella", "ΔE", "p ΔE", "Sharpe madre", "Sharpe sin ella", "ΔSharpe",
                "p ΔSharpe", "entradas gemelas"]),
            "ΔE y ΔSharpe son madre menos ablación, por operación: positivo es lo que la "
            "condición añade. 'Entradas gemelas' es la parte de las entradas de la madre que "
            "la ablación también tomó; baja cuando la estrategia sólo lleva una posición."), leg))
        content.append(_tag({"kind": "bars", "title": "ΔE por condición", "unit": "USD",
                             "items": [{"label": a["block"], "value": a["delta"]["expectancy"],
                                        "error": None, "state": reading.MEANS[a["label"]][0]}
                                       for a in f["ablations"]], "reference": 0.0}, leg))
        for a in f["ablations"]:
            content.append(_tag(_word(a["label"], a["block"]), leg))
            e = a["null"]["expectancy"]
            if e["draws"] is not None:
                content.append(_tag(blocks.distribution(
                    f"Sin {a['block']}: {a['mother']['n']} operaciones al azar", "USD",
                    e["draws"], e["observed"],
                    "Esperanza por operación de recortes al azar de la estrategia sin la "
                    "condición; la línea es la madre.", e["p"]), leg))
    return envelope.tab("conditions", "1 · Qué aporta cada condición", content, _selector(legs),
                        "Una ablación por condición de entrada. Se lee por operación: quitar un "
                        "filtro da más operaciones, y el beneficio total siempre favorece a la "
                        "que opera más.")


def inversion_tab(found: dict) -> dict:
    """The same entries the other way round: does the edge live in the direction?"""
    legs, content = list(found), []
    for leg, f in found.items():
        i = f["inversion"]
        content.append(_tag(_word(i["label"]), leg))
        content.append(_tag(blocks.table("La madre y su inversión", pd.DataFrame([
            ["operaciones", i["n_mother"], i["n_inverted"]],
            ["esperanza neta por operación", i["exp_mother"], i["exp_inverted"]],
            ["neto", i["net_mother"], i["net_inverted"]],
            ["bruto a precio de ejecución", i["gross_mother"], i["gross_inverted"]],
            ["a precio medio", i["mid"], -i["mid"]],
            ["swap y comisión", -i["carry_mother"], -i["carry_inverted"]]],
            columns=["", "madre", "invertida"]),
            f"Emparejadas {i['paired']:.1%} (mismo instante, mismo tamaño, lado contrario); "
            f"correlación del bruto por operación {i['corr']:+.4f}. Spread pagado por cada "
            f"lado: {i['spread']:,.0f} USD."), leg))
    return envelope.tab("inversion", "2 · La misma entrada, al revés", content, _selector(legs),
                        "Mismos instantes de entrada, dirección contraria. Sin stops, target "
                        "ni trailing es un espejo exacto a precio medio; dejará de serlo en "
                        "cuanto la estrategia lleve stops (paso 24).")


def controls_tab(found: dict) -> dict:
    """The three checks without which the other two tabs are decoration (encargo 12 §3)."""
    legs, content = list(found), []
    for leg, f in found.items():
        differs = [a for a in f["ablations"] if a["ablation"]["n"] != a["mother"]["n"]]
        kept = f["identity_retained"] and all(a["retained"] for a in f["ablations"]) \
            and f["inversion"]["retained"]
        matched = [r for r in f["identity"] if r["match"]]
        content.append(_tag(blocks.verdict(
            "controles", "pass" if kept and differs and matched else "watch",
            "Los tres controles del encargo 12 §3 en este tramo.", parts=[
                {"label": "SQX conservó cada edición", "state": "pass" if kept else "fail",
                 "value": None, "note": "sqx.structural.keep, leído del fichero reteseado"},
                {"label": "alguna ablación cambia el nº de operaciones",
                 "state": "pass" if differs else "fail", "value": float(len(differs)),
                 "note": "si ninguna cambia, SQX pudo ignorar la edición (OPEN.md §9)"},
                {"label": "la madre reconstruida reproduce un resultado guardado",
                 "state": "pass" if matched else "none", "value": None,
                 "note": "sólo donde el fichero de la madre guarda ese tramo"}]), leg))
        content.append(_tag(blocks.table(
            "Madre reconstruida contra lo que guardaba su fichero",
            pd.DataFrame(f["identity"], columns=["sample", "stored_trades", "stored_net",
                                                 "trades", "net", "match"])
            .rename(columns={"sample": "muestra guardada", "stored_trades": "ops guardadas",
                             "stored_net": "neto guardado", "trades": "ops reconstruida",
                             "net": "neto reconstruida", "match": "igual"})), leg))
    return envelope.tab("controls", "3 · Controles", content, _selector(legs),
                        "Sin estos tres no hay lectura: que SQX corrió lo que se fabricó, que "
                        "una ablación opera distinto y que la madre reconstruida es la madre.")
