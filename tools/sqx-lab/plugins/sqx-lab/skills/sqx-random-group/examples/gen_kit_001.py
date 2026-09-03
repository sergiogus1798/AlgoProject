"""gen_kit_001.py — full 12-pool "strategy-builder kit" for the 2953 install.

Three tiers a template draws from: entry triggers (SameCondition), filters
(SameCondition AND), levels (SameValue). All HYBRID (re-export existing CBlock_*).
Single long-side pools — the builder mirrors shorts via each block's oppositeBlockKey.
Period/int knobs are optimizable (randomValue="default"); multipliers/other knobs frozen.

Run from the skill root:
  python gen_kit_001.py
  python engine/validate.py <OUT> --catalog catalog.json
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.groups import load_catalog, hybrid_ref, make_group, wrap_groups  # noqa: E402

OUT = SKILL_ROOT / "blockGroups_kit_v144_001.xml"

# (group name, group type, group category, [block keys — all long/up-side])
POOLS = [
    # ── Tier 1 · entry triggers (Condition) ──────────────────────────────
    ("EntriesBreakout", "Condition", "Entries", [
        "CBlock_CloseAboveDCUpper_Brk", "CBlock_CloseAboveBBUpper_Brk", "CBlock_CloseAboveKCUpper_Brk",
        "CBlock_CloseAbovePrevDayHigh_Brk", "CBlock_CloseAboveHHLLUpper_Brk", "CBlock_PivotR1Break_Brk",
        "CBlock_RangeExpBreakUp", "CBlock_DonchianSessionBreakUp"]),
    ("EntriesTrend", "Condition", "Entries", [
        "CBlock_EMACrossUp_Trend", "CBlock_HMAGoldenCross_MA", "CBlock_SMAGoldenCross_MA",
        "CBlock_SuperTrendFlipUp_Trend", "CBlock_CloseAboveSAR", "CBlock_AroonCrossUp_Trend",
        "CBlock_IchimokuBull_Trend", "CBlock_VortexBullCross"]),
    ("EntriesMeanRevert", "Condition", "Entries", [
        "CBlock_RSIExitOversold", "CBlock_StochKExitOversold", "CBlock_CCIExitOversold",
        "CBlock_WilliamsRExitOversold", "CBlock_DeMarkerExitOversold", "CBlock_RSI2SnapBackLong",
        "CBlock_ZScoreExitOversold", "CBlock_SmoothedRSIExitOversold"]),
    ("EntriesMomentum", "Condition", "Entries", [
        "CBlock_MACDSignalCrossUp", "CBlock_MACDZeroCrossUp", "CBlock_OSMAZeroCrossUp",
        "CBlock_AwesomeZeroCrossUp", "CBlock_MomentumCrossUp", "CBlock_ROCThrustLong",
        "CBlock_MACDVZoneEntryLong", "CBlock_WaveTrendSignalCrossUp"]),
    # ── Tier 2 · filters / confirmation (Condition) ──────────────────────
    ("FilterTrendDirection", "Condition", "Filters", [
        "CBlock_CloseAboveEMA_MA", "CBlock_CloseAboveKAMA_Trend", "CBlock_CloseAboveSuperTrend",
        "CBlock_EMAFastAboveSlow_MA", "CBlock_EMARibbonUp_Trend", "CBlock_EMARising_MA"]),
    ("FilterRegimeTrending", "Condition", "Filters", [
        "CBlock_ChopTrending", "CBlock_KERTrending", "CBlock_HurstPersistent",
        "CBlock_ADXTrendStrong", "CBlock_CSSATrending", "CBlock_ChopBreakout"]),
    ("FilterVolExpansion", "Condition", "Filters", [
        "CBlock_ATRExpanding_Vol", "CBlock_StdDevExpanding_Vol", "CBlock_BBWidthExpanding_Vol",
        "CBlock_BBSqueezeOff_Vol", "CBlock_ATRPctRankStretched", "CBlock_BBOutsideKC_Vol"]),
    ("FilterSession", "Condition", "Filters", [
        "CBlock_SessionLondon", "CBlock_SessionNewYork", "CBlock_SessionLondonNYOverlap",
        "CBlock_SkipWeekOpen", "CBlock_SkipWeekClose"]),
    # ── Tier 3 · levels (Value, from PriceLevels) ────────────────────────
    ("LevelsTrailingStop", "Value", "Levels", [
        "CBlock_SuperTrendLevel", "CBlock_EfficiencySuperTrendLevel", "CBlock_HalfTrendLevel",
        "CBlock_ParabolicSARLevel", "CBlock_ChandelierLong", "CBlock_GannHiLoLevel",
        "CBlock_SlopeDirectionLineLevel"]),
    ("LevelsVolBands", "Value", "Levels", [
        "CBlock_AsymmetricATRUpper", "CBlock_HighestATRUpperLevel", "CBlock_KamaUpperBand",
        "CBlock_HMAUpperLevel", "CBlock_RegChannelUpper", "CBlock_ZScoreUpperLevel",
        "CBlock_SSLUpperLevel"]),
    ("LevelsPriorPeriod", "Value", "Levels", [
        "CBlock_PrevDayHigh", "CBlock_PrevWeekHigh", "CBlock_PrevMonthHigh", "CBlock_PrevDayClose",
        "CBlock_OpenDLevel", "CBlock_ThisWeekOpen", "CBlock_PrevDayOpen", "CBlock_ThisMonthOpen"]),
    ("LevelsTargets", "Value", "Levels", [
        "CBlock_CamarillaH4", "CBlock_MeasuredMoveUp", "CBlock_ConfluenceCeiling", "CBlock_KamaOhlcLevel"]),
]


def period_opt(block) -> dict:
    """Optimize the period/lookback int knobs (randomValue='default'); freeze the rest
    (deviation, multiplier doubles, #Line# combos, #Chart# data)."""
    opt = {}
    for p in block.findall("Param"):
        if p.get("type") == "int" and p.get("controlType") != "combo" and p.get("key"):
            opt[p.get("key")] = "default"
    return opt


def main():
    _, _, B = load_catalog("catalog.json")
    missing = [k for *_, keys in POOLS for k in keys if k not in B]
    if missing:
        raise SystemExit(f"NOT IN CATALOG ({len(missing)}): {missing}")

    groups = []
    for name, gtype, cat, keys in POOLS:
        items = [hybrid_ref(B[k], optimize=period_opt(B[k])) for k in keys]
        groups.append(make_group(name, gtype, items, category=cat))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(wrap_groups(groups), encoding="utf-8")

    total = sum(len(keys) for *_, keys in POOLS)
    print(f"wrote {OUT}")
    print(f"  {len(groups)} groups, {total} items")
    for name, gtype, _, keys in POOLS:
        print(f"    {name:22s} {gtype:9s} {len(keys)} items")


if __name__ == "__main__":
    main()
