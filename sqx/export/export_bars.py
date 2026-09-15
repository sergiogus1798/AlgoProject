#!/usr/bin/env python3
"""Export the bars of every market a base asset is retested on, into the shared bar library."""

import argparse
from datetime import date

from core import exportdrv, manifest
from core.paths import DATA, bars_file
from strategies.crossmarket import markets


def main() -> None:
    """Export one CSV per feed the cross-market study lists for the asset."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True, help="base asset, e.g. XAUUSD")
    ap.add_argument("--from", dest="date_from", default="2003.01.01")
    ap.add_argument("--to", dest="date_to", default="2026.01.01")
    a = ap.parse_args()

    tf = markets.load(a.asset)["timeframe"]
    # The declaration, not markets.universe(): bars are exported before the retest is, so
    # there is no export to discover the real feeds from yet.
    feeds = markets.declared(a.asset)

    rows = {}
    for feed in feeds:
        out = bars_file(feed, tf)
        out.parent.mkdir(parents=True, exist_ok=True)
        # One worker start per feed: a second export inside the same JVM overwrites the first.
        written = exportdrv.bars(feed, tf, out.parent, a.date_from, a.date_to)
        written.replace(out)
        rows[feed] = sum(1 for _ in out.open(encoding="utf-8")) - 1
        print(f"{feed:30} {rows[feed]:>8} bars → {out}")

    manifest.write(DATA / "bars",
                   {"asset": a.asset, "timeframe": tf, "feeds": feeds,
                    "window": [a.date_from, a.date_to], "exported": date.today().isoformat()},
                   f"export_bars.py --asset {a.asset} --from {a.date_from} --to {a.date_to}",
                   rows)
    print(f"wrote {len(rows)} feeds under {DATA / 'bars'}")


if __name__ == "__main__":
    main()
