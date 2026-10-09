"""The fragility tab: T1, T2 and T3 as one small table each, whose cells are the judge's facts."""

import pandas as pd

from core.study import blocks, result as envelope

# One table per test, titled by its code alone, one row per window, one column per measure:
# `pipeline.autopilot.facts.flatten` then names each cell `fragilidad.<test>.<window>.<measure>`
# whatever the order of rows or tables. Renaming a title, a row or a column renames a fact
# `pipeline/autopilot/criteria.yaml` may be judging.
COLUMNS = {"t1": ["ret_med", "ret_p5", "f_pos", "ret_benef", "beta_share", "n", "rho_vec"],
           "t2": ["ret_med_aprox", "ret_p5_aprox", "f_pos", "ret_benef", "same_count_frac",
                  "count_dev_med", "n"],
           "t3": ["ret_med", "ret_p5", "matched_frac", "identical_frac", "distinct", "n"]}
WINDOW = {"t2": "build", "t3": "build"}
TASK = {"t2": "ohlc", "t3": "bar"}

HELP = {
    "ret_med": "Retención mediana: mediana del exceso total de las re-ejecuciones dividida por "
               "el exceso total del original. 1 = la re-ejecución típica conserva todo el "
               "exceso. Vacía si el exceso del original no es positivo.",
    "ret_med_aprox": "Retención mediana APROXIMADA: como ret_med, pero el exceso de cada "
                     "re-ejecución es su beneficio total menos la deriva que cobró el ORIGINAL "
                     "(una re-ejecución no trae fechas con las que calcular la suya).",
    "ret_p5": "Retención en el percentil 5: la cola mala. Se anota, sin umbral.",
    "ret_p5_aprox": "Retención APROXIMADA en el percentil 5 del exceso: la cola mala. Se "
                    "anota, sin umbral.",
    "f_pos": "Fracción de re-ejecuciones con exceso total mayor que cero.",
    "ret_benef": "Retención mediana sobre el BENEFICIO, sin restar la deriva. Alta con ret_med "
                 "baja = meseta falsa: lo que aguanta es el mercado, no la lógica.",
    "beta_share": "Deriva cobrada / beneficio: la parte de lo que gana que es el mercado.",
    "same_count_frac": "Fracción de re-ejecuciones con exactamente las mismas operaciones que "
                       "el original: lo que sostiene la aproximación (la exposición apenas "
                       "cambia). Suele ser baja aunque el número de operaciones apenas se "
                       "mueva: léela junto a count_dev_med.",
    "count_dev_med": "Cuánto se aleja el número de operaciones de la re-ejecución típica del "
                     "del original, como fracción de éste (mediana). 0,01 = un 1 % de "
                     "operaciones de más o de menos: la exposición apenas cambia.",
    "identical_frac": "Fracción de re-ejecuciones cuya cola cubre toda la ventana común: ahí "
                      "son el original, operación a operación. Si pasa de la mitad, ret_med "
                      "es 1 por construcción; lo que se separa se ve en ret_p5.",
    "matched_frac": "Fracción de re-ejecuciones cuya cola de operaciones coincide con la del "
                    "original (al menos fragility.min_tail seguidas): sólo ésas tienen fechas "
                    "y cuentan. Por debajo de fragility.min_matched no hay ret_med.",
    "distinct": "Resultados distintos entre las re-ejecuciones. Con uno solo la tarea no "
                "movió nada y no hay ret_med.",
    "n": "Re-ejecuciones leídas.",
    "rho_vec": "Correlación de rangos entre el exceso de las vecinas en build y en oos1."}

NOTE = {
    "t1": "T1 — especificación: vecinas con los parámetros y las salidas movidos, exceso exacto "
          "(sus operaciones se exportan con fechas).",
    "t2": "T2 — histórico: ¿depende de las velas exactas? Cada vela retocada (MCR 7). Medida "
          "aproximada (aprox.): SQX guarda de cada re-ejecución sólo el beneficio por "
          "operación, sin fechas, así que se le resta la deriva por año natural que cobró el "
          "original.",
    "t3": "T3 — control: la barra inicial (MCR 1). Se mide sólo en la ventana común — las "
          "operaciones del original abiertas después del último arranque posible — y sólo con "
          "las re-ejecuciones cuya cola coincide con la del original: ahí el exceso es exacto. "
          "Donde una re-ejecución se separa dentro de la ventana, su tramo sin fechas se "
          "aproxima con la deriva del original, y las operaciones que hizo antes de la ventana "
          "(como mucho las de esas barras) entran en la cuenta. Nunca da NO PASA."}


def _table(test: str, rows: dict) -> dict:
    """One test's table: `rows` is {window: {measure: value}}, columns in COLUMNS' order."""
    frame = pd.DataFrame([[window, *(got.get(c) for c in COLUMNS[test])]
                          for window, got in rows.items()],
                         columns=["Ventana", *COLUMNS[test]])
    frame[COLUMNS[test]] = frame[COLUMNS[test]].astype(float)
    return blocks.table(test.upper(), frame, NOTE[test], 4) | {
        "help": [None, *(HELP[c] for c in COLUMNS[test])], "compact": True}


def _t1_rows(t1: dict) -> dict:
    """T1's flat facts as table rows: `t1.build.ret_med` → row «build», `t1.rho_vec` → «ambas»."""
    rows = {}
    for key, value in t1.items():
        window, _, measure = key.removeprefix("t1.").rpartition(".")
        rows.setdefault(window or "ambas", {})[measure] = value
    return rows


def tab(got: dict, t1: dict | None) -> dict | None:
    """The tab «Fragilidad»: what the re-runs keep of the original's excess over the drift.

    Args:
        got: What run.one() returned for one strategy; `retention` holds T2 and T3.
        t1: The T1 facts of this strategy as `neighbours.t1.facts()` returns them — flat,
            `t1.<window>.<measure>` and `t1.rho_vec`, the measures of COLUMNS["t1"] — or
            None while nothing provides them. This is where the neighbours' measure enters
            the result: the caller reads it and hands it over (`one.contract`, from
            `inputs["t1"]`, {strategy: facts}); this module imports nothing of it.

    Returns:
        The tab, a table per test that has data, or None when none has.
    """
    kept = got["retention"]
    tables = ([_table("t1", _t1_rows(t1))] if t1 else []) + [
        _table(t, {WINDOW[t]: kept[t]}) for t in ("t2", "t3") if kept[t]]
    return envelope.tab(
        "fragilidad", "Fragilidad (T1, T2, T3)", tables,
        note="Retención del EXCESO: el beneficio menos lo que el mercado pagó por estar "
             "dentro, con la deriva de cada año natural. PASA aquí significa «no es frágil», "
             "no «tiene ventaja». Los cortes están en criteria.yaml, no aquí.") if tables else None


def warnings(got: dict) -> list[dict]:
    """One warning per test whose task ran and which still has no data."""
    return [{"code": f"sin_{t}", "state": "watch",
             "text": f"{t.upper()} sin dato: el ingest no guarda las operaciones del build con "
                     "fechas (es anterior al 2026-10-07) o no casan una a una con el original "
                     "de la tarea. Repite el ingest tras cosechar el proyecto."}
            for t in ("t2", "t3") if TASK[t] in got and got["retention"][t] is None]
