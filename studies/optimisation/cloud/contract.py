"""The map as the contract's tabs, its warnings, and the facts the report carries."""

from typing import Any
import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.optimisation.cloud import heatmaps

NOISE = "Sin estructura distinguible del ruido"
TITLES = {"build": "Quién mueve el resultado (build)",
          "oos1": "Lectura secundaria: el mismo mapa en oos1"}
GLOSSARY = [
    {"term": "Exceso por año", "text": "Lo que la variante gana en el tramo menos lo que el "
     "mercado le habría pagado sólo por estar dentro (la deriva), en dinero de la cuenta por "
     "año. Es la misma medida del paso 14 y del WFC."},
    {"term": "R² ajustado", "text": "Qué parte de las diferencias de exceso entre variantes "
     "explica una superficie suave (cuadrática) de los parámetros, descontando lo que "
     "explicaría sola por tener muchos coeficientes. 0 es nada; 1, todo."},
    {"term": "Referencia barajada", "text": "El R² ajustado que sale de la misma superficie "
     "cuando el exceso se reparte al azar entre las variantes: lo que da el ruido puro."},
    {"term": "Índice de Sobol de primer orden", "text": "Qué parte de la variación de la "
     "superficie produce un parámetro él solo, de 0 a 1."},
    {"term": "Índice de Sobol total", "text": "Lo mismo contando además lo que el parámetro "
     "hace en combinación con los otros; muy por encima del de primer orden es interacción."}]
DESCRIPTION = (
    "El mapa de la nube: las variantes del lote, repartidas de manera uniforme por la meseta "
    "de cada parámetro vivo, y cuánto se mueve su exceso por año al mover cada parámetro. Es "
    "un diagnóstico: no tiene regla, no corta nada y no elige una variante mejor.")


def sobol(found: dict, leg: str) -> pd.DataFrame:
    """The leg's indices as a table, highest total first."""
    got = found["legs"][leg]["indices"]
    return pd.DataFrame({"Parámetro": [n[6:] for n in found["live"]], "Primer orden": got["first"],
                         "Total": got["total"]}).sort_values("Total", ascending=False)


def reading(found: dict, leg: str, cfg: dict) -> list[dict]:
    """One leg's call, the numbers behind it and its Sobol table."""
    got, n, p = found["legs"][leg], len(found["cloud"]), found["coefficients"]
    against = (f"R² ajustado {got['r2_adj']:.3f} frente a {got['r2_ref']:.3f}, el percentil "
               f"{cfg['shuffle_percentile']:g} de {cfg['shuffles']} barajados")
    call = blocks.verdict("Ranking legible", "info", f"{against}: la superficie explica más "
                          "de lo que explica el ruido, y el ranking de abajo se puede leer.") \
        if got["legible"] else blocks.verdict(
            NOISE, "watch", f"{against}: no lo supera. Los índices de abajo describen una "
            "superficie que no se distingue del ruido; el ranking no se lee.")
    table = sobol(found, leg)
    numbers = pd.DataFrame(
        [["R² ajustado de la superficie", got["r2_adj"]],
         [f"Referencia barajada (percentil {cfg['shuffle_percentile']:g})", got["r2_ref"]],
         ["Variantes", n], ["Parámetros vivos", len(found["live"])], ["Coeficientes", p],
         ["Variantes por coeficiente", n / p],
         ["Suma de los índices de primer orden", table["Primer orden"].sum()],
         ["Suma de los índices totales", table["Total"].sum()]], columns=pd.Index(["", "Valor"]))
    return [call,
            blocks.table("¿Se puede leer?", numbers,
                         "El ranking sólo se lee si el R² ajustado supera su referencia "
                         "barajada. Si los índices de primer orden suman cerca de 1, cada "
                         "parámetro actúa por su cuenta; si los totales suman mucho más de 1, "
                         "el resultado depende de combinaciones finas: señal de fragilidad "
                         "para revisar a mano."),
            {"kind": "bars", "title": "Índice de Sobol total por parámetro", "unit": "",
             "reference": None, "help": "Parte de la variación de la superficie que pasa por "
             "ese parámetro, solo o en combinación con otros. Es un coeficiente de 0 a 1.",
             "items": [{"label": name, "value": float(total), "error": None, "state": "info"}
                       for name, total in zip(table["Parámetro"], table["Total"])]},
            {**blocks.table("Índices de Sobol", table),
             "help": [None, "Primer orden: el parámetro solo.",
                      "Total: solo más sus combinaciones con los demás."]}]


