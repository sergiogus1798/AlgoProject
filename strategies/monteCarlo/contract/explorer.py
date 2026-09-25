"""The explorer tab: any sub-test's distribution of any statistic, chosen by two selectors."""

import pandas as pd

from core.study import blocks, result as envelope
from strategies.monteCarlo.contract import shapes
from strategies.monteCarlo.contract.words import LABELS
from strategies.monteCarlo.model import stress


def runs(result: dict) -> list[tuple[str, str, dict, dict]]:
    """Every sub-test the study kept: (label, readable name, shapes, tables)."""
    out = [(k, result["titles"][k], result[g]["shapes"][k], result[g]["runs"][k])
           for g in ("A", "B") for k in result[g]["shapes"]]
    return out + [(k, stress.TITLES[k], v["shapes"], v["table"]) for k, v in result["C"].items()]


def pair(label: str, title: str, shape: dict, table: dict, rerun: bool = False) -> list[dict]:
    """One sub-test's distribution and percentile table for every statistic, tagged."""
    mark = " (re-ejecución)" if rerun else ""
    out = []
    for metric, name in LABELS.items():
        where = {"prueba": title, "métrica": name}
        flat = table[metric]["p"][min(table[metric]["p"])] == table[metric]["p"][
            max(table[metric]["p"])]
        note = ("Esta prueba conserva este estadístico por construcción: reordenar las mismas "
                "operaciones no puede cambiarlo. Mira el drawdown o la racha." if flat else "")
        out.append({**shapes.distribution(shape[metric], table[metric], metric,
                                          f"{title}{mark} — {name}", note),
                    "select": where, "rerun": rerun})
        out.append({**shapes.summary(table[metric], metric, f"{title}{mark} — {name}"),
                    "select": where, "rerun": rerun})
    return out


def tab(result: dict, cones: dict) -> dict:
    """Every sub-test × statistic, and each sub-test's equity cone."""
    found = runs(result)
    body = []
    for label, title, shape, table in found:
        body += pair(label, title, shape, table)
        if label in cones:
            body.append({**shapes.cone(cones[label], f"{title} — curva de equity",
                                       "Bandas 2,5–97,5 y 25–75; la línea es el backtest."),
                         "select": {"prueba": title}})
    return envelope.tab(
        "explorer", "Explorador de pruebas", body,
        selectors=[{"key": "prueba", "label": "Prueba", "options": [t for _, t, _, _ in found],
                    "default": found[0][1]},
                   {"key": "métrica", "label": "Métrica", "options": list(LABELS.values()),
                    "default": LABELS["dd_pct"]}],
        note="Cualquier subprueba de cualquier familia y cualquier estadístico. Una "
             "re-ejecución se ve al lado de la guardada y nunca mueve el veredicto: un "
             "veredicto sale de un análisis entero o de ninguno.")


def method(result: dict, cfg: dict, shared: dict) -> dict:
    """What was run, on what data, and what this report may not be used to conclude."""
    g, cost, stab = cfg["global"], result["cost_check"], shared["stability"]
    rows = [["simulaciones por prueba", f"{g['n_sims']:,}"],
            ["cuenta inicial / riesgo por operación",
             f"{g['starting_equity']:,.0f} $ / {g['risk_per_trade']:,.0f} $"],
            ["operaciones exportadas", str(shared["export"])],
            ["barras diarias", str(shared["bars"])],
            ["coste recuperado del propio backtest", f"{cost['recovered']:.2f} $ mediana"],
            ["coste modelado desde assets/", f"{cost['modelled']:.2f} $ (ratio "
                                             f"{cost['ratio']:.2f})"],
            ["modelo de volatilidad", cfg["family_d"]["vol_model"]],
            ["estabilidad, peor número", f"{stab['worst']} ±{stab['worst_spread']:.1%} en "
                                         f"{stab['runs']} repeticiones"],
            ["semilla", "ninguna: cada ejecución usa entropía nueva"]]
    limits = [["No mide sobreajuste", "No hay Deflated Sharpe ni CSCV: harían falta todas las "
               "estrategias probadas en la generación."],
              ["No valida el edge", "Da por hecho que la estrategia lo tiene y mide de qué "
               "depende."],
              ["El techo de drawdown es provisional",
               f"{cfg['scoring']['survival_dd_pct']:.0%} de la cuenta hasta que las reglas de "
               f"la prop firm lo fijen."],
              ["Nada se repite igual dos veces", "Sin semilla, a propósito: la estabilidad dice "
               "cuánto se mueven los números que deciden."]]
    return envelope.tab("method", "Datos y método", [
        blocks.table("Qué se corrió", pd.DataFrame(rows, columns=["qué", "valor"])),
        blocks.table("Lo que este informe no dice", pd.DataFrame(limits,
                                                                 columns=["", "por qué"]))])


GLOSSARY = [
    {"term": "Inflación del drawdown", "text": "El drawdown del percentil 95 reordenando entre "
     "el del backtest. Por encima de 1, el orden en que llegaron las operaciones fue amable."},
    {"term": "Percentil 5", "text": "El valor que sólo el 5 % de las simulaciones empeora."},
    {"term": "Bootstrap estacionario", "text": "Remuestreo por bloques de longitud aleatoria; "
     "conserva rachas de operaciones correlacionadas."},
    {"term": "PSR", "text": "Probabilistic Sharpe Ratio: probabilidad de que el Sharpe real "
     "supere cero dada la muestra y su forma."},
    {"term": "Compuesto", "text": "Media ponderada de los cinco sub-scores; sólo cuenta si "
     "ninguna prueba veta."}]
