#!/usr/bin/env python3
"""Sweep in-sample filters against out-of-sample outcomes, as one result and its page."""

import argparse
import time
from datetime import date

import pandas as pd

from core import manifest
from core.paths import metrics_export, report_dir
from core.study import blocks, output, result as envelope
from core.study.render import markdown
from tasks.analysis import correlations, improvement, metrics

TARGETS = ["Sharpe Ratio (OOS)", "Ret/DD Ratio (OOS)"]
MODULE = "tasks.reports.filters"


def tab(target: str, base: dict, rows: list[dict], found: set[str], top: int) -> dict:
    """What each candidate filter buys on one out-of-sample outcome.

    Args:
        target: Full name of the out-of-sample column.
        base: Unfiltered outcome from analysis.improvement.outcome.
        rows: Rows from the sweep for this target, best first.
        found: Labels surviving Benjamini-Hochberg for this target.
        top: How many filters to list.

    Returns:
        One tab: the best filters as bars of Δ median, coloured by whether they survive the
        correction, and their table with the bootstrap interval on Δ.
    """
    level = improvement.breakeven(target)
    survived = [r for r in rows if r["metric"] in found and r["d_median"] > 0]
    shown = rows[:top]
    best = survived[0] if survived else None
    return envelope.tab(target, target, [
        {"kind": "bars", "title": f"Δ mediana de {target}, los {len(shown)} mejores filtros",
         "unit": "", "reference": 0.0,
         "items": [{"label": r["metric"], "value": r["d_median"],
                    "error": [r["d_median_lo"], r["d_median_hi"]],
                    "state": "pass" if r["metric"] in found and r["d_median"] > 0 else "none"}
                   for r in shown],
         "note": "En verde, los que mejoran la mediana y sobreviven Benjamini-Hochberg; la "
                 "barra fina es el intervalo del bootstrap sobre Δ."},
        blocks.table("Los mejores filtros", pd.DataFrame(
            [[r["metric"], r["n"], r["median"], r["d_median"], r["d_median_lo"],
              r["d_median_hi"], 100 * r["hit"], 100 * r["d_hit"], r["p"],
              r["metric"] in found] for r in shown],
            columns=["filtro", "quedan", "mediana", "Δ mediana", "Δ IC desde", "Δ IC hasta",
                     "% por encima", "Δ pp", "p", "BH"]),
            f"Mejor filtro superviviente: {best['metric']}, deja {best['n']:,} con mediana "
            f"{best['median']:.3f} ({best['d_median']:+.3f})." if best else
            "Ningún filtro mejora la mediana y sobrevive la corrección.")],
        note=f"Sin filtrar: {base['n']:,} estrategias · mediana {base['median']:.3f} · "
             f"{100 * base['hit']:.1f} % por encima de {level:g}. {len(survived)} de "
             f"{len(rows)} filtros juzgados mejoran la mediana y sobreviven la corrección.")


def main() -> None:
    """Read a databank's current metrics export and write the filter sweep for it."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--target", action="append", default=None, help="repeatable; OOS column")
    ap.add_argument("--top", type=int, default=15, help="filters listed per outcome")
    a = ap.parse_args()

    started = time.time()
    src = metrics_export(a.project, a.databank)
    columns, names = metrics.load(src / "metrics.csv")
    is_metrics = metrics.measured(columns, metrics.IS)
    targets = [t for t in (a.target or TARGETS) if t in metrics.measured(columns, metrics.OOS)]
    tried = len(improvement.candidates(is_metrics))
    tabs = []
    for target in targets:
        rows = improvement.sweep(columns, is_metrics, target)
        base = improvement.outcome(columns[target], improvement.breakeven(target))
        tabs.append(tab(target, base, rows, correlations.discoveries(rows), a.top))
    got = envelope.envelope(
        MODULE, None, None, {"targets": targets, "top": a.top}, started, tabs,
        warnings=[{"code": "busqueda", "state": "info",
                   "text": f"{tried} filtros candidatos sobre {len(is_metrics)} métricas, "
                           f"cortadas al {'/'.join(str(c) for c in improvement.CUTS)} % por "
                           f"los dos lados; sólo se juzgan los que dejan al menos "
                           f"{improvement.MIN_SURVIVORS} estrategias, y se corrigen juntos por "
                           f"Benjamini-Hochberg. El p del bootstrap no baja de "
                           f"1/{improvement.DRAWS}: ahí lee el intervalo."}])
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "filters"
    title = f"{a.project} / {a.databank} — qué compra un filtro"
    output.population(out, "filters", got, title, f"{len(names):,} estrategias.")
    manifest.write(out, {"input": str((src / "metrics.csv").resolve())},
                   f"filters.py --project {a.project} --databank {a.databank}",
                   {"strategies": len(names), "candidates": tried, "targets": targets})
    print(markdown.render(got, title))
    print(f"  {out / 'filters.md'}")


if __name__ == "__main__":
    main()
