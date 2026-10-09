"""One strategy's SPP reconnaissance as the contract's tabs: the noise call, and the two performance panels."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.breakage.spp import criteria
from studies.breakage.spp.model import combine

VERDICT = {"proceed": ("SEGUIR", "pass", "aprueba: el máximo supera lo que daría una rejilla de ruido"),
           "noise": ("RUIDO", "fail", "no aprueba: el máximo no supera lo que daría una rejilla de ruido")}

# What "combinado" means for each metric, spelled out beside its histogram (2026-09-30, §7):
# an SPP grid cannot be concatenated across windows (README.md), so four metrics are rebuilt
# from their additive components and two are only a pooled, broader sample.
COMBINED_CAVEAT = {
    "NetProfit": "combinado: suma exacta de ambas ventanas.",
    "ProfitFactor": "combinado: bruto ganado y bruto perdido sumados, PF recalculado — no la "
                    "media de los dos PF.",
    "ReturnDDRatio": "combinado: Net Profit y Max Drawdown combinados, recalculado — no la "
                     "suma de los dos ratios.",
    "Drawdown": "combinado: suma de las dos caídas — cota superior; la caída conjunta real "
               "pudo ser menor si no coinciden en el tiempo.",
    "SharpeRatio": "combinado: no hay operaciones por permutación para recalcularlo; aquí se "
                  "agrupan las permutaciones de IS y de OOS1 como una sola muestra.",
    "SortinoRatio": "combinado: mismo agrupamiento que Sharpe, no una ventana conjunta "
                    "recalculada."}


def verdict(result: dict) -> dict:
    """Whether the family is anything but noise, with the numbers behind the call."""
    n, s = result["noise"], result["shape"]
    label, state, meaning = VERDICT[n["verdict"]]
    return blocks.verdict(label, state, f"{meaning.capitalize()}: exceso del máximo sobre la media {n['excess']:.3f} "
                          f"contra {n['noise_max']:.3f} bajo el nulo σ·√(2·ln n_eff).",
                          n["ratio"],
                          [{"label": "Tuplas distintas (n_eff)", "state": "info",
                            "value": n["n_eff"], "note": f"de {n['n_rows']:,} filas"},
                           {"label": "Área de meseta", "state": "info",
                            "value": n["plateau_area"], "note": ""},
                           {"label": "(Máx − mediana)/IQR", "state": "info",
                            "value": s["spike_ratio"], "note": f"Curtosis {s['kurtosis']:.2f}"}])


# Where a metric stops being profitable; Max Drawdown has no good side, so no shade.
PIVOT = {"ProfitFactor": 1.0, "EdgeRatioInPips": 1.0}
NO_SHADE = {"Drawdown"}


def _hist(col: str, name: str, unit: str, values: np.ndarray, real: float | None, share: float,
         caveat: str) -> dict:
    """One panel-1 histogram: the grid's distribution, the real backtest, a median ± share band."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    median = float(np.median(arr))
    lo, hi = median - share * abs(median), median + share * abs(median)
    b = blocks.distribution(name, unit, arr, real, "", sign_shade=col not in NO_SHADE,
                           **({"pivot": PIVOT[col]} if col in PIVOT else {}))
    b["band"] = [lo, hi]
    where = "" if real is None else ("dentro" if lo <= real <= hi else "fuera")
    b["note"] = (f"Banda: mediana ± {share:.0%} de su propio valor."
                + (f" El real queda {where} de la banda." if where else "")
                + (f" {caveat}" if caveat else ""))
    return b


def panel1(periods: list[tuple[str, dict, dict, bool]], share: float) -> dict:
    """The six across-time histograms, one period at a time (2026-09-30, §7).

    Args:
        periods: `[(label, {metric: array}, {metric: real or None}, is_combined), ...]` — one
            entry per period the data actually supports (IS, OOS1, combined), built by
            `one._periods`.
        share: The band's half-width as a share of the median (`config.yaml: panel1.band_share`).

    Returns:
        One tab, a selector only when there is more than one period to choose from (§1: a
        selector that changes nothing is removed).
    """
    made = []
    for label, values, reals, combined in periods:
        for col, name, unit in combine.METRICS:
            caveat = COMBINED_CAVEAT[col] if combined else ""
            real = reals.get(col)
            if combined and col in ("SharpeRatio", "SortinoRatio") and real is None:
                caveat += " Sin real marcado: falta el export de operaciones para " \
                          "reconstruirlo (skill /export)."
            b = _hist(col, name, unit, values[col], real, share, caveat)
            if len(periods) > 1:
                b["select"] = {"periodo": label}
            made.append(b)
    selectors = ([{"key": "periodo", "label": "Periodo", "options": [p[0] for p in periods],
                  "default": periods[0][0]}] if len(periods) > 1 else [])
    return envelope.tab(
        "panel1", "Distribución del rendimiento", made, selectors=selectors,
        note="Se varían todos los parámetros a la vez, al azar, dentro de un rango — miles de "
             "backtests — y se estudia la distribución de la performance que resulta, no un "
             "solo número. Cada histograma marca el backtest real y la mediana de la "
             "distribución, con una banda de ± el porcentaje configurado sobre la mediana.")


