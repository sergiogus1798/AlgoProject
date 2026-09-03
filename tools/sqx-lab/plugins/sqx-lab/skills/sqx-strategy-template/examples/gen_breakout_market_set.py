"""Five basic MARKET-entry templates, mostly breakout — bound to the 2953_Dev install.

Research design (see ../research_agent.md): templates 1-4 hold the trigger constant
(EntriesBreakout) and vary the context FILTER, so a build/backtest isolates which context
most improves a breakout. Template 5 swaps the trigger to momentum under the same trend
filter as a control. All `market` shape (immediate fill); short side mirrors automatically.

    python examples/gen_breakout_market_set.py
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from generate import from_design  # type: ignore[import-not-found]  # noqa: E402

INSTALL = r"C:\StrategyQuantX"
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "engine", "out", "breakout_market_set")

designs = [
    {"name": "TrendBreakoutMarket", "shape": "market",
     "filter": "FilterTrendDirection", "trigger": "EntriesBreakout",
     "roles": {"FilterTrendDirection": "trend-direction filter", "EntriesBreakout": "breakout trigger"},
     "thesis": "A breakout taken only while price is above its trend MA follows through more often "
               "than a counter-trend break; counter-trend breaks are disproportionately fakeouts."},

    {"name": "VolBreakoutMarket", "shape": "market",
     "filter": "FilterVolExpansion", "trigger": "EntriesBreakout",
     "roles": {"FilterVolExpansion": "volatility-expansion filter", "EntriesBreakout": "breakout trigger"},
     "thesis": "Breakouts during expanding volatility (ATR/StdDev/BB widening) carry real momentum; "
               "breakouts in quiet or contracting volatility are noise that mean-reverts."},

    {"name": "RegimeBreakoutMarket", "shape": "market",
     "filter": "FilterRegimeTrending", "trigger": "EntriesBreakout",
     "roles": {"FilterRegimeTrending": "trending-regime filter", "EntriesBreakout": "breakout trigger"},
     "thesis": "Breakouts only pay in a trending regime; when ADX/Choppiness/KER say the market is "
               "range-bound, channel breaks are whipsaws that revert."},

    {"name": "SessionBreakoutMarket", "shape": "market",
     "filter": "FilterSession", "trigger": "EntriesBreakout",
     "roles": {"FilterSession": "active-session filter", "EntriesBreakout": "breakout trigger"},
     "thesis": "Breakouts during the active London/NY session have genuine order flow behind them; "
               "thin off-hours breakouts are fakeouts that revert when the session opens."},

    {"name": "TrendMomentumMarket", "shape": "market",
     "filter": "FilterTrendDirection", "trigger": "EntriesMomentum",
     "roles": {"FilterTrendDirection": "trend-direction filter", "EntriesMomentum": "momentum trigger"},
     "thesis": "Momentum-oscillator crosses (MACD/ROC/Awesome above zero) in the trend direction "
               "ride continuation; counter-trend crosses fade — the control versus the breakout set."},
]

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    written, failed = [], []
    for d in designs:
        try:
            p = from_design(d, install=INSTALL, outdir=OUTDIR)
            written.append(p)
            print("OK  ", d["name"], "->", p, "\n")
        except (SystemExit, Exception) as e:  # noqa: BLE001
            failed.append((d["name"], str(e)))
            print(f"FAIL {d['name']}: {type(e).__name__}: {e}\n")
    print("=" * 60)
    print(f"{len(written)}/{len(designs)} generated")
    for n, e in failed:
        print(f"  FAILED {n}: {e}")
