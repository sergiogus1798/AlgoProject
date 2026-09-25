#!/usr/bin/env python3
"""The IS/OOS study of one databank, as one result, its page, and the interactive explorer."""

import argparse
import json
import time
from datetime import date
from pathlib import Path

import pandas as pd

from core import manifest
from core.paths import metrics_export, report_dir
from core.study import blocks, output, result as envelope
from core.study.render import markdown
from tasks.analysis import correlations, metrics

MODULE = "tasks.reports.is_oos"
TEMPLATE = Path(__file__).with_name("panel.html")
TARGETS = ["Profit factor (OOS)", "Sharpe Ratio (OOS)", "Ret/DD Ratio (OOS)", "Net profit (OOS)"]


def payload(columns: dict, names: list[str], source: dict,
            is_metrics: list[str], oos_metrics: list[str]) -> dict:
    """Everything the interactive explorer needs, ready to embed.

    Args:
        columns: Numeric columns from analysis.metrics.load.
        names: Strategy names in row order.
        source: What produced the export, shown in the page header.
        is_metrics, oos_metrics: Full column names, in menu order.

    Returns:
        A JSON-serialisable dict. The page carries every strategy because it recomputes
        its statistics whenever a filter changes; five decimals keeps that a few megabytes.
    """
    return {"source": source, "names": names, "is": is_metrics, "oos": oos_metrics,
            "data": {k: [round(float(v), 5) for v in col] for k, col in columns.items()}}


def result(columns: dict, n: int, is_metrics: list[str], oos_metrics: list[str],
           started: float) -> dict:
    """What the IS metrics say about the OOS outcomes, over the whole population.

    Args:
        columns: Numeric columns from analysis.metrics.load.
        n: Strategies in the export.
        is_metrics, oos_metrics: The measured columns of each side.
        started: When the computation began.

    Returns:
        The contract dict: persistence, the IS × OOS correlation map, and one ranking per
        outcome with the Benjamini-Hochberg survivors marked.
    """
    ranked = {t: correlations.predictors(columns, t, is_metrics)
              for t in TARGETS if t in oos_metrics}
    found = {t: correlations.discoveries(rows) for t, rows in ranked.items()}
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


def main() -> None:
    """Read a databank's current metrics export and write one dated report from it."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    a = ap.parse_args()

    started = time.time()
    src = metrics_export(a.project, a.databank)
    columns, names = metrics.load(src / "metrics.csv")
    made = manifest.read(src)
    source = {"project": a.project, "databank": a.databank, "view": made["source"]["view"],
              "exported": made["date"], "reported": date.today().isoformat(),
              "code_version": manifest.code_version()}
    is_metrics = metrics.measured(columns, metrics.IS)
    oos_metrics = metrics.measured(columns, metrics.OOS)
    got = result(columns, len(names), is_metrics, oos_metrics, started)
    out = report_dir(a.project, a.databank, source["reported"]) / "isOos"
    title = f"{a.project} / {a.databank} — dentro de muestra contra fuera"
    output.population(out, "isOos", got, title,
                      f"{len(names):,} estrategias · vista «{source['view']}» · exportado "
                      f"{source['exported']}.")
    # The explorer recomputes every statistic in the browser as a filter changes; it stays
    # until the window has an IS/OOS zone that filters, and is the last page that needs one.
    (out / "explorer.html").write_text(
        TEMPLATE.read_text(encoding="utf-8").replace(
            "__PAYLOAD__",
            json.dumps(payload(columns, names, source, is_metrics, oos_metrics))),
        encoding="utf-8")
    manifest.write(out, dict(source, input=str((src / "metrics.csv").resolve())),
                   f"is_oos.py --project {a.project} --databank {a.databank}",
                   {"strategies": len(names), "is_metrics": len(is_metrics),
                    "oos_metrics": len(oos_metrics)})
    print(markdown.render(got, title))
    print(f"  {out / 'isOos.html'}\n  {out / 'explorer.html'}")


if __name__ == "__main__":
    main()
