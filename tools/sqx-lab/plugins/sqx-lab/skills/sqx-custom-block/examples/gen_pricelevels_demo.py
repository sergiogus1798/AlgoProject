"""gen_pricelevels_demo.py — research-front-half DEMO batch.

Authors the native, lowest-risk subset of the price-action/price-levels specs
that the research agent proposed and check_specs.py gated as BUILDABLE:
6 long/short pairs + 2 symmetric singles = 14 blocks, all prior-period OHLC
breaks (native priceValue atoms, no multi-output, no intraday-time params).

Left for a follow-up (flagged BUILDABLE* / intraday by the gate):
  PivotR1Break, PivotPointBias  -> Pivots is multi-output, pick #Line# first
  OpeningRangeBreakout          -> intraday HighestInRange + server-time window

Run:
  python gen_pricelevels_demo.py catalog.json pricelevels_demo.xml
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.emit import Catalog
from engine.grammar import (
    crosses_above, crosses_below, is_greater, is_lower, make_block, esc, wrap_batch,
)

CAT = "PriceLevels_user"


def build(cat: Catalog) -> list[str]:
    blocks: list[str] = []

    # current-bar operands (shift 0); prior-period levels (shift 1 = last completed)
    def now(key):   return cat.atom(key, shift="0")
    def prev(key):  return cat.atom(key, shift="1")

    def pair(base_long, base_short, disp_long, disp_short, help_long, help_short,
             c_long, c_short):
        lk, sk = f"CBlock_{base_long}", f"CBlock_{base_short}"
        blocks.append(make_block(
            key=lk, name=base_long, display=esc(disp_long), category=CAT,
            help_text=esc(help_long), opposite=sk, params="", contents=c_long))
        blocks.append(make_block(
            key=sk, name=base_short, display=esc(disp_short), category=CAT,
            help_text=esc(help_short), opposite=lk, params="", contents=c_short))

    def single(base, disp, help_text, contents):
        blocks.append(make_block(
            key=f"CBlock_{base}", name=base, display=esc(disp), category=CAT,
            help_text=esc(help_text), opposite="CBlock_null", params="", contents=contents))

    # 1 — prior-DAY high/low break (continuation trigger)
    pair("BreakPriorDayHigh", "BreakPriorDayLow",
         "Close crosses above prior-day High",
         "Close crosses below prior-day Low",
         "Long: breakout above yesterday's high (Crabel prior-day level break).",
         "Short: breakdown below yesterday's low.",
         crosses_above(now("Close"), prev("HighD")),
         crosses_below(now("Close"), prev("LowD")))

    # 2 — prior-WEEK high/low break (swing-timeframe breakout)
    pair("BreakPriorWeekHigh", "BreakPriorWeekLow",
         "Close crosses above prior-week High",
         "Close crosses below prior-week Low",
         "Long: takes out last week's high (swing higher-high).",
         "Short: takes out last week's low (swing lower-low).",
         crosses_above(now("Close"), prev("HighW")),
         crosses_below(now("Close"), prev("LowW")))

    # 3 — prior-MONTH high/low break (time-series momentum, best on D1)
    pair("BreakPriorMonthHigh", "BreakPriorMonthLow",
         "Close crosses above prior-month High",
         "Close crosses below prior-month Low",
         "Long: breaks last month's high (TSMOM regime; best on D1).",
         "Short: breaks last month's low.",
         crosses_above(now("Close"), prev("HighM")),
         crosses_below(now("Close"), prev("LowM")))

    # 4 — HOLDING above/below the prior-day level (state filter, not the event)
    pair("HoldAbovePriorDayHigh", "HoldBelowPriorDayLow",
         "Close > prior-day High (acceptance above)",
         "Close < prior-day Low (acceptance below)",
         "Filter long: price sustaining above yesterday's high (resistance->support flip).",
         "Filter short: price sustaining below yesterday's low.",
         is_greater(now("Close"), prev("HighD")),
         is_lower(now("Close"), prev("LowD")))

    # 5 — FAILED break of the prior-day level (Turtle-Soup fade)
    pair("FailPriorDayHigh", "FailPriorDayLow",
         "Close crosses back below prior-day High (failed breakout -> fade short)",
         "Close crosses back above prior-day Low (failed breakdown -> fade long)",
         "Short fade: a prior-day-high break that fails and re-crosses down (Turtle Soup).",
         "Long fade: a prior-day-low break that fails and re-crosses up.",
         crosses_below(now("Close"), prev("HighD")),
         crosses_above(now("Close"), prev("LowD")))

    # 6 — prior-DAY close (settlement) reclaim / loss
    pair("ReclaimPriorDayClose", "LosePriorDayClose",
         "Close crosses above prior-day Close (settlement reclaim)",
         "Close crosses below prior-day Close (settlement loss)",
         "Long: reclaims yesterday's settlement (close-to-close momentum sign flip up).",
         "Short: loses yesterday's settlement.",
         crosses_above(now("Close"), prev("CloseD")),
         crosses_below(now("Close"), prev("CloseD")))

    # singles — symmetric compression / expansion setup gates (no direction)
    single("InsideDayCompression",
           "Current High < prior-day High (inside-bar compression proxy)",
           "Setup gate: today's high inside yesterday's high -> volatility contraction "
           "(Crabel inside day). Upper-bound proxy; strict inside day also needs Low > prior Low.",
           is_lower(now("High"), prev("HighD")))

    single("OutsideDayExpansion",
           "Current High > prior-day High (range-expansion proxy)",
           "Setup gate: today's high exceeds yesterday's high -> volatility expansion "
           "(Crabel outside-bar component). Upper-bound proxy.",
           is_greater(now("High"), prev("HighD")))

    return blocks


def main(argv):
    catalog_path = argv[0] if argv else "catalog.json"
    out_path = argv[1] if len(argv) > 1 else "pricelevels_demo.xml"
    cat = Catalog(catalog_path)
    xml = wrap_batch(build(cat))
    Path(out_path).write_text(xml, encoding="utf-8")
    print(f"wrote {out_path} ({xml.count('oppositeBlockKey')} blocks)")
    print(f"validate:\n  python engine/validate.py {out_path} --catalog {catalog_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
