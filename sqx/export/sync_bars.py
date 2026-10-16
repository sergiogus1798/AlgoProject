#!/usr/bin/env python3
"""Keep the M1 bar library in step with SQX: decode its M1 .dat files for what is missing or has grown."""

import argparse
from datetime import date

from core import barstore, manifest
from core.assetdata import symbols
from core.assetmarkets import markets
from core.datapaths import bar_file
from core.paths import DATA, bar_source
from core.barstore import BarEntry


def wanted() -> list[str]:
    """Every feed the project should hold bars for.

    Returns:
        Feed names, sorted. The declaration in assets/_markets.yaml drives it — every base asset
        and every market it is retested on — plus whatever the library already holds, so a
        feed pulled once keeps being refreshed after its asset leaves the declaration.
    """
    declared = [markets(s) for s in symbols()]
    feeds = {spec["main"] for spec in declared if spec}
    feeds |= {
        m["feed"]
        for spec in declared
        if spec
        for category in spec.get("categories", {}).values()
        for m in category
    }
    feeds |= {d.name for d in (DATA / "bars").iterdir() if bar_source(d.name).exists()}
    return sorted(feeds)


def stale(feeds: list[str], held: dict[str, BarEntry]) -> list[str]:
    """Which feeds have to be decoded again from their .dat.

    Args:
        feeds: What wanted() returned, only those whose .dat exists.
        held: What barstore.library() returned.

    Returns:
        The feeds the library is missing, plus the ones whose .dat has another size than
        the one the library was decoded from. The size moves whenever SQX's data does —
        growth, backfill or a rewritten middle alike — and an entry written before the
        library was decoded from the .dat has no size, so it is decoded once.
    """
    return [
        f for f in feeds if held.get(f, {}).get("dat") != bar_file(f).stat().st_size
    ]


def main() -> None:
    """Decode every missing or outdated feed's M1 .dat into the library."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--check", action="store_true", help="report what is stale, decode nothing"
    )
    a = ap.parse_args()

    feeds, held = wanted(), barstore.library()
    missing = [f for f in feeds if not bar_file(f).exists()]
    todo = stale([f for f in feeds if f not in missing], held)

    for f in feeds:
        if f in missing:
            print(f"  ??   {f:32} no M1 .dat under SQX's History")
            continue
        mark = "PULL" if f in todo else "ok  "
        print(f"  {mark} {f:32} library {held.get(f, {}).get('bars', 0):>9,}")
    if a.check or not todo:
        print(f"{len(todo)} feed(s) to decode")
        return

    entries = dict(held)
    for f in todo:
        entries[f] = barstore.store(f)
        # Written after EVERY feed, not once at the end: whatever interrupts a run of
        # thirteen feeds must not leave Parquet that the manifest has never heard of.
        manifest.write(
            DATA / "bars",
            {
                "timeframe": "M1",
                "window": "each feed over its own full range",
                "synced": date.today().isoformat(),
            },
            "sync_bars.py",
            entries,
        )
        print(
            f"  {f:32} {entries[f]['bars']:>9,} bars  "
            f"{entries[f]['from']} → {entries[f]['to']}  {bar_source(f).stat().st_size / 1e6:.0f} MB"
        )

    print(f"{len(todo)} feed(s) refreshed; library holds {len(entries)}")


if __name__ == "__main__":
    main()
