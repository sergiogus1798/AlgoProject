#!/usr/bin/env python3
"""Export everything a Walk-Forward Matrix cross-check stored: cells, steps, parameters, trades."""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from core import exportdrv, manifest, trades, wfmatrix, wftrades
from core.paths import MASTER, databank_dir, export_dir
from sqx.export.export_trades import stage

KEYS = ["strategy", "result", "oos_pct", "runs"]


def tables(project: str, databank: str) -> dict[str, pd.DataFrame]:
    """Read the matrix out of every .sqx in a databank, without SQX running.

    Args:
        project: Project name on the master.
        databank: Databank the WFM cross-check wrote into.

    Returns:
        `cells` (one row per matrix cell), `steps` (one per walk-forward step of every
        cell) and `params` (long form: one row per step and parameter). Each statistic
        appears twice, `is_` from the optimisation window and `oos_` from the run window.
        A strategy the databank holds without a matrix result was never cross-checked with
        WFM and is skipped -- a stripped copy carries the rules and no cross-check at all.
    """
    cells, steps = [], []
    for f in sorted(databank_dir(project, databank, MASTER).glob("*.sqx")):
        node = wfmatrix.matrix(f)
        if node is None:
            continue
        cells += [{"strategy": f.stem} | c for c in wfmatrix.cells(node)]
        steps += [{"strategy": f.stem} | s for s in wfmatrix.periods(node)]
    params = [{**{k: s[k] for k in KEYS}, "index": s["index"], "parameter": k, "value": v}
              for s in steps for k, v in s["params"].items()]
    frame = lambda rows: pd.DataFrame(rows).drop(columns="params", errors="ignore")
    return {"cells": frame(cells), "steps": frame(steps), "params": pd.DataFrame(params)}


def split(raw_dir: Path, steps: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Fan each strategy's data=all CSV out into one file per matrix cell, step-tagged.

    Args:
        raw_dir: Where orderstocsv wrote its files, one per strategy.
        steps: The `steps` table, used both for the run windows and for the stored counts.
        out_dir: Root to write `<strategy>/<cell>.csv` under.

    Returns:
        The verification table: one row per cell and step with the trades assigned against
        the trades SQX stored for it. Any non-zero difference invalidates the split, so it
        is written out rather than asserted away.
    """
    checked = []
    for f in sorted(raw_dir.glob("*.csv")):
        mine = steps[steps["strategy"] == f.stem]
        if mine.empty:
            continue
        dest = out_dir / f.stem
        dest.mkdir(parents=True, exist_ok=True)
        blocks = wftrades.chunks(trades.read(f))[1:]
        for block, cell in zip(blocks, mine["result"].unique()):
            rows = mine[mine["result"] == cell].to_dict("records")
            tagged = wftrades.label(block, rows)
            tagged.to_csv(dest / f"{cell.replace(':', '').replace(' ', '_')}.csv",
                          sep=";", index=False, date_format=trades.TIME)
            checked.append(wftrades.check(tagged, rows).assign(strategy=f.stem, result=cell))
    return pd.concat(checked, ignore_index=True)


def main() -> None:
    """Export one WFM databank: the matrix tables, then the trades split per cell and step."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank the WFM retest wrote into")
    a = ap.parse_args()

    out = export_dir(a.project, a.databank, date.today().isoformat()) / "wfm"
    out.mkdir(parents=True, exist_ok=True)
    written = tables(a.project, a.databank)
    for name, table in written.items():
        table.to_csv(out / f"{name}.csv", index=False)
        print(f"{name + '.csv':16} {len(table):>7} rows  {len(table.columns):>4} columns")

    staged = stage(a.project, a.databank, out / "strategies")
    exportdrv.trades(out / "strategies", out / "raw", data="all")
    checked = split(out / "raw", written["steps"], out / "trades")
    checked.to_csv(out / "check.csv", index=False)
    off = int((checked["assigned"] - checked["stored"]).abs().sum())
    print(f"trades           {int(checked['assigned'].sum()):>7} assigned, {off} unaccounted for")

    manifest.write(out,
                   {"install": str(MASTER), "project": a.project, "databank": a.databank,
                    "data": "all"},
                   f"export_wfm.py --project {a.project} --databank {a.databank}",
                   {"strategies": len(staged), "unaccounted_trades": off,
                    **{f"{k}.csv": len(v) for k, v in written.items()}})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
