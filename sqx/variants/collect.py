#!/usr/bin/env python3
"""Join the three legs' metrics onto the manifest and write contract C3, metrics.parquet."""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.assetdata import doctrine
from sqx.variants import legs as legmod
from sqx.variants import united

NAME = "Strategy Name"
# The two ways the owner reads one batch, and they are not a preference: the whole point of
# keeping `oos2` on a pedestal is being able to ask the strict question. `build+oos1` vs
# `oos2` spends the reserved segment as the only out-of-sample; `build` vs `oos1+oos2`
# treats everything after the build as out of sample. Both are written into C3 so one
# harvest answers both without re-running anything.
UNIONS = [(["build", "oos1"], "build+oos1"), (["oos1", "oos2"], "oos1+oos2"),
          (["build", "oos1", "oos2"], "ALL")]
# SQX renames a colliding strategy by appending "(1)", "(2)" ... Stripping it is what lets
# a batch loaded twice still be read; the duplicate rows are then caught as duplicates
# rather than silently joining onto the wrong tuple.
COLLISION = r"\(\d+\)$"


def per_segment(legs: list[dict],
                say: Callable[[int, str], None]) -> pd.DataFrame:
    """Every leg's stored metrics, one row per variant, segment and market.

    Args:
        legs: What `ran.json` recorded, in segment order.
        say: Called with a percentage and a status line.

    Returns:
        The long frame that everything else here is built from. It is read out of the
        `.sqx` and not out of the exported CSV on purpose: the CSV carries the main
        symbol's 41 columns, while the files carry all 82 stored metrics **for every
        market** — which is what a view of the performance surface on other assets needs,
        and what makes the unions exact.
    """
    rows = [united.per_result(Path(leg["databank_dir"]), leg["segment"],
                              lambda p, line, i=i: say(i * 25 + p * 25 // 100, line))
            for i, leg in enumerate(legs)]
    return pd.concat(rows, ignore_index=True)


def unions(rows: pd.DataFrame, work: Path) -> pd.DataFrame:
    """The per-segment rows plus every union the studies downstream read.

    Args:
        rows: What `per_segment` returned.
        work: The batch directory, for the joined daily curves.

    Returns:
        The same frame with three more `segment` labels: `build+oos1`, `oos1+oos2` and
        `ALL`. Drawdown and Sharpe of a union are recomputed from the joined curve of the
        main market, because neither is additive — a union can cross a trough deeper than
        any of its parts.
    """
    curves = pd.read_parquet(work / "equity.parquet")
    spans = json.loads((work / "equity.json").read_text(encoding="utf-8"))["windows"]
    made = [rows]
    for segments, label in UNIONS:
        first, last = spans[segments[0]][0], spans[segments[-1]][1]
        window = curves[(curves.index >= first) & (curves.index <= last)]
        made.append(united.combine(rows, segments, window, label))
    return pd.concat(made, ignore_index=True)


def join(rows: pd.DataFrame, manifest: pd.DataFrame,
         segments: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Attach every variant's design tuple to its measured results, minus the thin ones.

    Args:
        rows: What `unions` returned.
        manifest: Contract C2.
        segments: The three leg names, for the trade total.

    Returns:
        The rows with `trades_total` and `usable` on them, the joined C3 frame, and what
        did not line up. The key is `variant_id`, because SQX names a databank entry after
        the **file** -- `P00000.sqx` comes back as `P00000` -- and not after
        `<StrategyName>`. The collision suffix SQX appends to a duplicate (`P00000(1)`) is
        stripped first, so a batch loaded twice still joins.

        ⚠️ **C3 carries only the backtests that clear `wfc.min_trades_total`.** The
        exclusion is structural rather than a flag downstream studies have to remember: a
        consumer that forgot it would put the degenerate corners of the grid back into the
        correlation. What was excluded stays in `segments.parquet`, marked, and is counted
        in `collected.json`.
    """
    rows = rows.assign(variant_id=rows["variant_id"].str.replace(COLLISION, "", regex=True))
    floor = doctrine()["wfc"]["min_trades_total"]
    rows = rows.merge(united.thin(rows, floor, segments), on=["variant_id", "market"],
                      how="left")
    kept = rows[rows["usable"].fillna(False)]
    table = united.wide(kept)
    merged = manifest.drop(columns="sqx_name", errors="ignore").merge(
        table, on="variant_id", how="inner")
    thin_ids = sorted(set(rows["variant_id"]) - set(table["variant_id"]))
    missing = sorted(set(manifest["variant_id"]) - set(rows["variant_id"]))
    extra = sorted(set(rows["variant_id"]) - set(manifest["variant_id"]))
    return rows, merged, {"missing": missing, "unexpected": extra, "floor": int(floor),
                          "thin": len(thin_ids), "thin_ids": thin_ids[:20],
                          "thin_cells": int((~rows["usable"].fillna(False)).sum())}


def canaries(merged: pd.DataFrame) -> dict:
    """Whether the controls came back distinguishable from one another.

    Args:
        merged: What `join` returned.

    Returns:
        The count of controls and how many distinct build-segment results they produced.

        ⚠️ A control that did not clear `wfc.min_trades_total` is not here to be counted:
        C3 excludes it like any other thin backtest. That is the right answer — a canary
        that barely trades cannot tell you whether the batch ran — but it means a batch of
        canaries that all trade too little fails this check for the other reason. The
        `thin` count in `collected.json` is what tells the two apart.

        **This is the detector for the failure this module exists to prevent.** A variant
        that was never actually run keeps the parent's `SQStats`, so it exports the
        parent's metrics rather than looking empty. If every control returns one identical
        number, nothing ran, and no amount of downstream analysis will say so.
    """
    controls = merged[merged["stratum"].isin(["canary", "origin"])]
    profits = controls["NetProfit (build)"].dropna()
    return {"n": len(controls), "distinct_netprofit": int(profits.nunique()),
            "all_identical": bool(len(profits) > 1 and profits.nunique() == 1)}


def main() -> None:
    """Write C3 beside the batch, and refuse the batch if the controls did not move."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    a = ap.parse_args()

    ran = json.loads((a.work / "ran.json").read_text(encoding="utf-8"))
    print("PROGRESS 5 leyendo las metricas de los tres tramos", flush=True)
    rows = unions(per_segment(ran["legs"], lambda pct, line:
                               print(f"PROGRESS {pct} {line}", flush=True)), a.work)
    manifest = pd.read_parquet(a.work / "manifest.parquet")
    rows, merged, gaps = join(rows, manifest, [leg["segment"] for leg in ran["legs"]])
    rows.to_parquet(a.work / "segments.parquet", index=False)
    print(f"PROGRESS 85 {len(merged)} filas unidas", flush=True)
    merged.to_parquet(a.work / "metrics.parquet", index=False)

    found = canaries(merged)
    markets = sorted(set(rows["market"]) - {legmod.MAIN})
    # Lifted to the top level as well as nested: the pipeline's `must` gate reads one
    # number out of this file by name, and a gate that has to walk into a sub-object is a
    # gate nobody will add the next one to.
    checks = gaps | {"canaries": found, "n": len(merged),
                     "canaries_distinct": found["distinct_netprofit"],
                     "segments": sorted(set(rows["segment"])), "markets": markets}
    (a.work / "collected.json").write_text(
        json.dumps(checks | {"files": [{"path": "metrics.parquet"},
                                       {"path": "segments.parquet"}],
                             "removable": [str((a.work / "sqx").name)]}, indent=2),
        encoding="utf-8")
    print(f"PROGRESS 100 {found['distinct_netprofit']} resultados distintos entre "
          f"{found['n']} controles, mercados: {', '.join(markets) or 'ninguno'}", flush=True)
    if gaps["thin"]:
        print(f"\n⚠️  {gaps['thin']} variantes y {gaps['thin_cells']} celdas "
              f"(variante x mercado) operan menos de {gaps['floor']} veces en "
              f"build+oos1+oos2 y quedan FUERA de toda estadistica. Siguen en "
              f"segments.parquet con usable=False, por si hace falta mirarlas.")
    print(json.dumps(checks, indent=2))

    if found["all_identical"]:
        sys.exit("los controles devuelven el MISMO resultado: nada se reteseo de verdad, "
                 "las variantes traen las metricas del padre. No uses este lote.")
    if gaps["missing"]:
        sys.exit(f"{len(gaps['missing'])} variantes no volvieron del retest")


if __name__ == "__main__":
    main()
