"""What the IS metrics of a whole population say about its OOS outcomes, as one contract result."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from engines.inference import fdr
from studies.screening.analysis import correlations, metrics

MODULE = "studies.screening.isOos.report"
TARGETS = ["Profit factor (OOS)", "Sharpe Ratio (OOS)", "Ret/DD Ratio (OOS)", "Net profit (OOS)"]


def run(inputs: dict, cfg: dict) -> dict:
    """The IS × OOS correlation map, persistence, and one predictor ranking per outcome.

    Args:
        inputs: `columns` (numeric columns from analysis.metrics.load), `n` (strategies in
            the export), `is` and `oos` (the measured columns of each side).
        cfg: The study's config; this half has no knob, so the hash is the outcomes'.

    Returns:
        The contract dict, the Benjamini-Hochberg survivors marked in every ranking.
    """
    started = time.time()
    columns, n, is_metrics = inputs["columns"], inputs["n"], inputs["is"]
    ranked = {t: correlations.predictors(columns, t, is_metrics)
              for t in TARGETS if t in inputs["oos"]}
    found = {t: fdr.discoveries(rows) for t, rows in ranked.items()}
    persist = pd.DataFrame(correlations.persistence(columns, metrics.paired(columns)))
    rho = {t: {r["metric"]: r["spearman"] for r in rows} for t, rows in ranked.items()}
    r_crit = correlations.critical_r(n)
    tabs = [envelope.tab("map", "Mapa de correlaciones", [
        {"kind": "grid", "title": "Spearman de cada métrica IS con cada resultado OOS",
         "rows": is_metrics, "cols": list(ranked),
         "values": [[rho[t].get(m) for t in ranked] for m in is_metrics],
         "scale": "diverging", "levels": [-0.3, -0.2, -0.1, -0.05, 0.05, 0.1, 0.2, 0.3],
         "labels": [["✓" if m in found[t] else "" for t in ranked] for m in is_metrics],
         "note": "✓ sobrevive Benjamini-Hochberg en su columna. Escala recortada a ±0,3: "
                 "estas correlaciones viven ahí."}],
        note=f"Con n={n:,} una correlación supera el 5 % ordinario en |r| > {r_crit:.3f}, "
             f"que no significa nada solo: se corrige por Benjamini-Hochberg sobre las "
             f"{len(is_metrics)} métricas IS de cada resultado. Spearman manda; si discrepa "
             f"de Pearson, sospecha de outliers."),
        envelope.tab("persistence", "¿Una métrica conserva su valor fuera de muestra?", [
            blocks.table("Misma métrica, dentro contra fuera", persist,
                         "OOS/IS por debajo de 1 es decaimiento.")])]
    tabs += [envelope.tab(t, f"¿Qué métrica IS predice {t}?", [
        blocks.table("Ranking de predictores", pd.DataFrame(
            [[r["metric"], r["spearman"], r["pearson"], r["p"], r["metric"] in found[t]]
             for r in rows], columns=["métrica IS", "ρ", "r", "p", "BH"]),
            f"{len(found[t])} de {len(rows)} sobreviven. Un ρ en torno a 0,2 mueve las "
            f"probabilidades, no decide el resultado.")]) for t, rows in ranked.items()]
    return envelope.envelope(
        MODULE, None, None, {"targets": list(ranked)}, started, tabs,
        warnings=[{"code": "busqueda", "state": "info",
                   "text": "Estas estrategias salieron de una búsqueda y ninguna se "
                           "seleccionó por su resultado fuera de muestra: esto es la relación "
                           "incondicional entre una métrica IS y lo que pasó después, no un "
                           "ranking de estrategias."}])
