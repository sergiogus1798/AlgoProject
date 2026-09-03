"""gen_complex_breakout.py — COMPLEX (compound) breakout blocks, session/time gated.

User ask: new breakout blocks, NOT the simple single-signal ones — compound conditions,
and use the Bar&Time blocks (BarHour / BarDayOfWeek). So every block here is a genuine
multi-clause AND: a price/channel breakout CORE (read confirmed, shift>=1) AND one or more
gates (time-of-day window, volatility squeeze, range-expansion, extreme-recency).

Edge-hygiene kept intact even though we dropped the single-signal default:
  - breakout/channel/level cores read at shift>=1 (no look-ahead),
  - Close / BarRange / BarHour are evaluated on the current bar (shift 0) — legitimate, their
    value is known at the bar's close / from the clock, and assess.py does not flag them
    (they are priceValue/priceRange/other, not categoryType="indicator").

Run:  python gen_complex_breakout.py catalog.json complex_breakout.xml
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.emit import Catalog
from engine.grammar import (
    and_op, crosses_above, crosses_below, is_greater, is_lower,
    make_block, int_param, double_param, esc, wrap_batch,
)

CAT = "BreakoutComplex_user"


def build(cat: Catalog) -> list[str]:
    B = []

    # shared knob builders ----------------------------------------------------
    def period_knob(k="#Int2#", d="20", lo="10", hi="120"):
        return int_param(k, "Channel Period", d, lo, hi)

    def startH(k="#Double3#", d="7"):
        return double_param(k, "Session Start Hour", d, "0", "23", "1")

    def endH(k="#Double4#", d="20"):
        return double_param(k, "Session End Hour", d, "0", "23", "1")

    # helper: a BarHour session window as two AND clauses (current bar, shift 0)
    def in_session(lo_knob="#Double3#", hi_knob="#Double4#"):
        return (
            is_greater(cat.atom("BarHour", shift="1"), cat.number("7", bind=lo_knob)),
            is_lower(cat.atom("BarHour", shift="1"), cat.number("20", bind=hi_knob)),
        )

    # === Pair 1 — Donchian channel break, inside a session window ============
    lk, sk = "CBlock_DonchianSessionBreakUp", "CBlock_DonchianSessionBreakDown"
    B.append(make_block(
        key=lk, name="DonchianSessionBreakUp",
        display=esc("Close crosses above Highest(High,N)[1]  AND  startH < Hour < endH"),
        category=CAT, opposite=sk,
        help_text=esc("Complex breakout: Close breaks the prior N-bar high (confirmed channel, "
                      "shift 1) only when the bar's hour is inside the session window. Hours are "
                      "broker server-time — calibrate."),
        params=period_knob() + startH() + endH(),
        contents=and_op(
            crosses_above(cat.atom("Close", shift="1"),
                          cat.atom("Highest", computedfrom="2", period="#Int2#", shift="2")),
            *in_session(),
        )))
    B.append(make_block(
        key=sk, name="DonchianSessionBreakDown",
        display=esc("Close crosses below Lowest(Low,N)[1]  AND  startH < Hour < endH"),
        category=CAT, opposite=lk,
        help_text=esc("Complex breakout (short): Close breaks the prior N-bar low inside the "
                      "session window. Broker server-time — calibrate."),
        params=period_knob() + startH() + endH(),
        contents=and_op(
            crosses_below(cat.atom("Close", shift="1"),
                          cat.atom("Lowest", computedfrom="3", period="#Int2#", shift="2")),
            *in_session(),
        )))

    # === Pair 2 — Prev-day break, after the open hour, OUT OF a quiet regime ==
    lk, sk = "CBlock_PrevDayBreakSqueezeUp", "CBlock_PrevDayBreakSqueezeDown"
    afterH = double_param("#Double3#", "Trade After Hour", "8", "0", "23", "1")
    volCeil = double_param("#Double4#", "ATR%Rank Quiet Ceiling", "40", "5", "90", "5")
    B.append(make_block(
        key=lk, name="PrevDayBreakSqueezeUp",
        display=esc("Close crosses above prior-day High  AND  Hour > afterH  AND  ATR%Rank < ceil"),
        category=CAT, opposite=sk,
        help_text=esc("Compound: break of the prior-day high, taken only after the open hour and "
                      "only when volatility is compressed (ATR Percent Rank below the ceiling = a "
                      "squeeze-then-break). HighD read confirmed (shift 1)."),
        params=afterH + volCeil,
        contents=and_op(
            crosses_above(cat.atom("Close", shift="1"), cat.atom("HighD", shift="2")),
            is_greater(cat.atom("BarHour", shift="1"), cat.number("8", bind="#Double3#")),
            is_lower(cat.atom("ATRPercentRank", atrperiod="14", lenght="100", shift="1"),
                     cat.number("40", bind="#Double4#")),
        )))
    B.append(make_block(
        key=sk, name="PrevDayBreakSqueezeDown",
        display=esc("Close crosses below prior-day Low  AND  Hour > afterH  AND  ATR%Rank < ceil"),
        category=CAT, opposite=lk,
        help_text=esc("Compound (short): break of the prior-day low after the open hour, out of a "
                      "compressed-volatility regime."),
        params=afterH + volCeil,
        contents=and_op(
            crosses_below(cat.atom("Close", shift="1"), cat.atom("LowD", shift="2")),
            is_greater(cat.atom("BarHour", shift="1"), cat.number("8", bind="#Double3#")),
            is_lower(cat.atom("ATRPercentRank", atrperiod="14", lenght="100", shift="1"),
                     cat.number("40", bind="#Double4#")),
        )))

    # === Pair 3 — FRESH N-bar extreme (HighestIndex) inside a session window ==
    # HighestIndex==0 => the confirmed bar IS the N-bar high. is_lower(idx, 1) catches it.
    lk, sk = "CBlock_FreshHighSessionUp", "CBlock_FreshLowSessionDown"
    B.append(make_block(
        key=lk, name="FreshHighSessionUp",
        display=esc("HighestIndex(High,N)[1] = 0 (fresh N-bar high)  AND  startH < Hour < endH"),
        category=CAT, opposite=sk,
        help_text=esc("Compound recency breakout: the most recent confirmed bar set a fresh N-bar "
                      "HIGH (HighestIndex of High is 0), taken only inside the session window. "
                      "HighestIndex is an ignoreInBuilder atom — the random builder can't make this."),
        params=period_knob() + startH() + endH(),
        contents=and_op(
            is_lower(cat.atom("HighestIndex", computedfrom="2", period="#Int2#", shift="1"),
                     cat.number("1")),
            *in_session(),
        )))
    B.append(make_block(
        key=sk, name="FreshLowSessionDown",
        display=esc("LowestIndex(Low,N)[1] = 0 (fresh N-bar low)  AND  startH < Hour < endH"),
        category=CAT, opposite=lk,
        help_text=esc("Compound recency breakout (short): the most recent confirmed bar set a fresh "
                      "N-bar LOW inside the session window."),
        params=period_knob() + startH() + endH(),
        contents=and_op(
            is_lower(cat.atom("LowestIndex", computedfrom="3", period="#Int2#", shift="1"),
                     cat.number("1")),
            *in_session(),
        )))

    # === Pair 4 — Channel break CONFIRMED by a range-expansion bar, skip early =
    lk, sk = "CBlock_RangeExpBreakUp", "CBlock_RangeExpBreakDown"
    expWin = int_param("#Int3#", "Expansion Window", "10", "3", "50")
    skipH = double_param("#Double4#", "Trade After Hour", "9", "0", "23", "1")
    B.append(make_block(
        key=lk, name="RangeExpBreakUp",
        display=esc("Close crosses above Highest(High,N)[1]  AND  BarRange > BiggestRange(M)[1]  AND  Hour > afterH"),
        category=CAT, opposite=sk,
        help_text=esc("Compound: an N-bar high break that is ALSO a volatility-expansion bar "
                      "(current range exceeds the biggest range of the prior M bars), taken after "
                      "the early session. Channel and expansion baseline read confirmed (shift 1)."),
        params=period_knob() + expWin + skipH,
        contents=and_op(
            crosses_above(cat.atom("Close", shift="1"),
                          cat.atom("Highest", computedfrom="2", period="#Int2#", shift="2")),
            is_greater(cat.atom("BarRange", shift="1"),
                       cat.atom("BiggestRange", period="#Int3#", shift="2")),
            is_greater(cat.atom("BarHour", shift="1"), cat.number("9", bind="#Double4#")),
        )))
    B.append(make_block(
        key=sk, name="RangeExpBreakDown",
        display=esc("Close crosses below Lowest(Low,N)[1]  AND  BarRange > BiggestRange(M)[1]  AND  Hour > afterH"),
        category=CAT, opposite=lk,
        help_text=esc("Compound (short): an N-bar low break that is also a range-expansion bar, "
                      "taken after the early session."),
        params=period_knob() + expWin + skipH,
        contents=and_op(
            crosses_below(cat.atom("Close", shift="1"),
                          cat.atom("Lowest", computedfrom="3", period="#Int2#", shift="2")),
            is_greater(cat.atom("BarRange", shift="1"),
                       cat.atom("BiggestRange", period="#Int3#", shift="2")),
            is_greater(cat.atom("BarHour", shift="1"), cat.number("9", bind="#Double4#")),
        )))

    # === Pair 5 — Channel break, only mid-week (BarDayOfWeek gate) ============
    # Project convention (existing Session blocks): dow 1..5, >1 skips week-open, <5 skips week-close.
    lk, sk = "CBlock_MidWeekBreakUp", "CBlock_MidWeekBreakDown"
    dowLo = double_param("#Double3#", "Day-of-Week Low Bound", "1", "0", "6", "1")
    dowHi = double_param("#Double4#", "Day-of-Week High Bound", "5", "0", "6", "1")
    B.append(make_block(
        key=lk, name="MidWeekBreakUp",
        display=esc("Close crosses above Highest(High,N)[1]  AND  dowLo < DayOfWeek < dowHi"),
        category=CAT, opposite=sk,
        help_text=esc("Compound: N-bar high break only on mid-week bars (skips the week-open and "
                      "week-close days, where breakouts whipsaw). Day numbering is broker-specific "
                      "(this assumes Mon=1..Fri=5) — calibrate."),
        params=period_knob() + dowLo + dowHi,
        contents=and_op(
            crosses_above(cat.atom("Close", shift="1"),
                          cat.atom("Highest", computedfrom="2", period="#Int2#", shift="2")),
            is_greater(cat.atom("BarDayOfWeek", shift="1"), cat.number("1", bind="#Double3#")),
            is_lower(cat.atom("BarDayOfWeek", shift="1"), cat.number("5", bind="#Double4#")),
        )))
    B.append(make_block(
        key=sk, name="MidWeekBreakDown",
        display=esc("Close crosses below Lowest(Low,N)[1]  AND  dowLo < DayOfWeek < dowHi"),
        category=CAT, opposite=lk,
        help_text=esc("Compound (short): N-bar low break only on mid-week bars."),
        params=period_knob() + dowLo + dowHi,
        contents=and_op(
            crosses_below(cat.atom("Close", shift="1"),
                          cat.atom("Lowest", computedfrom="3", period="#Int2#", shift="2")),
            is_greater(cat.atom("BarDayOfWeek", shift="1"), cat.number("1", bind="#Double3#")),
            is_lower(cat.atom("BarDayOfWeek", shift="1"), cat.number("5", bind="#Double4#")),
        )))

    # === Single — Intraday COIL gate: no fresh extreme either side, in session =
    # symmetric (CBlock_null): arms breakout entries during a session-time contraction.
    B.append(make_block(
        key="CBlock_IntradayCoilArm", name="IntradayCoilArm",
        display=esc("HighestIndex(High,N)[1] > k  AND  LowestIndex(Low,N)[1] > k  AND  startH < Hour < endH"),
        category=CAT, opposite="CBlock_null",
        help_text=esc("Compound coil gate (symmetric, non-directional): neither a fresh N-bar high "
                      "nor a fresh N-bar low printed in the last k bars (both extreme-indices are "
                      "old) AND inside the session window = an intraday contraction that arms a "
                      "breakout. Pair with a directional breakout in strategy assembly."),
        params=period_knob() + double_param("#Double3#", "Min Bars Since Extreme", "5", "2", "30", "1")
               + startH("#Double4#", "8") + endH("#Double5#", "16"),
        contents=and_op(
            is_greater(cat.atom("HighestIndex", computedfrom="2", period="#Int2#", shift="1"),
                       cat.number("5", bind="#Double3#")),
            is_greater(cat.atom("LowestIndex", computedfrom="3", period="#Int2#", shift="1"),
                       cat.number("5", bind="#Double3#")),
            is_greater(cat.atom("BarHour", shift="1"), cat.number("8", bind="#Double4#")),
            is_lower(cat.atom("BarHour", shift="1"), cat.number("16", bind="#Double5#")),
        )))

    return B


def main(argv):
    catalog_path = argv[0] if argv else "catalog.json"
    out_path = argv[1] if len(argv) > 1 else "complex_breakout.xml"
    cat = Catalog(catalog_path)
    xml = wrap_batch(build(cat))
    Path(out_path).write_text(xml, encoding="utf-8")
    nblocks = xml.count('type="Condition"')
    print(f"wrote {out_path} ({nblocks} blocks)")
    print(f"validate: python engine/validate.py {out_path} --catalog {catalog_path}")
    print(f"assess  : python engine/assess.py {out_path} --catalog {catalog_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
