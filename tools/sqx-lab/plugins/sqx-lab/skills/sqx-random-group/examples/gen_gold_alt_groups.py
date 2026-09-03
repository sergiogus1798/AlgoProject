"""gen_gold_alt_groups.py — creative second-wave pools for XAUUSD (from existing blocks).

Thesis (from docs/xauusd-template-ideas.md §3): 17 straight years of official-sector
buying puts a persistent bid under gold dips — so alongside the breakout wave, build a
DIP-BUY archetype: a liquidity sweep of a prior low that gets RECLAIMED, entered long.
Filtered either by classic trend direction (fleet group, referenced not modified) or by
a statistical trend-quality pool (Hurst persistence, Kaufman efficiency, entropy) that
measures "is this tape trending" without naming a direction.

  Brk_SweepReclaim_Long   sweep/reclaim + failed-gap + bullish-reversal-bar triggers
  Filt_TrendQuality       statistical trend-quality regime filters

All numeric knobs unfrozen (optimize="default") per the v2 lesson. Existing blocks only.

Run (from the skill folder):
  python gen_gold_alt_groups.py
  python engine/validate.py gold_alt_groups.xml --catalog catalog.json
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.groups import load_catalog, hybrid_ref, make_group, wrap_groups  # noqa: E402

POOLS = [
    ("Brk_SweepReclaim_Long", "Breakout", [
        "PrevDayLowSweep", "WeekLowSweep", "GapBelowLowReclaim", "FailedGapDownBull",
        "PrevDayCloseReclaimUp", "SwingFailureBullish", "RSI2SnapBackLong",
        "LaguerreTurnUpFromOS",
    ]),
    ("Filt_TrendQuality", "Filters", [
        "HurstPersistent", "KERTrending", "ADXTrendStrong", "ADXregimeHeldUp",
        "EntropyDirectional", "CSSATrending", "TotalPowerStrongRegime",
    ]),
]

NUMERIC = {"int", "double", "period"}


def numeric_knobs(block_el):
    return {p.get("key"): "default" for p in block_el.findall("Param")
            if p.get("type") in NUMERIC and p.get("minValue") not in (None, "null")}


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
    out = SKILL_ROOT / "gold_alt_groups.xml"
    out.write_text(wrap_groups(groups), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
