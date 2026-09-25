#!/usr/bin/env python3
"""Keep the M1 bar library in step with SQX: pull what is missing, refresh what SQX has grown."""

import argparse
import csv
import io
from datetime import date


from core import barstore, exportdrv, manifest
from core.assetdata import markets, symbols
from core.paths import DATA, bar_source

# Column positions of `-symbol action=list`: name, base symbol, resolution, timezone,
# date from, date to, days, bars. The rest is the data source and the category.
NAME, RESOLUTION, FROM, TO, BARS = 0, 2, 4, 5, 7


def catalogue(text: str) -> dict[str, dict]:
    """What SQX says it holds, per M1 feed.

    Args:
        text: Raw stdout of `-symbol action=list`.

    Returns:
        {feed: {"bars": int, "from": str, "to": str}} for the M1 feeds only. Tick feeds are
        dropped: a tick series is not bars and nothing here resamples from one.
    """
    rows = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) <= BARS or row[RESOLUTION] != "M1":
            continue
        rows[row[NAME]] = {"bars": int(row[BARS]), "from": row[FROM], "to": row[TO]}
    return rows


def wanted() -> list[str]:
    """Every feed the project should hold bars for.

    Returns:
        Feed names, sorted. The declaration in assets/_markets.yaml drives it — every base asset
        and every market it is retested on — plus whatever the library already holds, so a
        feed pulled once keeps being refreshed after its asset leaves the declaration.
    """
    declared = [markets(s) for s in symbols()]
    feeds = {spec["main"] for spec in declared if spec}
    feeds |= {m["feed"] for spec in declared if spec
              for category in spec.get("categories", {}).values() for m in category}
    feeds |= {d.name for d in (DATA / "bars").iterdir() if bar_source(d.name).exists()}
    return sorted(feeds)


def stale(feeds: list[str], sqx: dict[str, dict], held: dict[str, dict]) -> list[str]:
    """Which feeds have to be pulled from SQX.

    Args:
        feeds: What wanted() returned.
        sqx: What catalogue() returned.
        held: What barstore.library() returned.

    Returns:
        The feeds the library is missing, plus the ones whose bar count no longer matches
        SQX's. The count is the staleness signal rather than a data-version stamp: it moves
        whenever the data does — growth, backfill or a rewritten middle alike — and needs no
        mapping from a feed to the .version file that happens to cover it. It only works
        because every feed is pulled over its own full range; a fixed window would clip one
        feed and report it stale forever.
    """
    return [f for f in feeds
            if f not in held or held[f]["bars"] != sqx[f]["bars"]]


def main() -> None:
    """Pull every missing or outdated feed's M1 bars into the library."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what is stale, pull nothing")
    a = ap.parse_args()

    sqx = catalogue(exportdrv.symbols())
    feeds, held = wanted(), barstore.library()
    missing = [f for f in feeds if f not in sqx]
    todo = stale([f for f in feeds if f in sqx], sqx, held)

    for f in feeds:
        mark = "PULL" if f in todo else "ok  "
        have = held.get(f, {}).get("bars", 0)
        print(f"  {mark} {f:32} library {have:>9,}  SQX {sqx.get(f, {}).get('bars', 0):>9,}")
    for f in missing:
        print(f"  ??   {f:32} SQX does not list it as an M1 feed")
    if a.check or not todo:
        print(f"{len(todo)} feed(s) to pull")
        return

    entries = dict(held)
    for f in todo:
        # One worker start per feed: a second export inside the same JVM overwrites the first.
        written = exportdrv.bars(f, "M1", bar_source(f).parent,
                                 sqx[f]["from"], sqx[f]["to"])
        entries[f] = barstore.store(f, written)
        # Written after EVERY feed, not once at the end: a pull of thirteen feeds is tens of
        # minutes and whatever interrupts it used to leave gigabytes on disk that the
        # manifest had never heard of, so the next run downloaded them all again.
        manifest.write(DATA / "bars",
                       {"timeframe": "M1", "window": "each feed over its own full range",
                        "synced": date.today().isoformat()},
                       "sync_bars.py", entries)
        print(f"  {f:32} {entries[f]['bars']:>9,} bars  "
              f"{entries[f]['from']} → {entries[f]['to']}  {bar_source(f).stat().st_size/1e6:.0f} MB")

    print(f"{len(todo)} feed(s) refreshed; library holds {len(entries)}")


if __name__ == "__main__":
    main()