def panel2(is_pop: pd.DataFrame, oos_pop: pd.DataFrame, is_real: pd.Series,
          oos_real: pd.Series) -> dict:
    """IS against OOS1 overlaid, time-free metrics only (2026-09-30, §7).

    Args:
        is_pop, oos_pop: `export.without_original()` grids of each window.
        is_real, oos_real: Each window's permutation -1 row, for the per-series real mark.

    Returns:
        One tab, one overlaid `distribution` block per time-free metric the strategy's SPP
        actually varied.
    """
    made = []
    for col, name, unit in combine.TIME_FREE:
        if col not in is_pop.columns or col not in oos_pop.columns:
            continue
        a, b = is_pop[col].to_numpy(float), oos_pop[col].to_numpy(float)
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        reals = {"IS": float(is_real[col]) if col in is_real.index else None,
                "OOS1": float(oos_real[col]) if col in oos_real.index else None}
        edge = PIVOT.get(col, 0.0)
        pcts = " · ".join(f"{k}: {100 * float((v > edge).mean()):.1f} % por encima de {edge:g}"
                          .replace(".", ",") for k, v in (("IS", a), ("OOS1", b)))
        made.append(blocks.distribution(
            name, unit, np.concatenate([a, b]), None,
            f"{pcts}. IS y OOS1 solapadas como densidad (cada una integra a 1): compara su "
            "forma, no el tamaño de la muestra.", series={"IS": a, "OOS1": b}, reals=reals,
            sign_shade=col not in NO_SHADE,
            **({"pivot": PIVOT[col]} if col in PIVOT else {})))
    return envelope.tab(
        "panel2", "IS contra OOS1: lo que no crece con la ventana", made,
        note="Solo métricas atemporales: Sharpe, Sortino, Profit Factor y R/Edge ratio — nunca "
             "Net Profit ni Retorno/Drawdown, que crecen con la ventana y no se pueden comparar "
             "así entre una IS larga y una OOS1 más corta. Kaufman Efficiency Ratio no está "
             "entre las columnas que SQX exporta para el SPP, así que no aparece.")


# The map (step 16, 2026-10-07). Tab names are the fact keys: `spp.build.mapa.sharpe.d`.
# Table cells stay numbers on purpose: the autopilot reads them as facts.
MAP_HELP = [
    None,
    "El resultado de la madre (el backtest de SQX) en esta ventana.",
    "Mediana de la rejilla: lo que rinde la idea con parámetros razonables, sin la suerte de "
    "haber elegido la mejor combinación. No quita la suerte del periodo.",
    "Rango intercuartílico de la rejilla: su anchura típica.",
    "(real − mediana) / IQR: cuántas anchuras de su vecindario queda la madre por encima. Para el "
    "drawdown el signo va al revés (mediana − real): lo sospechoso es un drawdown menor que el de "
    "los vecinos. Vacío si la rejilla es plana.",
    "Parte de la rejilla estrictamente peor que la madre (en el drawdown, con un drawdown mayor): "
    "alto = sospechosamente buena."]
TAIL_HELP = [
    None,
    "Encogimiento: mediana / real del beneficio anual. 0,7 = con parámetros razonables cabe esperar "
    "el 70 % del backtest. Vacío si el real no es positivo.",
    "Percentil 10 del beneficio anual de la rejilla: la mala mano al elegir parámetros.",
    "Percentil 5 del beneficio anual de la rejilla.",
    "Drawdown con mala mano: percentil 95 del drawdown de la rejilla / drawdown de la madre."]
