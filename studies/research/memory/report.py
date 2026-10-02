#!/usr/bin/env python3
"""The command: rebuilds the attempts table and the ideas index, writes them, prints a summary."""

import argparse
import csv
from pathlib import Path

from core.researchpaths import research_memory_dir
from studies.research.memory import attempts, ideas, queries, verdict


def save(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    """Write dicts as a CSV, header from `fields` or the first row."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def show(rows: list[dict], cols: list[str]) -> None:
    """Print some columns of a table, aligned."""
    width = [max(len(c), *(len(str(r[c])) for r in rows)) for c in cols]
    for line in [dict(zip(cols, cols))] + rows:
        print("  ".join(str(line[c]).ljust(w) for c, w in zip(cols, width)))


def build(out: Path) -> tuple[list[dict], list[dict]]:
    """Recompute everything from its sources and write `attempts.csv`, `ideas.csv`,
    `ideas_spent.csv`, `survivors_by_family.csv` and `untouched_cells.csv` into `out`."""
    out.mkdir(parents=True, exist_ok=True)
    idea_rows = ideas.index()
    rows = attempts.table({i["idea"] for i in idea_rows})
    idea_rows = ideas.index(rows)
    save(out / "attempts.csv", rows, attempts.COLUMNS)
    save(out / "ideas.csv", idea_rows, ideas.COLUMNS)
    save(out / "ideas_spent.csv", queries.ideas_spent(idea_rows),
         ["symbol", "timeframe", "direction", "family", "ideas", "chosen", "hypotheses"])
    save(out / "survivors_by_family.csv", queries.survivors_by_family(rows),
         ["family", "asset_class", "attempts", "closed", "with_survivors", "survivors"])
    save(out / "untouched_cells.csv", [dict(zip(("symbol", "timeframe", "direction", "family"), c))
                                       for c in queries.untouched_cells(rows)])
    return rows, idea_rows


def main() -> None:
    """Rebuild the memory, or close one finished run's row with --close."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=research_memory_dir())
    ap.add_argument("--close", type=Path, metavar="RUN_DIR",
                    help="cierra la fila de runs.csv de un run del autopilot y sale")
    ap.add_argument("--runs-csv", type=Path, help="con --close: otra tabla en vez de runs.csv")
    a = ap.parse_args()
    if a.close:
        print(verdict.close_run(a.close, a.runs_csv))
        return
    rows, idea_rows = build(a.out)
    closed = [r for r in rows if r["verdict"]]
    print(f"{len(rows)} intentos, {len(closed)} con veredicto en runs.csv, "
          f"{sum(r['outcome'] != 'unknown' for r in rows)} con embudo; {len(idea_rows)} ideas "
          f"en el indice; {len(queries.untouched_cells(rows))}/{len(queries.grid())} celdas sin tocar")
    show(rows, ["project", "template", "symbol", "timeframe", "direction", "built", "oos", "gate",
                "markets", "mcr", "spp", "custodian_hours", "outcome"])
    print(f"\nescrito en {a.out}")


if __name__ == "__main__":
    main()
