"""gen_pricelevel_example.py — worked example for the PRICE-LEVEL block type.

A Price-level block RETURNS A PRICE (a stop / target / entry / breakout reference),
not a true/false signal. Use `make_price_level` (not `make_block`); the <Contents>
is a single VALUE expression — one price atom, or an arithmetic tree over atoms +
cat.number — with NO and_op/comparison wrapper.

This builds the three canonical shapes:
  1. a volatility BAND pair   — HMA(n) +/- k*ATR        (arithmetic over indicators)
  2. an OHLC ANCHOR           — prior-day High/Low + current-week open
  3. an adaptive TRAIL        — SuperTrend line

Run:
  python examples/gen_pricelevel_example.py catalog.json out.xml
  python engine/validate.py out.xml --catalog catalog.json

(Atom keys below are the common native ones; if your install names one differently,
`cat.search("...")` finds the real key — the catalog is the source of truth.)
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.emit import Catalog
from engine.grammar import (
    make_price_level, plus, minus, mult, int_param, double_param, esc, wrap_batch,
)


def build(cat: Catalog) -> list[str]:
    blocks = []

    # 1 — BAND pair: HMA(n) +/- k*ATR. Mirror pair (upper <-> lower).
    #     #Int2# = HMA period, #Int3# = ATR period, #Double4# = ATR multiplier.
    hi, lo = "CBlock_ExHMAUpperBand", "CBlock_ExHMALowerBand"
    band_knobs = (int_param("#Int2#", "HMA Period", "20", "5", "200", "5")
                  + int_param("#Int3#", "ATR Period", "14", "5", "50", "5")
                  + double_param("#Double4#", "ATR Mult", "2", "0.5", "5", "0.1"))
    blocks.append(make_price_level(
        key=hi, name="ExHMAUpperBand", display=esc("HMA + k*ATR (upper band)"),
        category="PriceLevels_user", help_text=esc("Upper volatility band: HMA(n) + k*ATR."),
        opposite=lo, params=band_knobs,
        contents=plus(cat.atom("HullMovingAverage", period="#Int2#"),
                      mult(cat.number("2", bind="#Double4#"), cat.atom("ATR", period="#Int3#")))))
    blocks.append(make_price_level(
        key=lo, name="ExHMALowerBand", display=esc("HMA - k*ATR (lower band)"),
        category="PriceLevels_user", help_text=esc("Lower volatility band: HMA(n) - k*ATR."),
        opposite=hi, params=band_knobs,
        contents=minus(cat.atom("HullMovingAverage", period="#Int2#"),
                       mult(cat.number("2", bind="#Double4#"), cat.atom("ATR", period="#Int3#")))))

    # 2 — OHLC ANCHOR: a single price atom returned as a level.
    #     Prior-day high/low = shift 1 (last CLOSED period), mirror-paired.
    dh, dl = "CBlock_ExPrevDayHigh", "CBlock_ExPrevDayLow"
    blocks.append(make_price_level(
        key=dh, name="ExPrevDayHigh", display=esc("Previous day's high"),
        category="PriceLevels_user", help_text=esc("Prior-day high as a price level."),
        opposite=dl, params="", contents=cat.atom("HighD", shift="1")))
    blocks.append(make_price_level(
        key=dl, name="ExPrevDayLow", display=esc("Previous day's low"),
        category="PriceLevels_user", help_text=esc("Prior-day low as a price level."),
        opposite=dh, params="", contents=cat.atom("LowD", shift="1")))
    #     Current-week OPEN at shift 0 is legitimate (fixed at week start = NOT
    #     look-ahead) — the one OHLC case where allow_shift0=True is correct.
    blocks.append(make_price_level(
        key="CBlock_ExThisWeekOpen", name="ExThisWeekOpen", display=esc("Current week's open"),
        category="PriceLevels_user",
        help_text=esc("This week's open (fixed at week start; shift 0 is not look-ahead)."),
        opposite="CBlock_null", params="",
        contents=cat.atom("OpenW", shift="0", allow_shift0=True)))

    # 3 — adaptive TRAIL: a trend/trail indicator returned as a dynamic level.
    #     Single line (it flips sides on its own) -> solo, opposite=CBlock_null.
    blocks.append(make_price_level(
        key="CBlock_ExSuperTrendLevel", name="ExSuperTrendLevel",
        display=esc("SuperTrend trailing line"), category="PriceLevels_user",
        help_text=esc("SuperTrend ATR trail as a dynamic stop level (settled shift 1)."),
        opposite="CBlock_null",
        params=int_param("#Int2#", "ATR Period", "24", "2", "240")
        + double_param("#Double3#", "ATR Mult", "3", "0.5", "10", "0.1"),
        contents=cat.atom("SuperTrend", atrperiod="#Int2#", atrmult="#Double3#")))

    return blocks


def main(argv):
    catalog_path = argv[0] if argv else "catalog.json"
    out_path = argv[1] if len(argv) > 1 else "out.xml"
    cat = Catalog(catalog_path)
    xml = wrap_batch(build(cat))
    Path(out_path).write_text(xml, encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"validate with:\n  python engine/validate.py {out_path} --catalog {catalog_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
