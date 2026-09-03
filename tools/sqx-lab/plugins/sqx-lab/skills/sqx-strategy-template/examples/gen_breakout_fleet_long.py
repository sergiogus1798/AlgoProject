"""Breakout fleet — LONG-ONLY twin of gen_breakout_fleet.py.

Same 24 designs, same long-biased kit (Brk_*_Long triggers x Filt_* filters x Lvl_BreakoutEntry_Long),
but bound to the LONG-ONLY skeletons (stop_long / market_long / mtf_filter_long), so the generated
.sqx carry NO short mirror — SQX builds long-only strategies from them.

  - SPINE        stop_long          full 4x4 trigger x filter  (16)  EnterAtStop @ Lvl_BreakoutEntry_Long
  - EXECUTION    market_long        4 aligned pairs            ( 4)  immediate fill
  - TIMEFRAME    mtf_filter_long    4 aligned pairs            ( 4)  daily filter + intraday trigger

Names get an `L` execution token (StopL / MktL / MTFL) so the long-only databanks are distinct from
the two-sided fleet's. PENDING BUILD-CONFIRM — the three _long skeletons each need one build.

    python examples/gen_breakout_fleet_long.py
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from generate import from_design  # type: ignore[import-not-found]  # noqa: E402

# NOTE: confirm the Brk_/Filt_/Lvl_ groups exist in your live install before regenerating. For an
# offline rebuild that reuses the build-confirmed groups, use engine/make_breakout_fleet_long.py.
INSTALL = r"C:\StrategyQuantX"
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "engine", "out", "breakout_fleet_long")
PRICE = "Lvl_BreakoutEntry_Long"

# trigger group -> short token
TRIGGERS = {
    "Brk_ChannelDonchian_Long": "Donchian",
    "Brk_VolatilityBands_Long": "VolBands",
    "Brk_PivotPrevPeriod_Long": "PivotPrev",
    "Brk_ThrustRangeExp_Long":  "Thrust",
}
# filter group -> short token
FILTERS = {
    "Filt_TrendUp_Long":   "TrendUp",
    "Filt_MomentumUp_Long": "MomUp",
    "Filt_RegimeTrending": "Regime",
    "Filt_VolExpansion":   "VolExp",
}
# aligned trigger->filter pairs for the market / mtf A/B subsets (confluence, each a real thesis)
ALIGNED = {
    "Brk_ChannelDonchian_Long": "Filt_TrendUp_Long",     # channel break in a trend
    "Brk_VolatilityBands_Long": "Filt_VolExpansion",     # band break when vol is expanding
    "Brk_PivotPrevPeriod_Long": "Filt_RegimeTrending",   # pivot break follows through when trending
    "Brk_ThrustRangeExp_Long":  "Filt_MomentumUp_Long",  # range thrust + momentum confluence
}

designs = []

# --- SPINE: full 4x4 stop_long matrix (16) ---
for trig, tt in TRIGGERS.items():
    for filt, ft in FILTERS.items():
        designs.append({
            "name": f"Bo_{tt}_{ft}_StopL", "shape": "stop_long",
            "filter": filt, "trigger": trig, "price_pool": PRICE,
            "thesis": f"LONG-ONLY {tt} breakout taken only while {ft} holds; the pending stop at a "
                      f"Lvl_BreakoutEntry_Long level fills only if price truly extends up.",
        })

# --- EXECUTION A/B: aligned pairs, immediate market fill, long-only (4) ---
for trig, filt in ALIGNED.items():
    tt, ft = TRIGGERS[trig], FILTERS[filt]
    designs.append({
        "name": f"Bo_{tt}_{ft}_MktL", "shape": "market_long",
        "filter": filt, "trigger": trig,
        "thesis": f"Same {tt}-in-{ft} confluence, long-only, filled at market on the breakout "
                  f"state — tests whether immediate fill beats waiting for a stop level.",
    })

# --- TIMEFRAME A/B: aligned pairs, daily filter + intraday trigger -> stop, long-only (4) ---
for trig, filt in ALIGNED.items():
    tt, ft = TRIGGERS[trig], FILTERS[filt]
    designs.append({
        "name": f"Bo_{tt}_{ft}_MTFL", "shape": "mtf_filter_long",
        "daily_filter": filt, "trigger": trig, "price_pool": PRICE,
        "thesis": f"LONG-ONLY intraday {tt} breakout gated by {ft} on the DAILY chart — tests "
                  f"whether higher-timeframe regime alignment removes breakouts that fight the trend.",
    })

if __name__ == "__main__":
    ok, fail = 0, 0
    for d in designs:
        try:
            p = from_design(d, install=INSTALL, outdir=OUTDIR)
            print("written:", os.path.basename(p))
            ok += 1
        except SystemExit as e:
            print(f"SKIP {d['name']}: {e}")
            fail += 1
    print(f"\n{ok} written, {fail} skipped -> {OUTDIR}")
