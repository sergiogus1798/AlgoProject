"""The fragility tab: T1 as one small table, whose cells are the judge's facts."""

from typing import Any

import pandas as pd

from core.study import blocks
from core.study import result as envelope

# One table per test, titled by its code alone, one row per window, one column per measure:
# `pipeline.autopilot.facts.flatten` then names each cell `fragilidad.<test>.<window>.<measure>`
# whatever the order of rows or tables. Renaming a title, a row or a column renames a fact
# `pipeline/autopilot/criteria.yaml` may be judging.
COLUMNS = {"t1": ["ret_med", "ret_p5", "f_pos", "ret_benef", "beta_share", "n", "rho_vec",
                  "percentil_madre", "dd_r_p99"]}

HELP = {
    "ret_med": "Retención mediana: mediana del exceso total de las re-ejecuciones dividida por "
               "el exceso total del original. 1 = la re-ejecución típica conserva todo el "
               "exceso. Vacía si el exceso del original no es positivo.",
    "ret_p5": "Retención en el percentil 5: la cola mala. Se anota, sin umbral.",
    "f_pos": "Fracción de re-ejecuciones con exceso total mayor que cero.",
    "ret_benef": "Retención mediana sobre el BENEFICIO, sin restar la deriva. Alta con ret_med "
                 "baja = meseta falsa: lo que aguanta es el mercado, no la lógica.",
    "beta_share": "Deriva cobrada / beneficio: la parte de lo que gana que es el mercado.",
    "n": "Re-ejecuciones leídas.",
    "rho_vec": "Correlación de rangos entre el exceso de las vecinas en build y en oos1.",
    "percentil_madre": "Dónde queda la madre entre sus vecinas en oos1, por exceso neto de "
                       "deriva (0 a 100; empates a medias). Un hecho, sin umbral.",
    "dd_r_p99": "Percentil 99 del drawdown máximo de las vecinas sobre build + oos1 juntos, en "
                "R (múltiplos del riesgo por operación): la dispersión que fija k. Un hecho, "
                "sin umbral. Fila «ambas»."}

NOTE = {
    "t1": "T1 — especificación: vecinas con los parámetros y las salidas movidos, exceso exacto "
          "(sus operaciones se exportan con fechas)."}


def _table(test: str, rows: dict) -> dict[str, Any]:
    """One test's table: `rows` is {window: {measure: value}}, columns in COLUMNS' order."""
    frame = pd.DataFrame([[window, *(got.get(c) for c in COLUMNS[test])]
                          for window, got in rows.items()],
                         columns=pd.Index(["Ventana", *COLUMNS[test]]))
    frame[COLUMNS[test]] = frame[COLUMNS[test]].astype(float)
    return blocks.table(test.upper(), frame, NOTE[test], 4) | {
        "help": [None, *(HELP[c] for c in COLUMNS[test])], "compact": True}


def _t1_rows(t1: dict) -> dict[str, dict[str, float]]:
    """T1's flat facts as table rows: `t1.build.ret_med` → row «build», `t1.rho_vec` → «ambas»."""
    rows: dict[str, dict[str, float]] = {}
    for key, value in t1.items():
        window, _, measure = key.removeprefix("t1.").rpartition(".")
        rows.setdefault(window or "ambas", {})[measure] = value
    return rows


def tab(t1: dict | None) -> dict | None:
    """The tab «Fragilidad»: what the parameter neighbours keep of the original's excess.

    Args:
        t1: The T1 facts of this strategy as `neighbours.t1.facts()` returns them — flat,
            `t1.<window>.<measure>` and `t1.rho_vec`, the measures of COLUMNS["t1"] — or
            None while nothing provides them. This is where the neighbours' measure enters
            the result: the caller reads it and hands it over (`one.contract`, from
            `inputs["t1"]`, {strategy: facts}); this module imports nothing of it.

    Returns:
        The tab, or None without T1 facts.
    """
    return envelope.tab(
        "fragilidad", "Fragilidad (T1)", [_table("t1", _t1_rows(t1))],
        note="Retención del EXCESO: el beneficio menos lo que el mercado pagó por estar "
             "dentro, con la deriva de cada año natural. Son hechos, no juicio: el paso 14 "
             "no tiene regla (encargo 65 §3d).") if t1 else None
