#!/usr/bin/env python3
"""Export a cross-market retest databank and split every strategy's trades by market."""

import argparse
import collections
from datetime import date
from pathlib import Path

from core import exportdrv, manifest, trades
from core.paths import MASTER, export_dir
from sqx.export.export_trades import stage


def split(raw_dir: Path, out_dir: Path) -> dict[str, int]:
    """Fan one CSV per strategy out into one CSV per market.

    Args:
        raw_dir: Where orderstocsv wrote its files, one per strategy, all markets inside.
        out_dir: Root to write `<feed>/<strategy>.csv` under.

    Returns:
        Trades written per feed. The feed name is taken from the Symbol column rather than
        from the retest task's chart list, so a market that produced no trades simply does
        not appear and is never silently confused with one that did.
    """
    counts: dict[str, int] = collections.Counter()
    for f in sorted(raw_dir.glob("*.csv")):
        for feed, block in trades.by_market(trades.read(f)).items():
            dest = out_dir / feed
            dest.mkdir(parents=True, exist_ok=True)
            # Written back in SQX's own date format: a split file has to be readable by the
            # same reader as the file it came from, and to_csv would default to ISO.
            block.to_csv(dest / f.name, sep=";", index=False, date_format=trades.TIME)
            counts[feed] += len(block)
    return dict(counts)


def main() -> None:
    """Stage a retest databank, export it with data=all, and split the result per market."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank the retest wrote into")
    a = ap.parse_args()

    out = export_dir(a.project, a.databank, date.today().isoformat())
    timeframes = stage(a.project, a.databank, out / "strategies")
    print(f"staged {len(timeframes)} strategies from {a.project}/{a.databank}")

    exportdrv.trades(out / "strategies", out / "raw", data="all")
    counts = split(out / "raw", out / "trades")
    for feed, n in sorted(counts.items()):
        print(f"{feed:30} {n:>8} trades")

    manifest.write(out,
                   {"install": str(MASTER), "project": a.project, "databank": a.databank,
                    "data": "all", "timeframes": sorted(set(timeframes.values()))},
                   f"export_retest.py --project {a.project} --databank {a.databank}",
                   {"strategies": len(timeframes), "markets": len(counts), **counts})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
