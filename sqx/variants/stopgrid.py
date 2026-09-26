#!/usr/bin/env python3
"""Fabricate each mother's stop-loss batch: the original, the X = 1000 probe and the grid's X."""

import argparse
from pathlib import Path

import pandas as pd

from sqx.variants import inputs, manifest, tuples
from sqx.variants.build import rewrite, stoploss

# A stop this far away never fires, so this variant must reproduce the original trade for
# trade. It is the proof the graft changed nothing but the stop.
PROBE = 1000.0
NAME = "{strategy} {variant_id}"


def plan(mothers: list[Path], grid: pd.DataFrame | None) -> pd.DataFrame:
    """Every file to write: per mother the reference, the probe and its rows of the grid.

    Args:
        mothers: The `.sqx` built without a stop; the stem is the strategy's name.
        grid: `stopgrid.csv` as the study wrote it (strategy, percentile, step, x), or None
            for the first pass, which runs only the reference and the probe.

    Returns:
        One row per file, with the columns contract C2 carries: `variant_id`, `stratum`
        (reference, probe or grid), `origin`, the canary columns empty, `tuple_hash`, and
        the study's own `strategy`, `percentile`, `step` and `x`.
    """
    rows = []
    for m, mother in enumerate(mothers):
        own = [] if grid is None else grid[grid["strategy"] == mother.stem].to_dict("records")
        wanted = ([{"stratum": "reference", "x": None}, {"stratum": "probe", "x": PROBE}]
                  + [{"stratum": "grid", **r} for r in own])
        for k, row in enumerate(wanted):
            x = row["x"]
            rows.append({"variant_id": f"S{m:02d}V{k:03d}", "strategy": mother.stem,
                         "mother": str(mother), "stratum": row["stratum"],
                         "percentile": row.get("percentile"), "step": row.get("step"),
                         "x": x, "origin": row["stratum"] == "reference",
                         "canary_expect_netprofit": None, "canary_expect_trades": None,
                         "canary_expect_same_as": None,
                         "tuple_hash": tuples.tuple_hash(
                             {} if x is None else {stoploss.VARIABLE: x})})
    return pd.DataFrame(rows)


def write(rows: pd.DataFrame, folder: Path, shape: str) -> None:
    """Write every planned file: the reference untouched but renamed, the rest grafted.

    Args:
        rows: Output of `plan`.
        folder: Where the `.sqx` go; emptied first, because the manifest adopts whatever
            is on disk.
        shape: A key of `rewrite.SHAPES`.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob("*.sqx"):
        stale.unlink()
    for row in rows.itertuples():
        parent = rewrite.members(Path(row.mother))
        if row.stratum != "reference":
            parent[rewrite.PORTFOLIO] = stoploss.graft(
                parent[rewrite.PORTFOLIO].decode("utf-8"), row.x).encode("utf-8")
        parts = rewrite.variant(parent, row.variant_id,
                                NAME.format(strategy=row.strategy, variant_id=row.variant_id), {})
        rewrite.save(folder / f"{row.variant_id}.sqx", parts, shape)


def main() -> None:
    """Fabricate the batch and its manifest, and refuse one whose files are not the plan."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mothers", required=True, type=Path, help="folder of .sqx without a stop")
    ap.add_argument("--out", required=True, type=Path,
                    help="the batch directory under the data root; holds sqx/ afterwards")
    ap.add_argument("--grid", type=Path,
                    help="stopgrid.csv from studies.closing.atrCalculator.report; without it, "
                         "only the reference and the X = 1000 probe")
    a = ap.parse_args()

    mothers = sorted(a.mothers.glob("*.sqx"))
    rows = plan(mothers, pd.read_csv(a.grid) if a.grid else None)
    write(rows, a.out / "sqx", inputs.load()["build"]["shape"])
    frame, report = manifest.write(rows, a.out / "sqx", [stoploss.VARIABLE])
    frame.merge(rows[["variant_id", "strategy", "percentile", "step", "x"]], on="variant_id") \
         .to_parquet(a.out / manifest.FILE, compression="zstd", index=False)
    broken = report["missing"] or report["unexpected"] or report["tuple_mismatch"]
    if broken:
        raise SystemExit(f"el lote no es el plan: {report}")
    print(f"{len(mothers)} madre(s) -> {len(rows)} ficheros en {a.out / 'sqx'}")
    print(rows.groupby(["strategy", "stratum"]).size().to_string())


if __name__ == "__main__":
    main()
