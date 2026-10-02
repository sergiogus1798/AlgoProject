#!/usr/bin/env python3
"""Refresh one databank's metrics export: one row per strategy, paired IS/OOS columns."""

import argparse
import csv

from core import manifest, sqxview
from core.paths import MASTER, databank_dir, metrics_export, worker_dir


def main() -> None:
    """Discard the databank's previous export, write a new one, and record what made it."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--role", help="headless install holding the project; "
                    "omit for the master")
    a = ap.parse_args()

    out = metrics_export(a.project, a.databank)
    install = worker_dir(a.role) if a.role else MASTER
    # Read off each .sqx, no SQX running (core/sqxview.py): the conductor cycle this used to
    # cost — stage, start, wait, export through the view, stop — was ~40 s of a 1-2 s job.
    files = {f.stem: f for f in sorted(databank_dir(a.project, a.databank, install).glob("*.sqx"))}
    table = sqxview.frame(files)
    if table.empty and not len(table.columns):
        # An empty databank used to leave a 1-byte file («\n») that every reader crashed on
        # with «No columns to parse from file» (2026-09-29, CrossTF): the header says «none».
        table = table.reindex(columns=["Strategy Name"])
    # The old export goes only now, with the new table in hand: gone for the seconds the .sqx
    # took to read, the window's loader found no manifest.json and said so in red (📓 2026-09-30).
    out.mkdir(parents=True, exist_ok=True)
    for stale in sorted(out.iterdir()):
        stale.unlink()
        print(f"removed {stale.name}")
    csv_path = out / "metrics.csv"
    table.to_csv(csv_path, sep=";", index=False, quoting=csv.QUOTE_ALL)
    manifest.write(out,
                   {"install": str(install), "project": a.project, "databank": a.databank,
                    "metrics": "SQStats of each .sqx, the columns of «Export Data View»"},
                   f"export_metrics.py --project {a.project} --databank {a.databank}",
                   {"metrics.csv": len(table), "columns": len(table.columns),
                    "worker_saw": len(files)})
    print(f"read {len(files)} strategies; wrote {csv_path} ({len(table)} rows, "
          f"{len(table.columns)} columns)")


if __name__ == "__main__":
    main()