GRID_HELP = [
    None,
    "Combinaciones que quedan tras quitar duplicados exactos, desplazamientos distintos de la "
    "madre y permutaciones con pocas operaciones.",
    "Parte de las combinaciones distintas que se quitó por tener menos operaciones que el suelo.",
    "Parte de la rejilla que se quitó por mover un desplazamiento (SQX los mueve de 0 a 6).",
    "Parte de la rejilla con Net Profit mayor que 0, sobre el periodo entero: todos los vecinos "
    "comparten la suerte del histórico.",
    "Años de la ventana."]
NA = float("nan")


def _row(label: str, d: dict, keys: tuple[str, ...]) -> list:
    """One table row: the label, then each key's value or NaN where this row has none."""
    return [label] + [d.get(k, NA) for k in keys]


def map_tab(name: str, title: str, w: dict) -> dict:
    """One window's map: the mother against its floored grid, on four metrics.

    Args:
        name: The tab's name and so its fact prefix: `build` or `oos1`.
        title: The tab's title in Spanish.
        w: `mapa.window`'s output.
    """
    m = w["metrics"]
    mapa_cols = ("real", "median", "iqr", "d", "puesto")
    tail_cols = ("s", "p10", "p5", "m_dd")
    made = [
        criteria.table(
            "mapa", ["métrica", "real", "median", "IQR", "d", "puesto"],
            [_row(k, v, mapa_cols) for k, v in m.items()],
            "Lectura 1: ¿la madre es un vecino más o un extremo de su rejilla? Sin juzgar.", MAP_HELP),
        criteria.table(
            "cola", ["métrica", "s", "p10", "p5", "m_dd"],
            [_row("benef_anual", m["benef_anual"], tail_cols),
             _row("drawdown", m["drawdown"], tail_cols)],
            "Cola baja del beneficio anual y drawdown con mala mano.", TAIL_HELP),
        criteria.table(
            "rejilla", ["", "n", "excluidas_frac", "fijos_frac", "frac_vecinos_rentables", "años"],
            [["grid", w["n"], w["excluidas_frac"], w["fijos_frac"], w["frac_vecinos_rentables"],
              w["years"]]],
            "La rejilla que leen todas las estadísticas de esta pestaña.", GRID_HELP)]
    s = w["sobresale"]
    if s:
        made.append(criteria.table(
            "sobresale", ["", "pass", "score"],
            [["grid", float(s["verdict"] == "proceed"), s["ratio"]]],
            "El máximo de Sharpe de la rejilla frente a lo que daría una rejilla de ruido. Solo se "
            "anota: no es puerta de nada.",
            [None, "1 si el máximo supera el nulo del ruido.",
             "Exceso del máximo sobre la media / máximo del nulo."]))
    return envelope.tab(name, title, made,
                        note="Se leen sólo las permutaciones distintas, con operaciones suficientes y "
                             "con los desplazamientos como los de la madre; la madre no está en la rejilla.")


def windows_tab(across: dict, build: dict, oos: dict) -> dict:
    """The two windows' Sharpe distributions side by side: three numbers and two overlaid histograms."""
    made = [criteria.table(
        "decaimiento", ["métrica", "r_s", "z_decay", "a"],
        [_row("sharpe", across, ("r_s", "z_decay", "a"))],
        "Se comparan distribuciones, nunca vecino contra vecino.",
        [None, "Mediana(oos1) / mediana(build); sólo si la mediana del build supera su suelo.",
         "Desplazamiento de la mediana entre el ruido esperado √(1/T_build + 1/T_oos1): "
         "-2 es una caída que supera el ruido.",
         "A de Vargha–Delaney: probabilidad de que una permutación de oos1 al azar supere a una del "
         "build al azar. 0,5 = iguales."])]
    for col, name in (("SharpeRatio", "Sharpe"), ("ProfitFactor", "Profit Factor")):
        a, b = build["frame"][col].to_numpy(float), oos["frame"][col].to_numpy(float)
        made.append(blocks.distribution(
            f"{name}, build y oos1", "", np.concatenate([a, b]), None,
            f"Mediana build {np.median(a):.2f}, mediana oos1 {np.median(b):.2f}. Cada una integra a 1: "
            "compara su forma, no el tamaño de la muestra.", series={"build": a, "oos1": b},
            reals={"build": build["metrics"][name.lower().replace(" ", "_")]["real"],
                   "oos1": oos["metrics"][name.lower().replace(" ", "_")]["real"]},
            sign_shade=False, **({"pivot": 1.0} if col == "ProfitFactor" else {})))
    return envelope.tab("ventanas", "Build contra oos1", made,
                        note="oos1 es más corto: su Sharpe sale más ancho sólo por eso. z_decay descuenta "
                             "ese ruido.")
