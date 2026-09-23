#!/usr/bin/env python3
"""Record what templates the library holds and which markets each has been tried on."""

import argparse
import csv
from pathlib import Path

from core.templatepaths import template_registry, template_runs

TEMPLATE_COLUMNS = ("name", "archetype", "shape", "entry", "exit", "groups", "blocks",
                    "created", "origin", "status")
RUN_COLUMNS = ("template", "symbol", "timeframe", "project", "date", "strategies_built",
               "strategies_kept", "verdict", "report")


def append(csv_path: Path, columns: tuple[str, ...], row: dict[str, str],
           key: tuple[str, ...]) -> str:
    """Add a row, replacing any row that already carries the same key.

    Args:
        csv_path: The CSV to write.
        columns: Its header, in order.
        row: Values by column name; missing columns are written empty.
        key: Columns that together identify a row. For a run that is template, symbol and
            timeframe — one template is tried on many markets, so keying on the template
            alone would make each new market delete the previous one's result.

    Returns:
        "added" or "replaced". Replacing rather than appending twice is what keeps the
        file answerable: two rows for one key make "have I tried this" ambiguous.
    """
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8"))) if csv_path.exists() else []
    was = len(rows)
    ident = tuple(row.get(c, "") for c in key)
    rows = [r for r in rows if tuple(r[c] for c in key) != ident]
    rows.append({c: row.get(c, "") for c in columns})
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    return "replaced" if len(rows) == was else "added"


def main() -> None:
    """Write one template row, or one run row, into the library's CSVs."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true", help="write a run row instead of a template row")
    ap.add_argument("--set", action="append", default=[], metavar="COLUMN=VALUE",
                    help="a column value; repeat once per column")
    args = ap.parse_args()

    row = dict(pair.split("=", 1) for pair in args.set)
    if args.run:
        what = append(template_runs(), RUN_COLUMNS, row, ("template", "symbol", "timeframe"))
        print(f"runs.csv: {what} {row['template']} on {row.get('symbol')} {row.get('timeframe')}")
    else:
        what = append(template_registry(), TEMPLATE_COLUMNS, row, ("name",))
        print(f"registry.csv: {what} {row['name']} ({row.get('status')})")


if __name__ == "__main__":
    main()
