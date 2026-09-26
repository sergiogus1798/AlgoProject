#!/usr/bin/env python3
"""Export everything a Walk-Forward Matrix cross-check stored: cells, steps, parameters, trades. Parquet."""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

import shutil

from core import exportdrv, manifest, sqxfile, trades, tradestore, wfmatrix, wftrades
from core.paths import MASTER, databank_dir, export_dir, worker_dir
from sqx.export.export_trades import stage

KEYS = ["strategy", "result", "oos_pct", "runs"]


def tables(project: str, databank: str, install: Path = MASTER) -> dict[str, pd.DataFrame]:
    """Read the matrix out of every .sqx in a databank, without SQX running.

    Args:
        project: Project name.
        databank: Databank the WFM cross-check wrote into.
        install: Which install holds the project; a worker's, since the runs moved there.

    Returns:
        `cells` (one row per matrix cell), `steps` (one per walk-forward step of every
        cell), `params` (long form: one row per step and parameter) and `status` (one per
        strategy: whether SQX marked it failed, and why — it is kept, never deleted). A cell's statistics
        come three times -- `is_`, `oos_`, `all_`; a step's twice, `is_` from its
        optimisation window and `oos_` from its run window.
        A strategy the databank holds without a matrix result was never cross-checked with
        WFM and is skipped -- a stripped copy carries the rules and no cross-check at all.
    """
    cells, steps, status = [], [], []
    for f in sorted(databank_dir(project, databank, install).glob("*.sqx")):
        node = wfmatrix.matrix(f)
        if node is None:
            continue
        note = sqxfile.sqx_filter(f)
        status.append({"strategy": f.stem, "sqx_filter": note,
                       "sqx_failed": note is not None and note != "Passed"})
        cells += [{"strategy": f.stem} | c for c in wfmatrix.cells(node, wfmatrix.results(f))]
        steps += [{"strategy": f.stem} | s for s in wfmatrix.periods(node)]
    params = [{**{k: s[k] for k in KEYS}, "index": s["index"], "parameter": k, "value": v}
              for s in steps for k, v in s["params"].items()]
    frame = lambda rows: pd.DataFrame(rows).drop(columns="params", errors="ignore")
    # Wide: one row per step, one column per parameter -- the shape every reader wants,
    # written once instead of pivoted on every read.
    # A step holds one value per parameter, so nothing is averaged: `first` takes it as SQX
    # wrote it. The values arrive as text -- 🔬 2026-09-25, pandas 2.3 refuses the old
    # implicit mean over them -- and a column becomes numeric only when every value is.
    wide = (pd.DataFrame(params).pivot_table(index=[*KEYS, "index"], columns="parameter",
                                             values="value", aggfunc="first").reset_index())
    wide.columns.name = None
    for name in wide.columns.difference([*KEYS, "index"]):
        number = pd.to_numeric(wide[name], errors="coerce")
        if number.notna().sum() == wide[name].notna().sum():
            wide[name] = number
    return {"cells": frame(cells), "steps": frame(steps), "params": wide,
            "status": pd.DataFrame(status)}


def split(raw_dir: Path, steps: pd.DataFrame, out: Path) -> pd.DataFrame:
    """Tag every strategy's data=all trades with their matrix cell and step, into one Parquet.

    Args:
        raw_dir: Where orderstocsv wrote its files, one per strategy.
        steps: The `steps` table, used both for the run windows and for the stored counts.
        out: The `trades.parquet` to write: tradestore's columns plus `result` (the cell),
            `period` (the step) and `sample`.

    Returns:
        The verification table: one row per cell and step with the trades assigned against
        the trades SQX stored for it. Any non-zero difference invalidates the split, so it
        is written out rather than asserted away. Rows with `period == -1` -- trades before
        a cell's first run window -- are in the Parquet but outside this table: 2026-09-10,
        88,721 rows against 65,161 assigned, and both numbers are right.
    """
    checked, frames = [], []
    for f in sorted(raw_dir.glob("*.csv")):
        mine = steps[steps["strategy"] == f.stem]
        if mine.empty:
            continue
        blocks = wftrades.chunks(trades.read(f))[1:]
        for block, cell in zip(blocks, mine["result"].unique()):
            rows = mine[mine["result"] == cell].to_dict("records")
            tagged = wftrades.label(block, rows)
            keep = tradestore.KEEP + (["Ticket"] if not tradestore.ordered(tagged) else [])
            frames.append(tagged[keep + ["period", "sample"]]
                          .assign(strategy=f.stem, result=cell))
            checked.append(wftrades.check(tagged, rows).assign(strategy=f.stem, result=cell))
    packed = pd.concat(frames, ignore_index=True)
    for c in (*tradestore.CATEGORICAL, "result", "sample"):
        if c in packed:
            packed[c] = packed[c].astype("category")
    packed.to_parquet(out, compression="zstd", index=False)
    return pd.concat(checked, ignore_index=True)


def main() -> None:
    """Export one WFM databank: the matrix tables, then the trades split per cell and step."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank the WFM retest wrote into")
    ap.add_argument("--role", help="worker role holding the project; the master if absent")
    a = ap.parse_args()

    install = worker_dir(a.role) if a.role else MASTER
    out = export_dir(a.project, a.databank, date.today().isoformat()) / "wfm"
    out.mkdir(parents=True, exist_ok=True)
    written = tables(a.project, a.databank, install)
    for name, table in written.items():
        table.to_parquet(out / f"{name}.parquet", compression="zstd", index=False)
        print(f"{name + '.parquet':16} {len(table):>7} rows  {len(table.columns):>4} columns")

    staged = stage(a.project, a.databank, out / "strategies", install=install)
    exportdrv.trades(out / "strategies", out / "raw", data="all")
    checked = split(out / "raw", written["steps"], out / "trades.parquet")
    checked.to_parquet(out / "check.parquet", index=False)
    off = int((checked["assigned"] - checked["stored"]).abs().sum())
    print(f"trades           {int(checked['assigned'].sum()):>7} assigned, {off} unaccounted for")
    if off == 0:
        # The split reconciled trade for trade, so the CSVs orderstocsv wrote and the .sqx
        # copies are reproducible intermediates and go. A mismatch keeps them for inspection.
        shutil.rmtree(out / "raw")
        shutil.rmtree(out / "strategies")

    manifest.write(out,
                   {"install": str(install), "project": a.project, "databank": a.databank,
                    "data": "all"},
                   f"export_wfm.py --project {a.project} --databank {a.databank}",
                   {"strategies": len(staged), "unaccounted_trades": off,
                    "trades_in_steps": int(checked["assigned"].sum()),
                    "failed_in_sqx": sorted(written["status"].query("sqx_failed")["strategy"]),
                    **{f"{k}.parquet": len(v) for k, v in written.items()}})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
