"""The tabs of one mother's reading in oos2: L1, the cells, L2, the drift and the segments."""

from typing import Any
import re

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope

UNIT = "USD/año"


def num(x: float, digits: int = 2) -> str:
    """A figure as the owner reads it: thousands apart, decimal comma."""
    return f"{x:,.{digits}f}".replace(",", " ").replace(".", ",")


def _axes(names: list[str]) -> tuple[list[int], list[int], dict]:
    """Rows (runs), columns (% OOS) and (runs, pct) -> the cell's name, from SQX's names."""
    at = {tuple(int(n) for n in re.findall(r"\d+", c)): c for c in names}
    return sorted({k[0] for k in at}), sorted({k[1] for k in at}), at


def heat(per_year: pd.Series, centre: str) -> dict[str, Any]:
    """Each cell's net excess per year in oos2, runs down and % OOS across, the centre marked."""
    rows, cols, at = _axes(list(per_year.index))
    values = [[float(per_year[at[r, c]]) for c in cols] for r in rows]
    top = float(np.abs(per_year).max()) or 1.0
    runs, pct = (int(n) for n in re.findall(r"\d+", centre))
    return {"kind": "grid", "title": "Exceso neto por año de cada celda en oos2",
            "help": "Lo que ganó cada celda en oos2 por encima de la deriva del mercado, ya "
                    "cobrada al coste de oos2, por año. Verde gana, rojo pierde. Las celdas "
                    "no son 30 pruebas: léelas con las celdas efectivas.",
            "rows": [str(r) for r in rows], "cols": [f"{c}%" for c in cols], "values": values,
            "scale": "diverging", "levels": [round(top * k, 2) for k in (-2/3, -1/3, 0, 1/3, 2/3)],
            "labels": [[num(v, 0) for v in row] for row in values],
            "mark": {"row": str(runs), "col": f"{pct}%", "label": "centro"},
            "note": "Filas: número de pasadas. Columnas: % de la ventana de optimización que "
                    "va fuera de muestra. Marcada, la celda del centro: la que se operaría "
                    "reoptimizando."}


def readings(got: dict, said: dict, cfg: dict) -> dict[str, Any]:
    """The annotations beside L1, each with the sentence that says what it is."""
    null, charged = cfg["null"], got["recharged"]
    rows = [
        ["Celdas con exceso positivo", f"{num(said['frac_celdas_positivas'] * 100, 1)} %",
         "Cuántas de las 30 celdas ganan en oos2. Depende del troceo del tiempo; no es un "
         "recuento de pruebas independientes."],
        ["Celdas efectivas", num(said["celdas_efectivas"], 1),
         "Por cuántas curvas independientes valen las 30, por los autovalores de su matriz "
         "de correlaciones semanales. 30 celdas de verdad independientes darían unas 25 "
         "con estas semanas."],
        ["Celda del centro", f"{num(said['centro']['exceso_oos2'])} {UNIT}",
         "Exceso neto por año en oos2 de la celda que se operaría reoptimizando "
         f"({got['centre']}), fijada antes de mirar."],
        ["Asimetría semanal", num(got["skew"]),
         "Asimetría de la serie semanal de la mediana de las celdas. El nulo supone semanas "
         f"simétricas; por encima de {num(null['skew_warn'], 1)} su cola baja rechaza de más."],
        ["Cierres tras fin de semana", f"{num(got['straddle'] * 100, 1)} %",
         "Operaciones cerradas lunes o martes tras pasar el fin de semana abiertas. Por "
         f"encima del {num(null['straddle_max'] * 100, 0)} % el nulo se repite en bloques de "
         "dos semanas."],
        ["Recobro de oos2", f"{num(charged['money'])} USD en {charged['trades']} operaciones",
         f"Lo cobrado de más a las operaciones que cierran en oos2 al pasar de los costes de "
         f"{cfg['recharge']['charged']} (con los que corrió la tarea) a los de oos2: spread, "
         "deslizamiento de entrada y de salida y comisión. No mueve stops ni objetivos."]]
    if got["l1_blocks"]:
        two = got["l1_blocks"]
        rows.append(["Nulo en bloques de dos semanas",
                     f"p+ {num(two['p_mas'], 3)} · p− {num(two['p_menos'], 3)}",
                     "L1 otra vez con las semanas volteadas de dos en dos. No cambia el estado."])
    return blocks.table("Lo que se anota", pd.DataFrame(rows, columns=pd.Index(["lectura", "valor", "qué es"])))


