#!/usr/bin/env python3
"""Export retest databanks as one typed Parquet each, every market inside it, in one SQX start."""

import argparse
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

from core import exportdrv, manifest, tradepack
from core.paths import MASTER, export_dir, worker_dir
from sqx.export.export_trades import SAMPLE_SEED, sign, stage


def pack(raw: Path, staged: int, out: Path, meta: dict, command: str) -> None:
    """Pack one databank's CSVs into its export directory and record where they came from.

    Args:
        raw: The databank's CSVs, one per strategy, named after the strategy.
        staged: How many strategies were staged from it.
        out: Its dated export directory.
        meta: The manifest's source block.
        command: The command line that reproduces this export alone.
    """
    # One typed Parquet for the whole export, `Symbol` separating the markets: the same
    # store export_trades uses, read back with core.tradestore.market().
    packed = tradepack.pack(sorted(raw.glob("*.csv")), out / "trades.parquet", per_market=True)
    symbols = pd.read_parquet(out / "trades.parquet", columns=["Symbol"])["Symbol"]
    counts = {str(k): int(v) for k, v in symbols.value_counts().items()}
    for feed, n in sorted(counts.items()):
        print(f"  {feed:30} {n:>8} trades")
    manifest.write(out, meta, command, {"strategies": staged,
                                        "markets": len(counts), **counts,
                                        "kept_ticket": packed["kept_ticket"]})
    print(f"wrote {out}")


def main() -> None:
    """Stage every databank asked for, export them with data=all in one go, pack each apart."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, action="append",
                    help="a databank the retest wrote into; repeat it to export several with "
                         "one SQX start instead of one each")
    ap.add_argument("--role", help="headless install holding the project; the master if absent")
    ap.add_argument("--limit", type=int, default=0,
                    help="export a reproducible random sample of this many strategies")
    a = ap.parse_args()

    install = worker_dir(a.role) if a.role else MASTER
    day = date.today().isoformat()
    work = export_dir(a.project, "_staging", day)
    # Each databank's copies carry its position as a prefix: SQX names a CSV after its file
    # (knowhow/sqx-format/loaded-name-is-filename.md), and two legs of one batch hold the
    # same strategy names. The prefix is what splits the CSVs back afterwards.
    timeframes = {i: stage(a.project, db, work / "strategies", a.limit, install, f"{i}__")
                  for i, db in enumerate(a.databank)}
    for i, db in enumerate(a.databank):
        print(f"staged {len(timeframes[i])} strategies from {a.project}/{db}")

    # 📓 2026-09-26: a small export was ~17 s, most of it SQX starting, and steps 23 to 25
    # paid that once per WFC leg.
    exportdrv.trades(work / "strategies", work / "raw", data="all")
    for i, db in enumerate(a.databank):
        mine = work / str(i)
        mine.mkdir()
        for csv in (work / "raw").glob(f"{i}__*.csv"):
            csv.rename(mine / csv.name[len(f"{i}__"):])
        pack(mine, len(timeframes[i]), export_dir(a.project, db, day),
             {"install": str(install), "project": a.project, "databank": db, "data": "all",
              "timeframes": sorted(set(timeframes[i].values())), "limit": a.limit,
              "sample_seed": SAMPLE_SEED if a.limit else None},
             f"export_retest.py --project {a.project} --databank {db}"
             + (f" --limit {a.limit}" if a.limit else ""))
        sign(work / "strategies", export_dir(a.project, db, day), f"{i}__")
    # The CSVs orderstocsv wrote and the .sqx copies are intermediates; only identity.csv
    # outlives them — a WFC batch of 5000 variants must not keep its .sqx three times.
    shutil.rmtree(work)


if __name__ == "__main__":
    main()
