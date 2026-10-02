#!/usr/bin/env python3
"""Judge every strategy in a databank on how much of its in-sample edge survived out of sample."""

import argparse
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd

from core import sqxfile, sqxstats
from core.paths import MASTER, databank_dir, report_dir, worker_dir
from core.study import blocks, output, result as envelope, verdicts
from core.study.render import markdown
from core.surface import dedupe
from studies.screening.analysis import decay
from studies.screening.decay import one

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


def curves(folder: Path, built: Path | None, split: str, strategy: str | None) -> dict:
    """Each strategy's daily equity, read from its .sqx, with its build's IS when given.

    Args:
        folder: The databank's folder on the install.
        built: The build's databank folder, or None when this one holds IS too.
        split: First out-of-sample day, YYYY-MM-DD.
        strategy: One name alone, or None for every .sqx of the databank.

    Returns:
        name -> curve, only names that also sit in the build when `built` is given.
    """
    files = [folder / f"{strategy}.sqx"] if strategy else sorted(folder.glob("*.sqx"))
    got = {f.stem: sqxstats.equity(f) for f in files}
    if built is None:
        return got
    return {n: joined(sqxstats.equity(built / f"{n}.sqx"), c, split)
            for n, c in got.items() if (built / f"{n}.sqx").is_file()}


def write_one(out: Path, folder: Path, strategy: str, curve: pd.Series, split: str,
              end: str) -> Path:
    """One strategy's run: only `estrategias/<name>.json` and its page, the way crossTF's
    `--strategy` does — `decay.json`, `verdict.csv` and the manifest are the population's,
    and rewriting them from one strategy would leave the databank tab with that one alone.

    Args:
        out: The module's report folder.
        folder: The databank's folder, for the strategy's identity.
        strategy: Its name.
        curve: Its daily equity, IS and OOS.
        split, end: The OOS stretch, YYYY-MM-DD.

    Returns:
        The JSON's path.
    """
    got = one.run(strategy, {"curve": curve,
                             "identity": sqxfile.identity(folder / f"{strategy}.sqx")},
                  {"split": split, "end": end})
    print(markdown.render(got, f"Decaimiento — {strategy}"))
    return output.member(out, got, f"Decaimiento — {strategy}")


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
    ap.add_argument("--strategy", help="one strategy alone, as the databank names it: writes "
                    "only estrategias/<name>.json, never the population's files")
    a = ap.parse_args()

    started = time.time()
    install = worker_dir(a.role) if a.role else MASTER
    folder = databank_dir(a.project, a.databank, install)
    built = databank_dir(a.project, a.is_databank, install) if a.is_databank else None
    found = curves(folder, built, a.split, a.strategy)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "decay"
    if a.strategy:
        if a.strategy not in found:
            raise SystemExit(f"{a.strategy} no está en {built} para leer su IS")
        print(f"-> {write_one(out, folder, a.strategy, found[a.strategy], a.split, a.end)}")
        return
    clone = dedupe.curve_duplicates(found)
    dropped = int(clone.sum())
    kept = {name: c for name, c in found.items() if not clone[name]}
    rows = decay.table(kept, a.split, a.end)
    identity = {n: sqxfile.identity(folder / f"{n}.sqx") for n in found}
    source = {"split": a.split, "end": a.end, "duplicates_dropped": dropped}
    got = result(rows, source, started)
    title = f"Decaimiento — {a.project} / {a.databank}"
    output.population(out, "decay", got, title)
    table = rows[COLUMNS].rename(columns={"name": "strategy"})
    table.insert(1, "identity", table["strategy"].map(identity))
    verdicts.write(out, table, folder, " ".join(sys.argv), [])
    print(markdown.render(got, title))
    print(f"{len(rows)} estrategias ({dropped} duplicadas de trades idénticos descartadas "
          f"de {len(found)}) → {out}")


if __name__ == "__main__":
    main()
