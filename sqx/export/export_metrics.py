#!/usr/bin/env python3
"""Refresh one databank's metrics export: one row per strategy, paired IS/OOS columns."""

import argparse

from core import exportdrv, manifest
from core.paths import MASTER, metrics_export


def main() -> None:
    """Discard the databank's previous export, write a new one, and record what made it."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--view", default="Export Data View",
                    help="databank view on the master; its sampleTypes become (IS)/(OOS) columns")
    a = ap.parse_args()

    out = metrics_export(a.project, a.databank)
    out.mkdir(parents=True, exist_ok=True)
    for stale in sorted(out.iterdir()):
        stale.unlink()
        print(f"removed {stale.name}")

    csv = out / "metrics.csv"
    seen = exportdrv.metrics(a.project, a.databank, a.view, csv)

    rows = sum(1 for _ in open(csv)) - 1
    columns = open(csv).readline().count(";") + 1
    manifest.write(out,
                   {"install": str(MASTER), "project": a.project,
                    "databank": a.databank, "view": a.view},
                   f"export_metrics.py --project {a.project} --databank {a.databank} "
                   f"--view '{a.view}'",
                   {"metrics.csv": rows, "columns": columns, "worker_saw": seen})
    print(f"worker saw {seen} strategies; wrote {csv} ({rows} rows, {columns} columns)")


if __name__ == "__main__":
    main()
