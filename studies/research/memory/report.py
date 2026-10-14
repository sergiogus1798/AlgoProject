#!/usr/bin/env python3
"""The command: rebuilds the attempts table and the ideas index, writes them, prints a summary."""

import argparse
import csv
from pathlib import Path

from core.researchpaths import research_memory_dir
from studies.research.memory import attempts, ideas, queries, verdict
from studies.research.memory.causes import CAUSES, VOCABULARY

FAILURE = ["project", "template", "symbol", "timeframe", "direction", "family", "date", "outcome",
           "cause", "cause_share", "causes", "rules_out", "try_next", "hypothesis"]


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
    `ideas_spent.csv`, `survivors_by_family.csv`, `untouched_cells.csv` and `failures.csv`
    (the closed runs that carry a cause, every cell) into `out`."""
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
    save(out / "failures.csv", [{k: r[k] for k in FAILURE} for r in rows
                                if r["cause"] and queries.conclusive(r, False)], FAILURE)
    return rows, idea_rows


def cell_text(rows: list[dict], idea_rows: list[dict], cell: list[str]) -> str:
    """One cell's memory as the page the ideaExpert and the ideaReviewer read, in Spanish: its
    closed failures with cause, what each rules out and what to try, the runs that are not
    evidence, and every idea already proposed on that asset, timeframe and direction."""
    failed = queries.failures(rows, cell[0], cell[1], cell[2], cell[3])
    other = [r for r in rows if queries.cell(r) == tuple(cell) and r not in failed]
    spent = [i for i in idea_rows if (i["symbol"], i["timeframe"], i["direction"]) == tuple(cell[:3])]
    lines = [f"MEMORIA DE LA CELDA {' '.join(cell)}",
             f"Vocabulario de causas: {CAUSES['status']}.", "",
             f"Fracasos cerrados ({len(failed)}) — quien proponga aquí adopta o rechaza cada uno "
             "por escrito:"]
    for r in failed:
        lines += [f"- {r['project']} · plantilla {r['template']} · {r['date']} · {r['outcome']} · "
                  f"causa: {VOCABULARY[r['cause']]['label']} ({r['cause']}"
                  + (f", {r['cause_share']} de las que fallaron; todas: {r['causes']}"
                     if r["cause_share"] else "") + ")",
                  f"  descarta: {r['rules_out']}", f"  probar: {r['try_next']}"]
        if r["trades_ratio"] != "":
            lines.append(f"  hoja: op/año x{r['trades_ratio']}, duración x{r['holding_ratio']} "
                         f"(construido ÷ predicho), {r['hypothesis']}")
    lines += ["", f"Corridas de la celda que no son un fracaso cerrado ({len(other)}):"]
    lines += [f"- {r['project']} · plantilla {r['template']} · {r['outcome']}"
              + (" · corte de desarrollo: no es evidencia" if r["dev_cut"] else "")
              + (" · fallo técnico: no es evidencia" if r["cause"] == "infrastructure" else "")
              for r in other]
    lines += ["", f"Ideas ya propuestas en {' '.join(cell[:3])}, de cualquier familia ({len(spent)}):"]
    lines += [f"- {i['idea']} · {i['date']} · {'ya es plantilla' if i['chosen'] == 'yes' else 'no elegida'}"
              f" · AlgoData/ideas/{i['file']}" for i in spent]
    return "\n".join(lines)


def main() -> None:
    """Rebuild the memory, close one finished run's row with --close, or print one cell with --cell."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=research_memory_dir())
    ap.add_argument("--close", type=Path, metavar="RUN_DIR",
                    help="cierra la fila de runs.csv de un run del autopilot y sale")
    ap.add_argument("--runs-csv", type=Path, help="con --close: otra tabla en vez de runs.csv")
    ap.add_argument("--cell", nargs=4, metavar=("ACTIVO", "MARCO", "DIRECCION", "FAMILIA"),
                    help="imprime la memoria de esa celda (fracasos con su causa, ideas gastadas) y sale")
    a = ap.parse_args()
    if a.close:
        print(verdict.close_run(a.close, a.runs_csv))
        return
    rows, idea_rows = build(a.out)
    if a.cell:
        print(cell_text(rows, idea_rows, a.cell))
        return
    closed = [r for r in rows if r["verdict"]]
    print(f"{len(rows)} intentos, {len(closed)} con veredicto en runs.csv, "
          f"{sum(r['outcome'] != 'unknown' for r in rows)} con embudo; {len(idea_rows)} ideas "
          f"en el indice; {len(queries.untouched_cells(rows))}/{len(queries.grid())} celdas sin tocar")
    show(rows, ["project", "template", "symbol", "timeframe", "direction", "built", "oos", "gate",
                "markets", "mcr", "spp", "custodian_hours", "outcome", "cause"])
    print(f"\nescrito en {a.out}")


if __name__ == "__main__":
    main()
