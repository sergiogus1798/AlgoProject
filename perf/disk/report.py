"""Inventory the data root: where the bytes are, what is over budget, and what could go."""

import argparse
import sys

from perf import store
from perf.disk import budget, duplicates, formats, inventory, retention
from perf.inputs import config

BRANCHES, COPIES, FORMATS = "disk.csv", "duplicates.csv", "formats.csv"
BUDGETS, RECLAIM = "budgets.csv", "reclaimable.csv"


def run(cfg: dict, quick: bool) -> dict:
    """Measure the data root and append every part to the catalogue.

    Args:
        cfg: What config.load() returned.
        quick: Skip the format comparison, which reads and rewrites real tables.

    Returns:
        The five tables, so a caller can print what it likes.
    """
    day = store.stamp()
    tree = [r | day for r in inventory.tree(cfg)]
    copies = [{"copies": r["copies"], "bytes": r["bytes"], "wasted": r["wasted"],
               "paths": " | ".join(r["paths"])} | day for r in duplicates.groups(cfg)]
    kinds = [] if quick else [r | day for r in formats.compare(cfg)]
    judged = [r | day for r in budget.judge(tree, cfg)]
    free = [r | day for r in retention.proposals(tree, cfg)]
    store.append(tree, BRANCHES)
    store.append(judged, BUDGETS)
    store.append(copies, COPIES) if copies else None
    store.append(kinds, FORMATS) if kinds else None
    store.append(free, RECLAIM) if free else None
    return {"tree": tree, "copies": copies, "formats": kinds, "budgets": judged,
            "reclaimable": free, "total": budget.total(tree, cfg)}


def main() -> None:
    """Print what the data root holds, what is over budget, and what could be freed.

    Exits non-zero when any branch or the total broke its budget, so this can sit in cron
    unattended the way `perf.catalogue` already does for regressions.
    """
    ap = argparse.ArgumentParser(description="Inventory the data root under ~/Desktop/AlgoData.")
    ap.add_argument("--quick", action="store_true", help="skip the format comparison")
    ap.add_argument("--set", action="append", default=[], help="config override, dotted.key=value")
    a = ap.parse_args()
    cfg = config.load(a.set)
    found = run(cfg, a.quick)
    whole = found["total"]

    print(f"AlgoData: {whole['gb']:.2f} GB de {whole['budget_gb']} GB "
          f"({whole['share']:.0%}) en {len(found['tree'])} ramas\n")
    for r in found["budgets"]:
        limit = f"{r['budget_gb']:>4} GB" if r["budget_gb"] else "  sin presupuesto"
        share = f"{r['share']:6.0%}" if r["share"] is not None else "      "
        print(f"  {r['verdict']:>11}  {r['gb']:8.2f} GB / {limit}  {share}  {r['branch']}")

    wasted = sum(r["wasted"] for r in found["copies"])
    print(f"\nduplicados: {len(found['copies'])} grupos, {wasted / 1e6:.1f} MB recuperables")
    for r in found["copies"][:5]:
        print(f"  x{r['copies']}  {r['wasted'] / 1e6:8.1f} MB  {r['paths']}")

    free = found["reclaimable"]
    print(f"\ncandidatos a borrar: {len(free)}, "
          f"{sum(r['bytes'] for r in free) / 1e9:.2f} GB  (nada se borra aquí)")
    for r in free[:10]:
        print(f"  {r['bytes'] / 1e6:9.1f} MB  {r['rule']:18s} {r['path']}  — {r['why']}")

    over = budget.failed(found["budgets"])
    for r in over:
        print(f"\nFUERA DE PRESUPUESTO: {r['branch']} {r['gb']:.2f} GB > {r['budget_gb']} GB")
    if whole["over"]:
        print(f"\nFUERA DE PRESUPUESTO: total {whole['gb']:.2f} GB > {whole['budget_gb']} GB")
    sys.exit(1 if over or whole["over"] else 0)


if __name__ == "__main__":
    main()
