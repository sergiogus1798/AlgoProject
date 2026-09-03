"""Breakout fleet — bound to the freshly-imported Brk_/Filt_/Lvl_ random groups.

Install : D:\\StrategyQuantX (blockGroups.xml imported 2026-06-09)
Kit     : 4 Brk_* triggers x 4 Filt_* filters x Lvl_BreakoutEntry_Long (entry-stop price pool)

Design (long-only), 24 templates across two controlled axes:
  - SPINE        stop          full 4x4 trigger x filter  (16)  EnterAtStop @ Lvl_BreakoutEntry_Long
  - EXECUTION    market        4 aligned pairs            ( 4)  immediate fill (stop-vs-market A/B)
  - TIMEFRAME    mtf_filter    4 aligned pairs            ( 4)  daily filter + intraday trigger (single-vs-HTF A/B)

role_market is intentionally omitted: this kit has no mean-revert/exhaustion pool, so a veto slot
would be a weak directional-filter-in-reverse, not a real exhaustion guard.

    python examples/gen_breakout_fleet.py
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from generate import from_design  # type: ignore[import-not-found]  # noqa: E402

INSTALL = r"C:\StrategyQuantX"
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "engine", "out", "breakout_fleet")
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

# --- SPINE: full 4x4 stop matrix (16) ---
for trig, tt in TRIGGERS.items():
    for filt, ft in FILTERS.items():
        designs.append({
            "name": f"Bo_{tt}_{ft}_Stop", "shape": "stop",
            "filter": filt, "trigger": trig, "price_pool": PRICE,
            "thesis": f"Long {tt} breakout taken only while {ft} holds; the pending stop at a "
                      f"Lvl_BreakoutEntry_Long level fills only if price truly extends.",
        })

# --- EXECUTION A/B: aligned pairs, immediate market fill (4) ---
for trig, filt in ALIGNED.items():
    tt, ft = TRIGGERS[trig], FILTERS[filt]
    designs.append({
        "name": f"Bo_{tt}_{ft}_Mkt", "shape": "market",
        "filter": filt, "trigger": trig,
        "thesis": f"Same {tt}-in-{ft} confluence but filled at market on the breakout state — "
                  f"tests whether immediate fill beats waiting for a stop level.",
    })

# --- TIMEFRAME A/B: aligned pairs, daily filter + intraday trigger -> stop (4) ---
for trig, filt in ALIGNED.items():
    tt, ft = TRIGGERS[trig], FILTERS[filt]
    designs.append({
        "name": f"Bo_{tt}_{ft}_MTF", "shape": "mtf_filter",
        "daily_filter": filt, "trigger": trig, "price_pool": PRICE,
        "thesis": f"Intraday {tt} breakout gated by {ft} on the DAILY chart — tests whether "
                  f"higher-timeframe regime alignment removes the breakouts that fight the bigger trend.",
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