def l1(got: dict, said: dict, cfg: dict) -> dict[str, Any]:
    """L1 against its null band, the cells' heat map and the annotations."""
    one = said["l1"]
    return envelope.tab("l1", "L1 · reoptimizar en dato limpio", [
        blocks.distribution(
            "Mediana de las celdas en oos2 frente al nulo de volteo por semanas", UNIT,
            got["l1"]["null"], one["mediana_exceso"],
            f"Histograma: la misma mediana con el signo de cada semana sorteado, igual para "
            f"las 30 celdas ({cfg['null']['draws']} sorteos); quita la ventaja y conserva lo "
            f"que se parecen las celdas. Banda p5–p95: {num(one['nulo_p5'])} a "
            f"{num(one['nulo_p95'])}. p+ {num(one['p_mas'], 3)} es la parte de sorteos que "
            f"iguala o supera a la real; p− {num(one['p_menos'], 3)}, la que queda igual o "
            f"por debajo.", one["p_menos"]),
        heat(got["per_year"], got["centre"]), readings(got, said, cfg)],
        note="La mediana de las 30 celdas del exceso neto por año, sólo con las operaciones "
             "que cierran en oos2 y cobradas al coste de oos2. Es lo único que decide.")


def l2(got: dict, said: dict, mode: str) -> dict[str, Any]:
    """L2: the reference against the mother with fixed parameters, week by week."""
    two = said["l2"]
    what = ("la celda del centro" if mode == "reoptimizado" else
            "la mediana semanal de las 30 celdas")
    weeks = [d.date().isoformat() for d in got["cells"].index]
    return envelope.tab("l2", "L2 · reoptimizar frente a congelar", [
        blocks.distribution(
            "Diferencia por año entre reoptimizar y la madre fija, frente al nulo", UNIT,
            got["l2"]["null"], two["delta"],
            f"Suma semanal de ({what} − la madre con sus parámetros fijos, recobrada igual), "
            f"por año, y la misma diferencia con los mismos sorteos de signos de L1. Banda "
            f"p5–p95: {num(two['nulo_p5'])} a {num(two['nulo_p95'])}. p+ "
            f"{num(two['p_mas'], 3)}, p− {num(two['p_menos'], 3)}.", two["p_menos"]),
        {"kind": "lines", "title": "Exceso neto acumulado en oos2", "unit": "USD", "x": weeks,
         "series": [{"label": what, "role": "real", "values": got["ref"].cumsum().tolist()},
                    {"label": "madre con parámetros fijos", "role": "reference",
                     "values": got["mother"].cumsum().tolist()}],
         "zero_shade": True,
         "note": "Cada operación entera en la semana en que cierra. Por encima de la madre, "
                 "reoptimizar compensó en oos2."}],
        note="¿Compensa reoptimizar? Positivo: reoptimizar gana a dejar la madre como está. "
             + ("Decide (sólo puede dar LIMBO) porque se va a reoptimizar en real."
                if mode == "reoptimizado" else "En modo fijo se anota y no decide."))


def drift(row: dict, stability: pd.DataFrame) -> dict[str, Any]:
    """How much the optimiser re-decides at every step, over the mother's own parameters."""
    table = pd.DataFrame(
        [["Parámetros de la madre", row["parameters"], "Los que la reoptimización puede mover."],
         ["Saltos entre reoptimizaciones", row["pairs"], "Pares de tramos consecutivos, en las 30 celdas."],
         ["Parámetros que cambian por salto (mediana)", f"{num(row['share_changed_median'] * 100, 1)} %",
          "Fracción de los parámetros de la madre que el optimizador cambia de un tramo al "
          "siguiente. Cerca del 100 %: cada reoptimización elige casi otra estrategia."],
         ["Movimiento medio (mediana)", num(row["move_median"]),
          "Cuánto se mueve cada parámetro por salto, en desviaciones típicas de ese parámetro."]],
        columns=pd.Index(["lectura", "valor", "qué es"]))
    return envelope.tab("drift", "Deriva de parámetros", [
        blocks.table("Cuánto re-decide el optimizador", table),
        blocks.table("Los parámetros sobre los que más se repite",
                     stability.drop(columns=["strategy"]).head(5).rename(columns={
                         "parameter": "parámetro", "distinct": "valores distintos",
                         "modal_share": "tramos con el valor más repetido"}),
                     "Qué parámetros elige casi siempre igual: candidatos a congelar.")],
        note="Si se va a reoptimizar en real, esto dice cuánto cambiará la estrategia cada vez.")


def segments(table: pd.DataFrame) -> dict[str, Any]:
    """Each cell's net excess per year in build, oos1 and oos2."""
    rows, cols, at = _axes(list(table.index))
    out = pd.DataFrame([[r, f"{c}%", *table.loc[at[r, c]].round(2)] for r in rows for c in cols],
                       columns=pd.Index(["pasadas", "% OOS", *table.columns]))
    return envelope.tab("segments", "Exceso por tramo", [blocks.table(
        "Exceso neto por año de cada celda, por tramo", out,
        "USD por año de los que las pasadas de la celda cubren de cada tramo; vacío donde no "
        "llegan. build y oos1 van al coste con que corrió la tarea; sólo oos2 está recobrado. "
        "La selección del paso 8 se ve en oos1: ahí las celdas ganan porque por eso se eligió "
        "la madre.")],
        note="Dónde gana cada celda. Sólo oos2 es dato que nadie usó para elegir.")
