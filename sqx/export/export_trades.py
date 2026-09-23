#!/usr/bin/env python3
"""Export one databank's trades into the data root, as one typed Parquet per export."""

import argparse
import random
import shutil
from datetime import date
from pathlib import Path

from core import exportdrv, manifest, sqxfile, tradestore
from core.paths import MASTER, databank_dir, export_dir


SAMPLE_SEED = 20260914   # a subset export is a sample, and a sample has to be reproducible


def stage(project: str, databank: str, dest: Path, limit: int = 0) -> dict[str, str]:
    """Copy a databank's strategies aside and read each one's timeframe.

    Args:
        project: Project name on the master.
        databank: Databank name on the master.
        dest: Directory to copy the .sqx files into.
        limit: Stage a random sample of this many instead of all of them; 0 means all.
            Random rather than the first N, because a databank is written in build order
            and its first strategies come from one generation run.

    Returns:
        Strategy name to timeframe, e.g. {"Strategy 1.2.3": "M30"}. Copies rather than
        exporting in place so SQX never opens the live files.
    """
    dest.mkdir(parents=True, exist_ok=True)
    found = sorted(databank_dir(project, databank, MASTER).glob("*.sqx"))
    if limit and limit < len(found):
        found = sorted(random.Random(SAMPLE_SEED).sample(found, limit))
    timeframes = {}
    for f in found:
        shutil.copy(f, dest / f.name)
        timeframes[f.stem] = sqxfile.symbol(f)[1].rsplit("_", 1)[-1]
    return timeframes


def main() -> None:
    """Stage a databank, export every trade of it, and pack them into one Parquet."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    # --symbol is load-bearing, not decoration: the packed trades drop the constant Symbol
    # column, so the manifest is the only record of which feed the backtest ran on.
    ap.add_argument("--symbol", required=True, help="SQX symbol without the timeframe suffix")
    a = ap.parse_args()

    out = export_dir(a.project, a.databank, date.today().isoformat())
    timeframes = stage(a.project, a.databank, out / "strategies")
    (out / "timeframes.csv").write_text(
        "strategy,timeframe\n" + "".join(f"{k},{v}\n" for k, v in timeframes.items()))
    print(f"staged {len(timeframes)} strategies from {a.project}/{a.databank}")

    exportdrv.trades(out / "strategies", out / "trades")
    # The CSVs are an intermediate, not the export: nine tenths of their bytes are quoting,
    # repeated text and four columns that are derivable back. Bars are not copied here at
    # all — they live once in the M1 library, which covers more history than this window did.
    packed = tradestore.pack(sorted((out / "trades").glob("*.csv")),
                             out / "trades.parquet", per_market=False)
    shutil.rmtree(out / "trades")
    # The staged .sqx are copies of what the databank holds; the manifest names the
    # databank, and 757 of them weighed 119 MB beside a 20 MB Parquet.
    shutil.rmtree(out / "strategies")

    manifest.write(out,
                   {"install": str(MASTER), "project": a.project, "databank": a.databank,
                    "symbol": a.symbol},
                   f"export_trades.py --project {a.project} --databank {a.databank} "
                   f"--symbol {a.symbol}",
                   {**packed, "timeframes": sorted(set(timeframes.values()))})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
