#!/usr/bin/env python3
"""Check whether one databank's conclusions hold on other, independently generated databanks."""

import argparse
import time
from datetime import date

import pandas as pd

from core import manifest
from core.paths import metrics_export, report_dir
from core.study import blocks, output, result as envelope
from core.study.render import markdown
from tasks.analysis import improvement, metrics, replication

MODULE = "tasks.reports.compare"
TARGETS = ["Sharpe Ratio (OOS)", "Ret/DD Ratio (OOS)"]
FILTERS = 6
RESTRICTED = 0.7


def load(project: str, databanks: list[str]) -> dict:
    """Read the current metrics export of every databank being compared.

    Args:
        project: Project name.
        databanks: Databank names, the reference first.

    Returns:
        One entry per databank with its columns, strategy count and export date.
    """
    out = {}
    for databank in databanks:
        src = metrics_export(project, databank)
        columns, names = metrics.load(src / "metrics.csv")
        out[databank] = {"columns": columns, "n": len(names),
                         "exported": manifest.read(src)["date"]}
    return out


def outcomes(samples: dict, reference: str, target: str) -> pd.DataFrame:
    """Where each sample ended up out of sample, against the reference.

    Args:
        samples: load() output.
        reference: Name of the databank the conclusions came from.
        target: Full name of the out-of-sample column.

    Returns:
        One row per databank: its count, median, hit rate and the gap to the reference
        with its interval.
    """
    level = improvement.breakeven(target)
    base = samples[reference]["columns"][target]
    rows = []
    for name, s in samples.items():
        got = improvement.outcome(s["columns"][target], level)
        gap = replication.hit_gap(base, s["columns"][target], level)
        own = name == reference
        rows.append([name, got["n"], got["median"], 100 * got["hit"],
                     None if own else 100 * gap["gap"], None if own else 100 * gap["lo"],
                     None if own else 100 * gap["hi"]])
    return pd.DataFrame(rows, columns=["databank", "estrategias", "mediana", "% por encima",
                                       "Δ pp", "Δ IC desde", "Δ IC hasta"])


def best_filters(ref: dict, target: str, is_metrics: list[str]) -> list[dict]:
    """The reference's best filters, one per metric, strongest first."""
    ranked = sorted(improvement.candidates(is_metrics),
                    key=lambda c: -replication.carried(ref, ref, c, target)["predicted"])
    best, seen = [], set()
    for candidate in ranked:
        if candidate["metric"] not in seen:
            seen.add(candidate["metric"])
            best.append(candidate)
        if len(best) == FILTERS:
            break
    return best


def replicated(samples: dict, reference: str, target: str, is_metrics: list[str]) -> list[dict]:
    """Whether the reference's best filters deliver what they promised on each other sample.

    Args:
        samples: load() output.
        reference: Name of the databank the conclusions came from.
        target: Full name of the out-of-sample column.
        is_metrics: In-sample metrics present in every sample.

    Returns:
        One table block per checked sample.
    """
    ref = samples[reference]["columns"]
    best = best_filters(ref, target, is_metrics)
    out = []
    for name, s in samples.items():
        if name == reference:
            continue
        rows = []
        for candidate in best:
            got = replication.carried(ref, s["columns"], candidate, target)
            rows.append([improvement.label(candidate), 100 * got["predicted"],
                         100 * got["share"], got["n"], 100 * got["observed"],
                         100 * (got["observed"] - got["predicted"]), 100 * got["lo"],
                         100 * got["hi"]])
        out.append(blocks.table(f"{name}: los umbrales de la referencia aplicados", pd.DataFrame(
            rows, columns=["filtro", "% previsto", "% de la muestra que pasa", "n",
                           "% observado", "Δ", "Δ IC desde", "Δ IC hasta"]),
            "Previsto es lo que el filtro dio en la referencia. Si casi toda la muestra ya "
            "pasa el umbral, esa muestra se construyó para cumplirlo."))
    return out


def agreement(samples: dict, reference: str, target: str, is_metrics: list[str]) -> dict:
    """Whether the samples rank the in-sample predictors the same way, as one table."""
    ref = replication.predictors(samples[reference]["columns"], target, is_metrics)
    rows = []
    for name, s in samples.items():
        if name == reference:
            continue
        here = replication.predictors(s["columns"], target, is_metrics)
        narrowed = [m for m in is_metrics
                    if replication.restriction(samples[reference]["columns"][m],
                                               s["columns"][m]) < RESTRICTED]
        rows.append([name, replication.stability(ref, here), ", ".join(narrowed[:4])])
    return blocks.table("¿Coinciden en qué lo predice?", pd.DataFrame(
        rows, columns=["databank", "ρ del ranking con la referencia",
                       "seleccionada sobre (correlación atenuada por construcción)"]))


def main() -> None:
    """Compare the current metrics exports of several databanks of one project."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--reference", required=True, help="databank the conclusions came from")
    ap.add_argument("--databank", action="append", required=True, help="repeatable; to check")
    ap.add_argument("--target", action="append", default=None)
    a = ap.parse_args()

    started = time.time()
    names = [a.reference] + [d for d in a.databank if d != a.reference]
    samples = load(a.project, names)
    common = sorted(set.intersection(*(set(metrics.measured(s["columns"], metrics.IS))
                                       for s in samples.values())))
    targets = [t for t in (a.target or TARGETS)
               if all(t in s["columns"] for s in samples.values())]
    tabs = [envelope.tab(t, t, [blocks.table("Dónde acabó cada muestra",
                                             outcomes(samples, a.reference, t)),
                                *replicated(samples, a.reference, t, common),
                                agreement(samples, a.reference, t, common)])
            for t in targets]
    got = envelope.envelope(
        MODULE, None, None, {"reference": a.reference, "databanks": names}, started, tabs,
        warnings=[{"code": "resultado", "state": "info",
                   "text": "Cada muestra es su propia generación: lo que significa algo es el "
                           "resultado fuera de muestra. Una correlación medida dentro de una "
                           "muestra seleccionada sobre esa métrica está atenuada por "
                           "construcción."}])
    out = report_dir(a.project, "_comparison", date.today().isoformat()) / "replication"
    title = f"{a.project} — ¿se sostienen las conclusiones en otras muestras?"
    output.population(out, "replication", got, title,
                      f"Referencia {a.reference}; contra " + ", ".join(names[1:]) + ".")
    manifest.write(out, {"project": a.project, "reference": a.reference, "databanks": names,
                         "exported": {n: s["exported"] for n, s in samples.items()}},
                   f"compare.py --project {a.project} --reference {a.reference} "
                   + " ".join(f"--databank {n}" for n in names[1:]),
                   {n: s["n"] for n, s in samples.items()})
    print(markdown.render(got, title))
    print(f"  {out / 'replication.md'}")


if __name__ == "__main__":
    main()
