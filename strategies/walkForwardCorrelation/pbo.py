#!/usr/bin/env python3
"""Is the way this grid's parameters get chosen prone to overfitting? The CSCV, by rule."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from strategies.walkForwardCorrelation import (cost, cscv, figures, matrix, report,
                                               rules, summary, trials)

PARAM = "param_"


def grid_of(metrics: pd.DataFrame, columns: pd.Index) -> pd.DataFrame:
    """Each variant's parameter tuple, in the panel's own column order.

    Args:
        metrics: Contract C3.
        columns: The panel's columns, which are variant identifiers.

    Returns:
        One row per panel column. The order is load-bearing: every rule receives scores
        as a positional array and answers with a position, so a grid in a different order
        would silently name a different variant.
    """
    named = [c for c in metrics.columns if c.startswith(PARAM)]
    return metrics.set_index("variant_id")[named].reindex(columns)


def flat(name: str, found: dict) -> dict:
    """One rule's numbers under keys a threshold can name.

    Args:
        name: The rule.
        found: What `summary.everything` returned, plus the rule's measured cost.

    Returns:
        `pbo_argmax`, `slope_argmax` and so on. `pipeline/stages/verdict.py` reads
        scalars out of this file by name, and a gate that has to walk into a sub-object
        is a gate nobody adds the next one to.
    """
    return {f"{k}_{name}": v for k, v in found.items() if not isinstance(v, (dict, list))}


def main() -> None:
    """Run the CSCV once per selection rule and write the verdict beside the batch."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds metrics.parquet and equity.parquet")
    a = ap.parse_args()

    cfg = report.settings()
    knobs = cfg["cscv"]
    print("PROGRESS 10 construyendo la matriz de rendimientos por periodo", flush=True)
    metrics = pd.read_parquet(a.work / "metrics.parquet")
    wide = matrix.usable(matrix.panel(a.work, knobs["period"]), metrics, cfg["min_trades"])
    grid = grid_of(metrics, wide.columns)
    inside, outside = matrix.windows(wide, matrix.split(a.work))

    runs, found = {}, {}
    for n, name in enumerate(knobs["rules"], 1):
        print(f"PROGRESS {10 + n * 20} {name}: {len(cscv.partitions(knobs['blocks']))} "
              f"particiones sobre {wide.shape[1]} variantes", flush=True)
        runs[name] = cscv.run(wide, knobs["blocks"], rules.RULES[name], grid,
                              np.random.default_rng(knobs["seed"]))
        found[name] = summary.everything(runs[name]) | cost.cost(inside, outside, grid,
                                                                name, knobs)

    print("PROGRESS 80 contando cuantas pruebas independientes hay de verdad", flush=True)
    independent = trials.independent(inside, knobs["cluster_k_max"])
    best = rules.argmax(cscv.sharpe(inside.to_numpy()), grid, None)
    deflated = trials.deflated(inside, best, independent["n_clusters"])
    moved = cost.drift(inside, outside, grid)

    print("PROGRESS 90 dibujando", flush=True)
    result = {"n": int(wide.shape[1]), "periods": int(wide.shape[0]),
              "period": knobs["period"], "blocks": knobs["blocks"],
              "dsr": deflated["dsr"], "sharpe_benchmark": deflated["benchmark"],
              "n_clusters": independent["n_clusters"], "levels_max": moved["levels_max"],
              # The carry-over slope is fitted across every variant of a partition, so it
              # is a property of the surface and identical for all three rules. Stated
              # once here; the per-rule copies below are the same number three times.
              "slope": found[knobs["rules"][0]]["slope"],
              "r2": found[knobs["rules"][0]]["r2"],
              **{k: v for name in knobs["rules"] for k, v in flat(name, found[name]).items()},
              "rules": found, "trials": independent, "sharpe": deflated, "drift": moved}
    (a.work / "cscv.json").write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    (a.work / "cscv.html").write_text(
        figures.page(a.work.name.replace("_", " "), runs, found, result), encoding="utf-8")

    head = knobs["rules"][0]
    print(f"PROGRESS 100 PBO {found[head]['pbo']:.0%} con {head}, DSR {deflated['dsr']:.2f}",
          flush=True)
    for name in knobs["rules"]:
        low, high = found[name]["ci95"]
        print(f"  {name:20s} PBO {found[name]['pbo']:6.1%}  percentil OOS "
              f"{found[name]['pct_oos']:5.1f} [{low:.0f}, {high:.0f}]  "
              f"pierde {found[name]['prob_loss']:.0%}")
    print(f"\n{wide.shape[1]} variantes que valen {independent['n_clusters']} pruebas "
          f"independientes; el orden se conserva con pendiente {result['slope']:+.2f}")
    print(f"-> {a.work / 'cscv.html'}")


if __name__ == "__main__":
    main()
