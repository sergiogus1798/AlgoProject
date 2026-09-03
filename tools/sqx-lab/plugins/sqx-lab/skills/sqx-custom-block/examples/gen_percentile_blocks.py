"""gen_percentile_blocks.py — MANY percentile-rank / SR-percent-rank breakout blocks.

User ask: combine the percentile-rank operator + breakout Highest/Lowest + SRPercentRank, in
volume. Three themed files:

  1. percentile_indicators.xml   — "X is in the top/bottom P% of its OWN last N values"
       (IsGreaterPercentil / IsLowerPercentil wrapping a curated indicator set). Self-normalising
       extremes = portable across instruments (no absolute level to calibrate).
  2. srpercentrank.xml           — dedicated SRPercentRank + ATRPercentRank blocks
       (50-cross, high/low state, slope, and percentile-of-the-rank meta-extreme).
  3. percentile_breakout_combos.xml — COMPOUND: a Highest/Lowest channel break AND a percentile
       gate (vol / momentum / SR-regime). This is the explicit "combination" ask.

Edge-hygiene: every wrapped indicator and the percentile operator read confirmed (shift>=1); the
channel cores read shift 1; only the compound combos carry the (intended) AND.

Run:  python gen_percentile_blocks.py catalog.json
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.emit import Catalog
from engine.grammar import (
    and_op, crosses_above, crosses_below, is_greater, is_lower, is_rising, is_falling,
    percentile_above, percentile_below, make_block, int_param, double_param, esc, wrap_batch,
)

# ---- indicator tables ------------------------------------------------------
# directional oscillators/momentum: PctHigh = self-relative strong (long), PctLow = weak (short)
DIRECTIONAL = [
    ("RSI", None, "RSI"), ("CCI", None, "CCI"), ("Momentum", None, "Momentum"),
    ("ROC", None, "ROC"), ("AwesomeOscillator", None, "AO"), ("CMMA", None, "CMMA"),
    ("ZScore", None, "ZScore"), ("DisparityIndex", None, "Disparity"), ("DeMarker", None, "DeMarker"),
    ("OSMA", None, "OSMA"), ("MACDV", "0", "MACDV"), ("WaveTrend", "0", "WaveTrend"),
    ("BHErgodic", "0", "BHErgodic"), ("VST", None, "VST"), ("LaguerreRSI", None, "LaguerreRSI"),
    ("SmoothedRSI", "0", "SmoothedRSI"),
]
# non-directional regime gauges: PctHigh = expansion/strong regime, PctLow = compression/quiet
# both are symmetric single blocks (CBlock_null), not long/short opposites.
GAUGES = [
    ("ATR", None, "ATR"), ("StdDev", None, "StdDev"), ("ATRPercent", None, "ATRPercent"),
    ("BBWidthRatio", None, "BBWidth"), ("BarRange", None, "BarRange"), ("ADX", "0", "ADX"),
    ("ChoppinessIndex", None, "Choppiness"), ("HurstExponent", None, "Hurst"),
]

CAT_PCT = "PercentileExtreme_user"
CAT_SR = "SRPercentRank_user"
CAT_COMBO = "PercentileBreakout_user"


def _wrapped(cat, key, line):
    return cat.atom(key, line=line) if line else cat.atom(key)


# === FILE 1 — percentile self-extremes =====================================
def build_indicators(cat) -> list[str]:
    B = []
    bars = int_param("#Int2#", "Lookback Bars", "100", "20", "500")
    pctHi = double_param("#Double3#", "Percentile %", "90", "50", "99.9", "0.5")
    pctLo = double_param("#Double3#", "Percentile %", "10", "0.1", "50", "0.5")

    # directional pairs
    for key, line, nm in DIRECTIONAL:
        lk, sk = f"CBlock_{nm}PctHigh", f"CBlock_{nm}PctLow"
        B.append(make_block(
            key=lk, name=f"{nm}PctHigh",
            display=esc(f"{nm} >= top percentile of its own last N values"),
            category=CAT_PCT, opposite=sk,
            help_text=esc(f"Long/strong: {nm} is in the top P% of its own last N values "
                          f"(self-normalising momentum extreme; no absolute level to calibrate). "
                          f"Read confirmed (shift 1)."),
            params=bars + pctHi,
            contents=percentile_above(_wrapped(cat, key, line), "#Int2#", "#Double3#")))
        B.append(make_block(
            key=sk, name=f"{nm}PctLow",
            display=esc(f"{nm} <= bottom percentile of its own last N values"),
            category=CAT_PCT, opposite=lk,
            help_text=esc(f"Short/weak: {nm} is in the bottom P% of its own last N values."),
            params=bars + pctLo,
            contents=percentile_below(_wrapped(cat, key, line), "#Int2#", "#Double3#")))

    # gauge singles (symmetric)
    for key, line, nm in GAUGES:
        B.append(make_block(
            key=f"CBlock_{nm}PctExpand", name=f"{nm}PctExpand",
            display=esc(f"{nm} >= top percentile of its own last N (expansion/strong regime)"),
            category=CAT_PCT, opposite="CBlock_null",
            help_text=esc(f"Regime gate: {nm} at a self-relative HIGH (top P% of its last N) = "
                          f"expansion / strong-regime state. Non-directional. Shift 1."),
            params=bars + pctHi,
            contents=percentile_above(_wrapped(cat, key, line), "#Int2#", "#Double3#")))
        B.append(make_block(
            key=f"CBlock_{nm}PctQuiet", name=f"{nm}PctQuiet",
            display=esc(f"{nm} <= bottom percentile of its own last N (compression/quiet regime)"),
            category=CAT_PCT, opposite="CBlock_null",
            help_text=esc(f"Regime gate: {nm} at a self-relative LOW (bottom P% of its last N) = "
                          f"compression / quiet-regime state (a coil that often precedes a break). Shift 1."),
            params=bars + pctLo,
            contents=percentile_below(_wrapped(cat, key, line), "#Int2#", "#Double3#")))
    return B


# === FILE 2 — SRPercentRank + ATRPercentRank dedicated =====================
def build_srpct(cat) -> list[str]:
    B = []

    def sr():   # SR Percent Rank, ATR mode, frozen internals (0-100, mid 50)
        return cat.atom("SRPercentRank", mode="2", length="100", atrperiod="14", shift="1")

    def atrr():
        return cat.atom("ATRPercentRank", atrperiod="14", lenght="100", shift="1")

    # SR 50-cross (regime birth)
    B.append(make_block("CBlock_SRPctRankCrossUp50", "SRPctRankCrossUp50",
        esc("SRPercentRank crosses above 50"), CAT_SR, esc("Long: support/resistance percent rank "
        "crosses up through its 50 midline (regime birth)."), "CBlock_SRPctRankCrossDown50",
        double_param("#Double3#", "Midline", "50", "20", "80", "1"),
        crosses_above(sr(), cat.number("50", bind="#Double3#"))))
    B.append(make_block("CBlock_SRPctRankCrossDown50", "SRPctRankCrossDown50",
        esc("SRPercentRank crosses below 50"), CAT_SR, esc("Short: SR percent rank crosses down "
        "through 50."), "CBlock_SRPctRankCrossUp50",
        double_param("#Double3#", "Midline", "50", "20", "80", "1"),
        crosses_below(sr(), cat.number("50", bind="#Double3#"))))

    # SR high / low state
    B.append(make_block("CBlock_SRPctRankHigh", "SRPctRankHigh",
        esc("SRPercentRank > upper level"), CAT_SR, esc("Filter: SR percent rank in its upper band "
        "(price extended vs its support/resistance map)."), "CBlock_SRPctRankLow",
        double_param("#Double3#", "Upper", "80", "55", "99", "1"),
        is_greater(sr(), cat.number("80", bind="#Double3#"))))
    B.append(make_block("CBlock_SRPctRankLow", "SRPctRankLow",
        esc("SRPercentRank < lower level"), CAT_SR, esc("Filter: SR percent rank in its lower band."),
        "CBlock_SRPctRankHigh",
        double_param("#Double3#", "Lower", "20", "1", "45", "1"),
        is_lower(sr(), cat.number("20", bind="#Double3#"))))

    # SR slope
    B.append(make_block("CBlock_SRPctRankRising", "SRPctRankRising",
        esc("SRPercentRank is rising"), CAT_SR, esc("Long: SR percent rank rising (price climbing "
        "its S/R structure)."), "CBlock_SRPctRankFalling", "",
        is_rising(sr(), bars="2", shift="1")))
    B.append(make_block("CBlock_SRPctRankFalling", "SRPctRankFalling",
        esc("SRPercentRank is falling"), CAT_SR, esc("Short: SR percent rank falling."),
        "CBlock_SRPctRankRising", "",
        is_falling(sr(), bars="2", shift="1")))

    # SR percentile-of-the-rank (meta self-extreme)
    bars = int_param("#Int2#", "Lookback Bars", "100", "20", "500")
    B.append(make_block("CBlock_SRPctRankPctHigh", "SRPctRankPctHigh",
        esc("SRPercentRank >= top percentile of its own last N"), CAT_SR, esc("Long: SR percent "
        "rank itself at a self-relative high (top P% of its last N) = unusually strong S/R standing."),
        "CBlock_SRPctRankPctLow", bars + double_param("#Double3#", "Percentile %", "90", "50", "99.9", "0.5"),
        percentile_above(sr(), "#Int2#", "#Double3#")))
    B.append(make_block("CBlock_SRPctRankPctLow", "SRPctRankPctLow",
        esc("SRPercentRank <= bottom percentile of its own last N"), CAT_SR, esc("Short: SR percent "
        "rank at a self-relative low."), "CBlock_SRPctRankPctHigh",
        bars + double_param("#Double3#", "Percentile %", "10", "0.1", "50", "0.5"),
        percentile_below(sr(), "#Int2#", "#Double3#")))

    # ATRPercentRank regime singles
    B.append(make_block("CBlock_ATRPctRankStretched", "ATRPctRankStretched",
        esc("ATRPercentRank > stretched level"), CAT_SR, esc("Vol regime: ATR percent rank high = "
        "volatility stretched (late move / breakout already underway). Non-directional."), "CBlock_null",
        double_param("#Double3#", "Stretched", "70", "55", "99", "1"),
        is_greater(atrr(), cat.number("70", bind="#Double3#"))))
    B.append(make_block("CBlock_ATRPctRankCoiled", "ATRPctRankCoiled",
        esc("ATRPercentRank < coiled level"), CAT_SR, esc("Vol regime: ATR percent rank low = "
        "volatility coiled (squeeze; primes a breakout). Non-directional."), "CBlock_null",
        double_param("#Double3#", "Coiled", "30", "1", "45", "1"),
        is_lower(atrr(), cat.number("30", bind="#Double3#"))))
    B.append(make_block("CBlock_ATRPctRankRising", "ATRPctRankRising",
        esc("ATRPercentRank is rising"), CAT_SR, esc("Vol expanding: ATR percent rank rising. "
        "Non-directional."), "CBlock_null", "", is_rising(atrr(), bars="2", shift="1")))
    B.append(make_block("CBlock_ATRPctRankFalling", "ATRPctRankFalling",
        esc("ATRPercentRank is falling"), CAT_SR, esc("Vol contracting: ATR percent rank falling. "
        "Non-directional."), "CBlock_null", "", is_falling(atrr(), bars="2", shift="1")))
    return B


# === FILE 3 — COMPOUND: channel break AND a percentile gate ================
def build_combos(cat) -> list[str]:
    B = []

    def chan_up():
        return crosses_above(cat.atom("Close", shift="1"),
                             cat.atom("Highest", computedfrom="2", period="#Int2#", shift="2"))

    def chan_dn():
        return crosses_below(cat.atom("Close", shift="1"),
                             cat.atom("Lowest", computedfrom="3", period="#Int2#", shift="2"))

    def sr():
        return cat.atom("SRPercentRank", mode="2", length="100", atrperiod="14", shift="1")

    def atrr():
        return cat.atom("ATRPercentRank", atrperiod="14", lenght="100", shift="1")

    period = int_param("#Int2#", "Channel Period", "20", "10", "120")

    def pair(base, gate_up, gate_dn, gname, extra_params=""):
        lk, sk = f"CBlock_{base}Up", f"CBlock_{base}Down"
        B.append(make_block(lk, f"{base}Up",
            esc(f"Close breaks N-bar high  AND  {gname}"), CAT_COMBO,
            esc(f"Compound breakout: an N-bar Highest channel break confirmed by {gname}. "
                f"Channel + gate read shift 1."), sk, period + extra_params,
            and_op(chan_up(), gate_up)))
        B.append(make_block(sk, f"{base}Down",
            esc(f"Close breaks N-bar low  AND  {gname}"), CAT_COMBO,
            esc(f"Compound breakout (short): N-bar Lowest channel break confirmed by {gname}."),
            lk, period + extra_params,
            and_op(chan_dn(), gate_dn)))

    # C1 vol-expansion confirmed break
    pair("ChanBreakVolExpand",
         percentile_above(atrr(), "100", "60"), percentile_above(atrr(), "100", "60"),
         "ATR%Rank in top percentile (vol expansion)")
    # C2 break in upper/lower SR regime
    pair("ChanBreakSRRegime",
         is_greater(sr(), cat.number("50")), is_lower(sr(), cat.number("50")),
         "SR percent rank on the breakout side of 50")
    # C3 momentum-percentile confirmed break
    pair("ChanBreakMomThrust",
         percentile_above(cat.atom("Momentum"), "100", "80"),
         percentile_below(cat.atom("Momentum"), "100", "20"),
         "Momentum at a self-relative extreme")
    # C4 break out of a quiet (coiled) regime  -> squeeze-then-break
    pair("ChanBreakFromCoil",
         is_lower(atrr(), cat.number("35")), is_lower(atrr(), cat.number("35")),
         "ATR%Rank coiled (breaking out of a squeeze)")
    # C5 break with trend (low choppiness percentile)
    pair("ChanBreakTrending",
         percentile_below(cat.atom("ChoppinessIndex"), "100", "25"),
         percentile_below(cat.atom("ChoppinessIndex"), "100", "25"),
         "Choppiness in its bottom percentile (trending regime)")

    # C6 FRESH-high recency AND SR regime (uses HighestIndex/LowestIndex)
    lk, sk = "CBlock_FreshHighSRUp", "CBlock_FreshLowSRDown"
    B.append(make_block(lk, "FreshHighSRUp",
        esc("Fresh N-bar high (HighestIndex=0)  AND  SRPercentRank > 50"), CAT_COMBO,
        esc("Compound: the confirmed bar set a fresh N-bar high AND SR percent rank is on the "
            "bullish side of 50. HighestIndex is ignoreInBuilder (net-new)."), sk,
        int_param("#Int2#", "Lookback", "20", "10", "100"),
        and_op(is_lower(cat.atom("HighestIndex", computedfrom="2", period="#Int2#", shift="1"), cat.number("1")),
               is_greater(sr(), cat.number("50")))))
    B.append(make_block(sk, "FreshLowSRDown",
        esc("Fresh N-bar low (LowestIndex=0)  AND  SRPercentRank < 50"), CAT_COMBO,
        esc("Compound (short): fresh N-bar low AND SR percent rank below 50."), lk,
        int_param("#Int2#", "Lookback", "20", "10", "100"),
        and_op(is_lower(cat.atom("LowestIndex", computedfrom="3", period="#Int2#", shift="1"), cat.number("1")),
               is_lower(sr(), cat.number("50")))))
    return B


def main(argv):
    catalog_path = argv[0] if argv else "catalog.json"
    cat = Catalog(catalog_path)
    files = {
        "percentile_indicators.xml": build_indicators(cat),
        "srpercentrank.xml": build_srpct(cat),
        "percentile_breakout_combos.xml": build_combos(cat),
    }
    total = 0
    for fn, blocks in files.items():
        Path(fn).write_text(wrap_batch(blocks), encoding="utf-8")
        print(f"wrote {fn:34s} {len(blocks):3d} blocks")
        total += len(blocks)
    print(f"TOTAL {total} blocks across {len(files)} files")


if __name__ == "__main__":
    main(sys.argv[1:])
