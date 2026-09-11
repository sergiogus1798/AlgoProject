#!/usr/bin/env python3
"""Judge every strategy in a databank on how much of its in-sample edge survived out of sample."""

import argparse
from datetime import date

import pandas as pd

from core import manifest, sqxstats
from core.paths import databank_dir, report_dir
from tasks.analysis import decay

COLUMNS = ["name", "sharpe_is", "sharpe_oos", "retention", "t", "years_positive",
           "worst_year", "concentration", "net_profit_oos", "verdict"]


def render(source: dict, rows: pd.DataFrame) -> str:
    """The written summary that goes beside the CSV.

    Args:
        source: What was analysed and when, for the header.
        rows: The table from analysis.decay.

    Returns:
        Markdown. The counts are per verdict and per template — the leading field of a
        strategy's name is the build task that produced it — and nothing is averaged
        across templates.
    """
    counts = rows.verdict.value_counts()
    lines = [f"# Decaimiento — {source['project']} / {source['databank']}", "",
             f"{len(rows)} estrategias · IS hasta {source['split']} · "
             f"OOS {source['split']} → {source['end']} · informe {source['reported']}", "",
             "## Veredicto", "", "| veredicto | n |", "|---|---|"]
    lines += [f"| {name} | {n} |" for name, n in counts.items()]

    keep = rows[rows.verdict == "MANTENER"]
    lines += ["", "## Retención del Sharpe", "",
              f"Mediana {rows.retention.median():.0%} · p90 {rows.retention.quantile(.9):.0%} · "
              f"máximo {rows.retention.max():.0%}", "",
              f"Ninguna estrategia con t ≥ 2 (el máximo es {rows.t.max():.2f}): "
              "el Sharpe fuera de muestra no se distingue de cero en ninguna.", "",
              "## Por plantilla", "", "| plantilla | n | mantener | descartar |", "|---|---|---|---|"]
    rows = rows.assign(template=rows.name.str.split(".").str[0])
    for name, group in rows.groupby("template"):
        lines.append(f"| {name} | {len(group)} | {(group.verdict == 'MANTENER').sum()} | "
                     f"{(group.verdict == 'DESCARTAR').sum()} |")

    lines += ["", "## Las que pasan todo", "",
              "| estrategia | Sharpe IS | Sharpe OOS | retiene | t | años+ | concentr. |",
              "|---|---|---|---|---|---|---|"]
    lines += [f"| {r.name_} | {r.sharpe_is:.2f} | {r.sharpe_oos:.2f} | {r.retention:.0%} | "
              f"{r.t:.2f} | {r.years_positive} | {r.concentration:.0%} |"
              for r in keep.rename(columns={"name": "name_"}).itertuples()]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Read a databank's .sqx straight from disk and write one dated decay report."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--split", required=True, help="first out-of-sample day, YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="last day to consider, YYYY-MM-DD")
    a = ap.parse_args()

    files = sorted(databank_dir(a.project, a.databank).glob("*.sqx"))
    curves = {f.stem: sqxstats.equity(f) for f in files}
    rows = decay.table(curves, a.split, a.end)

    source = {"project": a.project, "databank": a.databank, "split": a.split, "end": a.end,
              "reported": date.today().isoformat(), "code_version": manifest.code_version()}
    out = report_dir(a.project, a.databank, source["reported"])
    out.mkdir(parents=True, exist_ok=True)
    rows[COLUMNS].to_csv(out / "decay.csv", index=False)
    (out / "decay.md").write_text(render(source, rows), encoding="utf-8")
    manifest.write(out, source,
                   f"decay.py --project {a.project} --databank {a.databank} "
                   f"--split {a.split} --end {a.end}",
                   {"strategies": len(rows),
                    **rows.verdict.value_counts().to_dict()})
    print(f"{len(rows)} estrategias → {out}")
    print(rows.verdict.value_counts().to_string())


if __name__ == "__main__":
    main()
