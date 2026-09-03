"""gen_gold_groups.py — 4 hybrid Condition pools for the XAUUSD template wave (v2).

v2 (2026-07-18, after the 5-min smoke test):
  * ALL numeric knobs are unfrozen (optimize="default") so the Builder searches
    calibration — v1 froze session hours / coil percentiles at authoring defaults,
    which collapsed trade frequency on gold (AvgTradesPerMonth>2 is a hard gate).
  * Filt_SessionGold drops the fixed-hour session blocks (SessionLondon/NewYork/
    Overlap have NO knobs — hours are baked into the rule, uncalibratable, true only
    2–8h/day → frequency killers in the filter slot). The session thesis lives in the
    TRIGGERS (DonchianSessionBreakUp carries optimizable session start/end hours).
    The filter slot now pools direction/bias conditions (true ~half the bars).

  Filt_SessionGold      intraday direction/bias filters (long)
  Brk_SessionORB_Long   session-anchored breakout triggers (long, hours searchable)
  Filt_VolCoil          volatility-contraction (coil) regime filters
  Brk_PrevLevels_Long   prior-period level-break triggers (long)

Run (from the skill folder):
  python gen_gold_groups.py
  python engine/validate.py gold_groups.xml --catalog catalog.json
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.groups import load_catalog, hybrid_ref, make_group, wrap_groups  # noqa: E402

POOLS = [
    ("Filt_SessionGold", "Filters", [
        "SessionOpenBull", "DayOpenBull", "AboveVWAPByATR", "AboveDailyMid",
        "DayOpenReclaimUp", "CloseVWAPHeldUp", "AbovePrevMid",
    ]),
    ("Brk_SessionORB_Long", "Breakout", [
        "ORBBreakoutUp", "DonchianSessionBreakUp", "FreshHighSessionUp",
        "SessionHighBreak", "RangeExpBreakUp", "ThrustUp", "ChanBreakVolExpandUp",
    ]),
    ("Filt_VolCoil", "Filters", [
        "ATRPctRankCoiled", "BBSqueezeTight", "NR4Coil", "RangeContractionBar",
        "ATRContracting", "NarrowRangeBar", "InsideBar", "StdDevContracting",
    ]),
    ("Brk_PrevLevels_Long", "Breakout", [
        "PrevDayHighBreak", "PrevWeekHighBreak", "PrevDayHighExceed",
        "CloseAbovePrevHigh", "PrevMonthHighBreak", "PivotR1Break",
        "PivotR2Break", "PrevDayHighCross",
    ]),
]

NUMERIC = {"int", "double", "period"}


def numeric_knobs(block_el):
    """optimize spec unfreezing every numeric Param that has a real min/max range."""
    out = {}
    for p in block_el.findall("Param"):
        if p.get("type") in NUMERIC and p.get("minValue") not in (None, "null"):
            out[p.get("key")] = "default"
    return out


def main() -> None:
    _, _, B = load_catalog(str(SKILL_ROOT / "catalog.json"))
    groups = []
    for name, category, keys in POOLS:
        missing = [k for k in keys if "CBlock_" + k not in B]
        if missing:
            raise SystemExit(f"{name}: keys not in catalog: {missing}")
        items, unfrozen = [], 0
        for k in keys:
            blk = B["CBlock_" + k]
            opt = numeric_knobs(blk)
            unfrozen += len(opt)
            items.append(hybrid_ref(blk, optimize=opt) if opt else hybrid_ref(blk))
        groups.append(make_group(name, "Condition", items, category=category))
        print(f"  {name:22s} {len(keys)} items  [{category}]  knobs unfrozen: {unfrozen}")
    out = SKILL_ROOT / "gold_groups.xml"
    out.write_text(wrap_groups(groups), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
