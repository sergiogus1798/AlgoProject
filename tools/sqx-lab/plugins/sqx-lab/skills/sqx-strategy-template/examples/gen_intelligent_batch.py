"""Intelligent batch — one design per archetype (research_agent.md v2), bound to THIS install.

Demonstrates the design brain: each spec names an ARCHETYPE, assigns roles (regime/filter/
trigger/veto/level) from the install's REAL catalog groups, pairs for confluence (orthogonal
axes — never two filters / two triggers), and carries a falsifiable thesis. The buggy `market`
shape is deliberately avoided; status per shape is noted.

Groups used (this install's catalog.json):
  Triggers : EntriesBreakout · EntriesTrend · EntriesMeanRevert · EntriesMomentum
  Filters  : FilterTrendDirection · FilterRegimeTrending · FilterVolExpansion · FilterSession
  Levels   : LevelsTrailingStop · LevelsVolBands · LevelsPriorPeriod · LevelsTargets

    python examples/gen_intelligent_batch.py
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from generate import from_design  # type: ignore[import-not-found]  # noqa: E402

INSTALL = r"C:\StrategyQuantX"
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "engine", "out", "intelligent_batch")

designs = [
    # 1. TrendContinuationBreakout — stop (BUILD-CONFIRMED). direction regime x breakout event.
    {"name": "TrendContinuationBreakout", "shape": "stop",
     "filter": "FilterTrendDirection", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
     "roles": {"FilterTrendDirection": "regime", "EntriesBreakout": "trigger", "LevelsPriorPeriod": "stop level"},
     "thesis": "Breakouts taken only in the FilterTrendDirection regime follow through more than "
               "counter-trend ones; the prior-period stop only fills if price truly extends."},

    # 2. VolatilityExpansionBreakout — stop (BUILD-CONFIRMED). vol-state x breakout event.
    {"name": "VolExpansionBreakout", "shape": "stop",
     "filter": "FilterVolExpansion", "trigger": "EntriesBreakout", "price_pool": "LevelsVolBands",
     "roles": {"FilterVolExpansion": "regime", "EntriesBreakout": "trigger", "LevelsVolBands": "stop level"},
     "thesis": "Breakouts that fire as volatility EXPANDS (squeeze release) extend; during contraction "
               "they fail back into the range. Gating on vol-state selects the regime where range "
               "extension is sustained."},

    # 3. HTFRegimeBreakout — mtf_filter (NEW spike, pending build-confirm). daily regime x intraday event.
    {"name": "HTFRegimeBreakout", "shape": "mtf_filter",
     "daily_filter": "FilterTrendDirection", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
     "roles": {"FilterTrendDirection": "daily regime (HTF)", "EntriesBreakout": "intraday trigger",
               "LevelsPriorPeriod": "stop level"},
     "thesis": "Intraday breakouts aligned with the DAILY trend follow through; the higher-timeframe "
               "gate removes intraday breakouts that fight the bigger trend."},

    # 4. SessionBreakout — market (clean). FilterSession GROUP supplies the session window, so no
    #    separate baked time-gate is needed (that would be a redundant example artifact). Trigger lives
    #    in the signal var; immediate fill when the session is active AND a breakout fires.
    {"name": "SessionBreakout", "shape": "market",
     "filter": "FilterSession", "trigger": "EntriesBreakout",
     "roles": {"FilterSession": "session gate (group)", "EntriesBreakout": "trigger"},
     "thesis": "Breakouts in high-liquidity sessions have participation behind them and follow through; "
               "the same breakout in thin hours is noise. FilterSession constrains WHEN (non-directional), "
               "so it adds confluence without double-booking the directional edge."},

    # 5. BreakoutWithExhaustionVeto — role_market (pending). regime AND trigger AND NOT veto.
    {"name": "BreakoutVetoExhaustion", "shape": "role_market",
     "regime": "FilterTrendDirection", "trigger": "EntriesBreakout", "veto": "EntriesMeanRevert",
     "roles": {"FilterTrendDirection": "regime", "EntriesBreakout": "trigger", "EntriesMeanRevert": "veto"},
     "thesis": "Trend-aligned breakouts follow through EXCEPT when they coincide with an oscillator "
               "reversal (exhaustion / blow-off); vetoing those removes the worst breakouts without "
               "thinning the good ones."},

    # 6. RegimeGatedMomentum (veto-guarded) — role_market (pending). strength regime x momentum, veto exhaustion.
    {"name": "RegimeGatedMomentum", "shape": "role_market",
     "regime": "FilterRegimeTrending", "trigger": "EntriesMomentum", "veto": "EntriesMeanRevert",
     "roles": {"FilterRegimeTrending": "regime (strength)", "EntriesMomentum": "trigger", "EntriesMeanRevert": "veto"},
     "thesis": "Momentum crosses persist only when trend STRENGTH is high; gating by FilterRegimeTrending "
               "(energy, not direction) keeps the signal where follow-through exists, and the veto drops "
               "crosses that are really exhaustion."},

    # 7. TrendPullbackGuarded — role_market (pending). trend regime x dip-buy, veto vol-still-expanding.
    {"name": "TrendPullbackGuarded", "shape": "role_market",
     "regime": "FilterTrendDirection", "trigger": "EntriesMeanRevert", "veto": "FilterVolExpansion",
     "roles": {"FilterTrendDirection": "regime", "EntriesMeanRevert": "dip-buy trigger", "FilterVolExpansion": "veto"},
     "thesis": "In an uptrend, an oscillator snapping back from oversold marks the END of a pullback "
               "(continuation entry); but veto the dip-buy while volatility is still EXPANDING, when the "
               "pullback is more likely a real reversal. The trend filter re-purposes the fade into a dip-buy."},

    # 8. MultiSetupPortfolio — multi_leg (pending). three uncorrelated long legs, each its own clock.
    {"name": "MultiSetupPortfolio", "shape": "multi_leg", "legs": [
        {"group": "EntriesBreakout", "order": "market", "exit_bars": 10},
        {"group": "EntriesTrend", "order": "market", "exit_bars": 30},
        {"group": "EntriesMomentum", "order": "stop", "price_pool": "LevelsPriorPeriod", "exit_bars": 50},
     ],
     "thesis": "Three uncorrelated long setups (breakout / trend-cross / momentum-thrust) booked as "
               "separate legs so each exits on its own clock — diversification within one strategy; "
               "different Entries groups so no edge is double-counted."},

    # 9. BaselineTrendOnly — market_single (pending). the CONTROL the others must beat.
    {"name": "BaselineTrendOnly", "shape": "market_single",
     "condition": "FilterTrendDirection",
     "roles": {"FilterTrendDirection": "regime"},
     "thesis": "Long while the regime is up, flat otherwise — the control baseline that measures whether "
               "any added trigger/veto in the richer designs actually contributes edge."},
]

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    ok, skipped = 0, 0
    for d in designs:
        try:
            p = from_design(d, install=INSTALL, outdir=OUTDIR)
            print("written:", os.path.basename(p))
            ok += 1
        except SystemExit as e:
            print(f"SKIP {d['name']}: {e}")
            skipped += 1
    print(f"\n{ok} written, {skipped} skipped -> {OUTDIR}")
