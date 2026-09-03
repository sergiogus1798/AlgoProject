"""Worked example: design specs -> validated .sqx templates, bound to YOUR install.

Copy this, edit `INSTALL` and the `designs`, run it. Every group name must exist in your
`catalog.json` (run `python engine/discover.py "<install>"` first) with the right type:
Condition for filter/trigger/regime/veto, Value for a stop/level price pool.

The names below are this repo install's REAL catalog groups (Entries* triggers, Filter* filters,
Levels* value pools) — on a different install your names will differ; the catalog wins. The designs
mirror the research agent's archetypes (see ../research_agent.md): one filter + one trigger, paired
for confluence, each with a falsifiable thesis. Pick a `shape` per the table in SKILL.md.

    python examples/gen_template_example.py
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from generate import from_design  # type: ignore[import-not-found]  # noqa: E402

INSTALL = r"C:\StrategyQuantX"   # <-- your install folder

designs = [
    # TrendContinuationBreakout (stop) — the fill itself confirms the move
    {"name": "TrendContinuationBreakout", "shape": "stop",
     "filter": "FilterTrendDirection", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
     "thesis": "Breakouts taken only in the FilterTrendDirection regime follow through more than "
               "counter-trend ones; the prior-period stop only fills if price truly extends."},

    # HTFRegimeBreakout (mtf_filter) — daily regime gate + intraday breakout trigger (NEW: axis A)
    {"name": "MTFTrendBreakout", "shape": "mtf_filter",
     "daily_filter": "FilterTrendDirection", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
     "thesis": "Intraday breakouts aligned with the DAILY trend follow through; the higher-timeframe "
               "gate removes breakouts that fight the bigger trend."},

    # BreakoutWithExhaustionVeto (role_market) — regime AND trigger AND NOT veto
    {"name": "BreakoutVetoExhaustion", "shape": "role_market",
     "regime": "FilterTrendDirection", "trigger": "EntriesBreakout", "veto": "EntriesMeanRevert",
     "thesis": "Trend-aligned breakouts follow through except when they coincide with an oscillator "
               "reversal (exhaustion); vetoing those removes the worst breakouts."},

    # RegimeGatedMomentum (market) — strength gate x momentum event (the condition is the edge)
    {"name": "RegimeGatedMomentum", "shape": "market",
     "filter": "FilterRegimeTrending", "trigger": "EntriesMomentum",
     "thesis": "Momentum crosses persist only when trend strength is high; gating by FilterRegimeTrending "
               "(not a direction filter) keeps the signal where follow-through exists."},

    # BaselineTrendOnly (market_single) — the control
    {"name": "BaselineTrendOnly", "shape": "market_single",
     "condition": "FilterTrendDirection",
     "thesis": "Long while the regime is up, flat otherwise — a baseline to measure whether any extra "
               "trigger actually adds edge."},

    # MultiSetupPortfolio (multi_leg) — N independent legs, each its own group + order + bars-exit + magic
    {"name": "MultiSetupPortfolio", "shape": "multi_leg", "legs": [
        {"group": "EntriesBreakout", "order": "market", "exit_bars": 10},
        {"group": "EntriesTrend", "order": "market", "exit_bars": 30},
        {"group": "EntriesMomentum", "order": "stop", "price_pool": "LevelsPriorPeriod", "exit_bars": 50},
     ],
     "thesis": "Three uncorrelated long setups (breakout / trend / momentum) booked as separate legs so "
               "each exits on its own clock — diversification within one strategy."},
]

if __name__ == "__main__":
    for d in designs:
        try:
            p = from_design(d, install=INSTALL)
            print("written:", p, "\n")
        except SystemExit as e:
            print(f"SKIP {d['name']}: {e}\n")