def counted(found: dict) -> dict[str, Any]:
    """How many variants each filter removed, as a table."""
    c = found["counts"]
    rows = [["Variantes que volvieron del retest", c["lote"]],
            ["Controles (canarios y pares inertes)", -c["controles"]],
            ["Menos operaciones en build que el suelo", -c["suelo_dentro"]],
            ["Duplicados exactos (mismo resultado en build y en oos1)", -c["duplicados"]],
            ["Quedan en el mapa", c["quedan"]],
            ["… de ellas, con alguna operación en oos1",
             int((found["cloud"]["oos1_trades"] > 0).sum())]]
    return blocks.table("Qué variantes entran", pd.DataFrame(rows, columns=pd.Index(["", "Variantes"])),
                        f"El suelo son {c['suelo']:g} operaciones en build, por los "
                        f"{c['vivos']} parámetros vivos del lote. El mapa no lee oos2.")


def tabs(found: dict, cfg: dict) -> list[dict]:
    """Build's map with its heat maps, oos1's as a secondary reading, and the filter counts."""
    if not found["legs"]:
        return [envelope.tab("build", TITLES["build"], [
            blocks.verdict("Sin dato", "info", f"Quedan {len(found['cloud'])} variantes y la "
                           f"superficie de {len(found['live'])} parámetros vivos tiene "
                           f"{found['coefficients']} coeficientes: no hay mapa que ajustar."),
            counted(found)], note=DESCRIPTION)]
    cloud = found["cloud"]
    maps = heatmaps.pairs(cloud, found["live"], cloud["build_excess"].to_numpy(dtype=float),
                          found["legs"]["build"]["indices"]["total"], "el exceso por año en build",
                          cfg["heatmap_pairs"])
    return [envelope.tab("build", TITLES["build"], reading(found, "build", cfg) + maps,
                         note=DESCRIPTION),
            envelope.tab("oos1", TITLES["oos1"], reading(found, "oos1", cfg),
                         note="Las mismas variantes y la misma superficie, con el exceso por "
                              "año de oos1 en vez del de build. Sirve para ver si los "
                              "parámetros que mandan en build siguen mandando después; no "
                              "decide nada."),
            envelope.tab("variantes", "Qué variantes entran", [counted(found)])]


def warnings(found: dict, cfg: dict) -> list[dict]:
    """What the reader must know before the ranking: noise, a thin fit, a floor not applied."""
    out = [{"code": "suelo", "state": "watch", "text": t} for t in found["counts"]["avisos"]]
    n, p, legs = len(found["cloud"]), found["coefficients"], found["legs"]
    if legs and not legs["build"]["legible"]:
        out.append({"code": "sin_estructura", "state": "watch",
                    "text": f"{NOISE}: el ranking de build no se lee."})
    if n < cfg["per_coefficient"] * p:
        out.append({"code": "pocas_variantes", "state": "watch",
                    "text": f"{n} variantes para {p} coeficientes: {n / p:.1f} por coeficiente, "
                            f"menos de {cfg['per_coefficient']:g}."})
    if len(found["live"]) < found["counts"]["vivos"]:
        out.append({"code": "colapsados", "state": "watch",
                    "text": f"El suelo de operaciones dejó {found['counts']['vivos'] - len(found['live'])} "
                            "parámetro(s) vivo(s) con un solo valor: quedan fuera de la superficie."})
    return out


def facts(found: dict) -> dict[str, Any]:
    """What the report carries of step 16.5 (proposal §4), nested as `pipeline.autopilot.facts` flattens it."""
    cloud, names = found["cloud"], [n[6:] for n in found["live"]]
    out = {"vivos": len(names), "coeficientes": found["coefficients"],
           "variantes": {"build": len(cloud), "oos1": int((cloud["oos1_trades"] > 0).sum())}}
    for leg, got in found["legs"].items():
        out[leg] = {"r2_ajustado": got["r2_adj"], "r2_barajado": got["r2_ref"],
                    "legible": got["legible"],
                    "sobol_primer": dict(zip(names, np.asarray(got["indices"]["first"]).tolist())),
                    "sobol_total": dict(zip(names, np.asarray(got["indices"]["total"]).tolist()))}
    return out
