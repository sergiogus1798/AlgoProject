"""The CSCV as the contract's blocks: where the chosen variant landed, and what choosing cost."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope

PERIODO = {"W": "semanal", "ME": "mensual", "D": "diario"}
CALL = {"primer_orden": "gana siempre", "segundo_orden": "gana en promedio",
        "ninguna": "no gana"}
GLOSSARY = [
    {"term": "PBO", "text": "De cada 100 formas de partir la historia en dos mitades, en "
     "cuántas la combinación elegida por la mitad de entrenamiento acabó por debajo de la "
     "mediana en la otra. Por encima del 50 % elegir así es peor que no elegir."},
    {"term": "Percentil OOS", "text": "En qué percentil del ranking real fuera de muestra cayó "
     "lo que la regla habría elegido. 50 es lo que da elegir a ciegas."},
    {"term": "Pendiente", "text": "Cuánto del orden dentro de muestra se conserva fuera, "
     "ajustado sobre todas las variantes de cada partición. Sobre ruido puro sale 0."},
    {"term": "Pierde", "text": "En qué fracción de las particiones lo elegido terminó la "
     "mitad reservada en pérdidas. El PBO habla de puesto; esto, de dinero."},
    {"term": "vs. la mediana", "text": "Si elegir con la regla bate a quedarse con la "
     "combinación del medio, en toda la distribución o sólo en promedio."}]


def verdict(found: dict, result: dict) -> dict:
    """The head rule's PBO as the call, every rule as a part."""
    head = next(iter(found))
    pbo = found[head]["pbo"]
    return blocks.verdict(
        f"PBO {pbo:.0%} con {head}", "fail" if pbo > 0.5 else "pass",
        f"Las {result['n']} variantes valen {result['n_clusters']} pruebas independientes; con "
        f"ese recuento el Sharpe del mejor sobrevive con probabilidad {result['dsr']:.2f} "
        f"(DSR). De una mitad a la otra el orden se conserva con pendiente "
        f"{result['slope']:+.2f}.", pbo,
        [{"label": name, "state": "fail" if f["pbo"] > 0.5 else "pass", "value": f["pbo"],
          "note": CALL[f["dominance"]]} for name, f in found.items()])


def tabs(runs: dict, found: dict, result: dict) -> list[dict]:
    """λ per rule, the rules side by side, and the head rule partition by partition."""
    head = next(iter(runs))
    unit = f"{result['score'].capitalize()} {PERIODO.get(result['period'], result['period'])}"
    records = runs[head]
    x, y = records["is_score"].to_numpy(), records["oos_score"].to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    return [
        envelope.tab("lambda", "Cuántas veces lo elegido queda por debajo de la mediana", [
            *[{**blocks.distribution(f"λ — {name}", "", r["lam"].to_numpy(), 0.0,
                                     f"PBO {found[name]['pbo']:.0%}: la parte a la izquierda "
                                     f"del cero."), "mark": "la mediana"}
              for name, r in runs.items()],
            blocks.table("Regla a regla", pd.DataFrame(
                [[name, f["pbo"], f["pct_oos"], f["ci95"][0], f["ci95"][1], f["prob_loss"],
                  CALL[f["dominance"]]] for name, f in found.items()],
                columns=["regla", "PBO", "percentil OOS", "IC 95 % desde", "hasta",
                         "pierde", "vs. la mediana"]))],
            note=f"{result['n']} variantes, {result['periods']} periodos de tipo "
                 f"{result['period']}, {result['blocks']} bloques y {result['partitions']} "
                 f"particiones, ordenadas por {unit.lower()}. El mejor dentro y el mejor "
                 f"fuera distan {result['levels_max']} niveles en el parámetro que más se "
                 f"movió."),
        envelope.tab("decay", f"Lo elegido por {head}, partición a partición", [
            {"kind": "scatter", "title": f"{unit} dentro contra fuera",
             "x_label": f"{unit} dentro de muestra", "y_label": "fuera",
             "points": [{"x": float(a), "y": float(b), "label": str(i), "group": head}
                        for i, (a, b) in enumerate(zip(x, y))],
             "quadrants": True, "fit": {"slope": float(slope), "intercept": float(intercept),
                                        "r": float(np.corrcoef(x, y)[0, 1])},
             "note": "Esta recta cae aunque no pase nada malo: las dos mitades son "
                     "complementarias. Sobre ruido puro marca -0,57. Lo que hay que leer es "
                     "la pendiente ajustada sobre todas las variantes, que sobre ruido marca "
                     "0."}],
            note="Este estudio no dice si la estrategia va a funcionar hacia delante: rompe "
                 "la cronología a propósito para juzgar el procedimiento de elección. Lo "
                 "que mira hacia delante es el holdout y la walk forward matrix.")]
