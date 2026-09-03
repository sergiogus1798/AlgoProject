"""gen_example.py — worked example + copyable template for authoring a batch.

This is the pattern every batch follows. Copy it, change the block list, re-run.
It builds an RSI mean-reversion pair (long when RSI crosses up out of oversold,
short when it crosses down out of overbought), writes XML, and tells you how to
validate.

Run:
  python examples/gen_example.py catalog.json out.xml

Prereq: run bootstrap first to produce catalog.json:
  python engine/bootstrap.py /path/to/global/config.xml
"""

from __future__ import annotations

import sys
from pathlib import Path

# make `from engine...` work no matter where this is run from
SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.emit import Catalog
from engine.grammar import (
    crosses_above, crosses_below, make_block, int_param, double_param, esc, wrap_batch,
)


def build(cat: Catalog) -> list[str]:
    blocks = []

    # --- one long/short pair: RSI crossing out of an extreme -----------------
    # outer optimizer knobs: #Int2# = RSI period, #Double3# = oversold level,
    # #Double4# = overbought level. The atom binds #Period# to #Int2#; the
    # Number operand binds to the #DoubleN# level. Validator check 4 enforces
    # that every #IntN#/#DoubleN# referenced below is declared in `params`.
    long_key, short_key = "CBlock_ExRSIReclaimOversold", "CBlock_ExRSIFailOverbought"
    period_knob = int_param("#Int2#", "RSI Period", "14", "2", "50")
    os_knob = double_param("#Double3#", "Oversold", "30", "5", "45", "1")
    ob_knob = double_param("#Double4#", "Overbought", "70", "55", "95", "1")

    blocks.append(make_block(
        key=long_key,
        name="ExRSIReclaimOversold",
        display=esc("RSI(@Chart@14) crosses above 30"),
        category="MeanReversion_user",
        help_text=esc("Long: RSI crosses back up through the oversold level."),
        opposite=short_key,
        params=period_knob + os_knob,
        contents=crosses_above(cat.atom("RSI", period="#Int2#"), cat.number("30", bind="#Double3#")),
    ))
    blocks.append(make_block(
        key=short_key,
        name="ExRSIFailOverbought",
        display=esc("RSI(@Chart@14) crosses below 70"),
        category="MeanReversion_user",
        help_text=esc("Short: RSI crosses back down through the overbought level."),
        opposite=long_key,
        params=period_knob + ob_knob,
        contents=crosses_below(cat.atom("RSI", period="#Int2#"), cat.number("70", bind="#Double4#")),
    ))

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
