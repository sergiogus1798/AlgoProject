#!/usr/bin/env python3
"""Export a cross-market retest databank as one typed Parquet, every market inside it."""

import argparse
import shutil
from datetime import date

import pandas as pd

from core import exportdrv, manifest, tradestore
from core.paths import MASTER, export_dir
from sqx.export.export_trades import SAMPLE_SEED, stage


def main() -> None:
    """Stage a retest databank, export it with data=all, and pack it into one Parquet."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank the retest wrote into")
    ap.add_argument("--limit", type=int, default=0,
                    help="export a reproducible random sample of this many strategies")
    a = ap.parse_args()

    out = export_dir(a.project, a.databank, date.today().isoformat())
    timeframes = stage(a.project, a.databank, out / "strategies", a.limit)
    print(f"staged {len(timeframes)} strategies from {a.project}/{a.databank}")

    exportdrv.trades(out / "strategies", out / "raw", data="all")
    # One typed Parquet for the whole export, `Symbol` separating the markets: the same
    # store export_trades uses, read back with tradestore.market(). The CSVs orderstocsv
    # wrote and the .sqx copies are intermediates and do not outlive the pack.
    packed = tradestore.pack(sorted((out / "raw").glob("*.csv")), out / "trades.parquet",
                             per_market=True)
    symbols = pd.read_parquet(out / "trades.parquet", columns=["Symbol"])["Symbol"]
    counts = {str(k): int(v) for k, v in symbols.value_counts().items()}
    for feed, n in sorted(counts.items()):
        print(f"{feed:30} {n:>8} trades")
    shutil.rmtree(out / "raw")
    shutil.rmtree(out / "strategies")

    manifest.write(out,
                   {"install": str(MASTER), "project": a.project, "databank": a.databank,
                    "data": "all", "timeframes": sorted(set(timeframes.values())),
                    "limit": a.limit, "sample_seed": SAMPLE_SEED if a.limit else None},
                   f"export_retest.py --project {a.project} --databank {a.databank}"
                   + (f" --limit {a.limit}" if a.limit else ""),
                   {"strategies": len(timeframes), "markets": len(counts), **counts,
                    "kept_ticket": packed["kept_ticket"]})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
