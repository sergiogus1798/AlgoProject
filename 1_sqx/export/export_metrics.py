#!/usr/bin/env python3
"""Export one databank's metrics as one row per strategy, with paired IS/OOS columns."""

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core import exportdrv, manifest
from core.paths import MASTER, export_dir


def main() -> None:
    """Export a databank through a view and record what produced the file."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--view", default="Export Data View",
                    help="databank view on the master; its sampleTypes become (IS)/(OOS) columns")
    a = ap.parse_args()

    out = export_dir(a.project, a.databank, date.today().isoformat())
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
