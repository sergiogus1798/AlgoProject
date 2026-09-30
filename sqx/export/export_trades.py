#!/usr/bin/env python3
"""Export one databank's trades into the data root, as one typed Parquet per export."""

import argparse
import random
import shutil
from datetime import date
from pathlib import Path

from core import exportdrv, manifest, sqxfile, tradepack
from core.paths import MASTER, databank_dir, export_dir, worker_dir


SAMPLE_SEED = 20260914   # a subset export is a sample, and a sample has to be reproducible


def stage(project: str, databank: str, dest: Path, limit: int = 0,
          install: Path = MASTER, prefix: str = "") -> dict[str, str]:
    """Copy a databank's strategies aside and read each one's timeframe.

    Args:
        project: Project name.
        databank: Databank name.
        dest: Directory to copy the .sqx files into.
        limit: Stage a random sample of this many instead of all of them; 0 means all.
            Random rather than the first N, because a databank is written in build order
            and its first strategies come from one generation run.
        install: Which install holds the project. Defaults to the master, which is where
            it lived before builds moved to the headless workers — a project built on the
            custodian is invisible from here without this.
        prefix: Put before each copy's file name, so several databanks can share one
            folder and one export.

    Returns:
        Strategy name to timeframe, e.g. {"Strategy 1.2.3": "M30"}. Copies rather than
        exporting in place so SQX never opens the live files.
    """
    dest.mkdir(parents=True, exist_ok=True)
    found = sorted(databank_dir(project, databank, install).glob("*.sqx"))
    if limit and limit < len(found):
        found = sorted(random.Random(SAMPLE_SEED).sample(found, limit))
    timeframes = {}
    for f in found:
        shutil.copy(f, dest / f"{prefix}{f.name}")
        timeframes[f.stem] = sqxfile.symbol(f)[1].rsplit("_", 1)[-1]
    return timeframes


def sign(staged: Path, out: Path, prefix: str = "") -> int:
    """Write `out/identity.csv` (strategy, identity) from the staged .sqx before they go.

    Args:
        staged: The staged copies, named after their strategies.
        out: The export directory.
        prefix: Only the copies carrying it, named without it (export_retest stages
            several databanks in one folder as `<i>__<name>.sqx`).

    Returns:
        Rows written. A few KB in place of the files, which weigh six times the Parquet;
        `core.study.identity.from_export` reads it once no install holds the databank.
    """
    found = sorted(staged.glob(f"{prefix}*.sqx"))
    (out / "identity.csv").write_text(
        "strategy,identity\n" + "".join(f"{f.stem[len(prefix):]},{sqxfile.identity(f)}\n"
                                         for f in found),
        encoding="utf-8")
    return len(found)


def main() -> None:
    """Stage a databank, export every trade of it, and pack them into one Parquet."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    # --symbol is load-bearing, not decoration: the packed trades drop the constant Symbol
    # column, so the manifest is the only record of which feed the backtest ran on.
    ap.add_argument("--symbol", required=True, help="SQX symbol without the timeframe suffix")
    ap.add_argument("--role", help="headless install holding the project, e.g. custodian; "
                                   "the master if absent")
    a = ap.parse_args()
    install = worker_dir(a.role) if a.role else MASTER

    out = export_dir(a.project, a.databank, date.today().isoformat())
    # Both are this command's intermediates. A run that failed half-way leaves them, and a
    # second export the same day then handed SQX a folder with a stray file: «No plugin
    # loader was able to recognize file …/strategies/manifest.json» (📓 2026-09-29). Its
    # own names: `strategies/` is `export_spp`'s product in the same day folder (the mothers
    # the variant factory opens), and this command used to delete it (📓 2026-09-30).
    staged, csvs = out / "_trades_sqx", out / "_trades_csv"
    for scratch in (staged, csvs):
        shutil.rmtree(scratch, ignore_errors=True)
    timeframes = stage(a.project, a.databank, staged, install=install)
    (out / "timeframes.csv").write_text(
        "strategy,timeframe\n" + "".join(f"{k},{v}\n" for k, v in timeframes.items()))
    print(f"staged {len(timeframes)} strategies from {a.project}/{a.databank}")

    exportdrv.trades(staged, csvs)
    # The CSVs are an intermediate, not the export: nine tenths of their bytes are quoting,
    # repeated text and four columns that are derivable back. Bars are not copied here at
    # all — they live once in the M1 library, which covers more history than this window did.
    packed = tradepack.pack(sorted(csvs.glob("*.csv")), out / "trades.parquet", per_market=False)
    shutil.rmtree(csvs)
    # The staged .sqx are copies of what the databank holds; the manifest names the
    # databank, and 757 of them weighed 119 MB beside a 20 MB Parquet. Their identities
    # stay, in identity.csv.
    sign(staged, out)
    shutil.rmtree(staged)

    manifest.write(out,
                   {"install": str(install), "project": a.project, "databank": a.databank,
                    "symbol": a.symbol},
                   f"export_trades.py --project {a.project} --databank {a.databank} "
                   f"--symbol {a.symbol}",
                   {**packed, "timeframes": sorted(set(timeframes.values()))})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
