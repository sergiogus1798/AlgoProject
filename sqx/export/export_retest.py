#!/usr/bin/env python3
"""Export retest databanks as one typed Parquet each, every market inside it, in one SQX start."""

import argparse
import shutil
import time
from datetime import date
from pathlib import Path

import pandas as pd

from core import bankfile, bankframes, exportdrv, fanout, identities, manifest, sqxstats, sqxview, tradepack
from core.paths import MASTER, export_dir, worker_dir
from sqx.export import membank
from sqx.export.export_trades import SAMPLE_SEED, sign, stage


def pack(raw: Path, staged: int, out: Path, meta: dict, command: str, since: float) -> None:
    """Pack one databank's CSVs into its export directory and record where they came from.

    Args:
        raw: The databank's CSVs, one per strategy, named after the strategy.
        staged: How many strategies were staged from it.
        out: Its dated export directory.
        meta: The manifest's source block.
        since: When the export began (`manifest.write`).
        command: The command line that reproduces this export alone.
    """
    # One typed Parquet for the whole export, `Symbol` separating the markets: the same
    # store export_trades uses, read back with core.tradestore.market().
    record(tradepack.pack(sorted(raw.glob("*.csv")), out / "trades.parquet", per_market=True),
           staged, out, meta, command, since)


def record(packed: dict, staged: int, out: Path, meta: dict, command: str, since: float) -> None:
    """Write the manifest of a databank whose `trades.parquet` is in `out` (`packed`: the pack's dict)."""
    symbols = pd.read_parquet(out / "trades.parquet", columns=["Symbol"])["Symbol"]
    counts = {str(k): int(v) for k, v in symbols.value_counts().items()}
    for feed, n in sorted(counts.items()):
        print(f"  {feed:30} {n:>8} trades")
    manifest.write(out, meta, command, {"strategies": staged,
                                        "markets": len(counts), **counts,
                                        "kept_ticket": packed["kept_ticket"]}, since=since)
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
    ap.add_argument("--batch", default="",
                    help="step tag, e.g. structure or neighbours — several steps can retest the "
                         "same databank the same day; without a tag the later export overwrites "
                         "the earlier one's trades.parquet")
    a, began = ap.parse_args(), time.time()

    install = worker_dir(a.role) if a.role else MASTER
    day = date.today().isoformat()
    work = export_dir(a.project, "_staging", day, a.batch)
    # A same-day run that failed leaves its copies and CSVs here, and they would be packed
    # into this batch's trades as if they were its own (as export_trades clears its own).
    shutil.rmtree(work, ignore_errors=True)
    # Each databank's copies carry its position as a prefix: SQX names a CSV after its file
    # (knowhow/sqx-format/loaded-name-is-filename.md), and two legs of one batch hold the
    # same strategy names. The prefix is what splits the CSVs back afterwards.
    timeframes = {i: stage(a.project, db, work / "strategies", a.limit, install, f"{i}__")
                  for i, db in enumerate(a.databank)}
    for i, db in enumerate(a.databank):
        print(f"staged {len(timeframes[i])} strategies from {a.project}/{db}")

    # 📓 2026-09-26: a small export was ~17 s, most of it SQX starting, and steps 23 to 25
    # paid that once per WFC leg.
    # A live session's `.abk` (sqx.export.membank) serves the trades of a databank it holds whole;
    # only the others go through orderstocsv (refused while a GUI session holds the install).
    held = {}
    for i, db in enumerate(a.databank):
        if not (a.role and (membank.bank_dir(a.project, a.role) / f"{db}.abk").exists()):
            continue         # no dump: the identities of the staged files are not worth hashing
        files = sorted((work / "strategies").glob(f"{i}__*.sqx"))
        ids = {f.stem[len(f"{i}__"):]: v for f, v in identities.many(files, fanout.CORES).items()}
        if bank := membank.take(a.project, a.role, db, ids, "all"):
            markets = {f.stem[len(f"{i}__"):]: e for f, e in fanout.run(sqxstats.every, {f: 1 for f in files}, fanout.CORES)}
            lacking = sorted(n for n, e in markets.items() if not any(k.startswith("Main") for k in e))
            assert not lacking, f"{a.project}/{db}: {lacking[:3]} sin resultado Main en su .sqx: vuelve a correr el retest"
            stats = {n: next(v for k, v in e.items() if k.startswith("Main")) for n, e in markets.items()}
            try:
                why = bankframes.unbound(bank, stats, sqxview.measured(stats), markets)
            except SystemExit as err:       # both sample blocks filled: no single result to bind to
                why = str(err)
            if why:
                print(f"{a.project}/{db}: .abk no vale: {why}")
            else:
                held[i] = bank
    (work / "held").mkdir()
    for i in held:      # signed from here; what stays in strategies/ is what orderstocsv reads
        for f in (work / "strategies").glob(f"{i}__*.sqx"):
            f.rename(work / "held" / f.name)
    if len(held) < len(a.databank):
        exportdrv.trades(work / "strategies", work / "raw", data="all")
    for i, db in enumerate(a.databank):
        meta = {"install": str(install), "project": a.project, "databank": db, "data": "all",
                "timeframes": sorted(set(timeframes[i].values())), "limit": a.limit,
                "batch": a.batch or None, "sample_seed": SAMPLE_SEED if a.limit else None}
        command = (f"export_retest.py --project {a.project} --databank {db}"
                   + (f" --batch {a.batch}" if a.batch else "") + (f" --limit {a.limit}" if a.limit else ""))
        out = export_dir(a.project, db, day, a.batch)
        out.mkdir(parents=True, exist_ok=True)
        if i in held:
            record(bankfile.pack(held[i], out / "trades.parquet", per_market=True),
                   len(timeframes[i]), out, meta, command, began)
            sign(work / "held", out, f"{i}__")
            continue
        mine = work / str(i)
        mine.mkdir()
        for csv in (work / "raw").glob(f"{i}__*.csv"):
            csv.rename(mine / csv.name[len(f"{i}__"):])
        pack(mine, len(timeframes[i]), out, meta, command, began)
        sign(work / "strategies", out, f"{i}__")
    shutil.rmtree(work)


if __name__ == "__main__":
    main()
