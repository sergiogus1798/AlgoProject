#!/usr/bin/env python3
"""Judge every strategy in a databank on how much of its in-sample edge survived out of sample."""

import argparse
import sys
import time
from datetime import date

import pandas as pd

from core import sqxfile, sqxstats
from core.paths import MASTER, databank_dir, report_dir, worker_dir
from core.study import blocks, output, result as envelope, verdicts
from core.study.render import markdown
from core.surface import dedupe
from studies.screening.analysis import decay

MODULE = "studies.screening.decay.report"
COLUMNS = ["name", "sharpe_is", "sharpe_oos", "retention", "t", "years_positive",
           "worst_year", "concentration", "net_profit_oos", "verdict"]
STATE = {"MANTENER": "pass", "DUDOSA": "watch", "DESCARTAR": "fail"}


def result(rows: pd.DataFrame, source: dict, started: float) -> dict:
    """The databank's decay as one result: the counts, retention, templates, the keepers.

    Args:
        rows: The table from analysis.decay.
        source: What was analysed, for the notes.
        started: When the computation began.

    Returns:
        The contract dict. Counts are per verdict and per template — the leading field of a
        strategy's name is the build task that produced it — and nothing is averaged across
        templates.
    """
    counts = rows.verdict.value_counts()
    kept = rows[rows.verdict == "MANTENER"]
    by = rows.assign(plantilla=rows.name.str.split(".").str[0]).groupby("plantilla")
    per_template = pd.DataFrame({"n": by.size(),
                                 "mantener": by.verdict.apply(lambda v: (v == "MANTENER").sum()),
                                 "descartar": by.verdict.apply(lambda v: (v == "DESCARTAR").sum())}
                                ).reset_index()
    return envelope.envelope(
        MODULE, None, None, {"split": source["split"], "end": source["end"]}, started,
        [envelope.tab("verdicts", "Veredicto", [
            {"kind": "bars", "title": "Estrategias por veredicto", "unit": "estrategias",
             "reference": None,
             "items": [{"label": k, "value": int(n), "error": None,
                        "state": STATE.get(k, "info")} for k, n in counts.items()]},
            blocks.table("Retención del Sharpe", pd.DataFrame(
                [["mediana", rows.retention.median()], ["p90", rows.retention.quantile(.9)],
                 ["máximo", rows.retention.max()], ["t máximo", rows.t.max()]],
                columns=["", "valor"]),
                "Con t por debajo de 2 el Sharpe fuera de muestra no se distingue de cero."),
            blocks.table("Por plantilla", per_template),
            blocks.table("Las que pasan todo", kept[COLUMNS])],
            note=f"IS hasta {source['split']} · OOS {source['split']} → {source['end']} · "
                 f"{source['duplicates_dropped']} duplicadas (misma curva diaria de P&L bajo "
                 f"otro nombre) descartadas antes de contar.")],
        blocks.verdict(f"{int(counts.get('MANTENER', 0))} de {len(rows)}",
                       "pass" if counts.get("MANTENER", 0) else "fail",
                       "Cuánto del filo dentro de muestra sobrevivió fuera, y si lo que queda "
                       "bate a su propio error estándar."))


def joined(before: pd.Series, after: pd.Series, split: str) -> pd.Series:
    """One cumulative daily P&L from a build's curve up to `split` and its retest's from it.

    Args:
        before, after: Daily cumulative P&L of the build and of its out-of-sample retest,
            each starting from its own capital.
        split: First out-of-sample day, YYYY-MM-DD.

    Returns:
        Their daily changes glued at `split` and summed again: `analysis.decay` reads
        `diff()`, so two curves that each restart at the capital must not meet as a jump.
    """
    cut = pd.Timestamp(split)
    daily = pd.concat([before.diff().dropna()[lambda s: s.index < cut],
                       after.diff().dropna()[lambda s: s.index >= cut]])
    return daily.cumsum()


def main() -> None:
    """Read a databank's .sqx straight from disk and write one dated decay report."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--split", required=True, help="first out-of-sample day, YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="last day to consider, YYYY-MM-DD")
    ap.add_argument("--role", help="read a worker's install instead of the master")
    ap.add_argument("--is-databank", help="the build this databank retested out of sample: "
                    "its curve before --split, paired by name (a workflow keeps IS and OOS apart)")
    a = ap.parse_args()

    started = time.time()
    install = worker_dir(a.role) if a.role else MASTER
    folder = databank_dir(a.project, a.databank, install)
    files = sorted(folder.glob("*.sqx"))
    curves = {f.stem: sqxstats.equity(f) for f in files}
    if a.is_databank:
        built = databank_dir(a.project, a.is_databank, install)
        curves = {n: joined(sqxstats.equity(built / f"{n}.sqx"), c, a.split)
                  for n, c in curves.items() if (built / f"{n}.sqx").is_file()}
        files = [f for f in files if f.stem in curves]
    clone = dedupe.curve_duplicates(curves)
    dropped = int(clone.sum())
    curves = {name: c for name, c in curves.items() if not clone[name]}
    rows = decay.table(curves, a.split, a.end)
    identity = {f.stem: sqxfile.identity(f) for f in files}
    source = {"split": a.split, "end": a.end, "duplicates_dropped": dropped}
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "decay"
    got = result(rows, source, started)
    title = f"Decaimiento — {a.project} / {a.databank}"
    output.population(out, "decay", got, title)
    table = rows[COLUMNS].rename(columns={"name": "strategy"})
    table.insert(1, "identity", table["strategy"].map(identity))
    verdicts.write(out, table, folder, " ".join(sys.argv), [])
    print(markdown.render(got, title))
    print(f"{len(rows)} estrategias ({dropped} duplicadas de trades idénticos descartadas "
          f"de {len(files)}) → {out}")


if __name__ == "__main__":
    main()
