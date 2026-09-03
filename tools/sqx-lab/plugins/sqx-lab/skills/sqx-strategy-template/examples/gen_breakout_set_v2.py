"""v2 — five GENUINELY distinct templates, mostly breakout, designed for real edge.

What was wrong with v1 (and fixed here):
  - v1 paired COLLINEAR conditions (trend filter + breakout = the filter is implied by the
    trigger). v2 pairs only ORTHOGONAL context with each trigger.
  - v1 entered breakouts at MARKET = chasing the close. v2 enters breakouts on a STOP at a
    level (fill only if price truly extends) — and that also puts the Level pools to work.
  - v1 used 0 of the 4 Value/Level groups. v2 uses LevelsVolBands + LevelsPriorPeriod.
  - v1 was 5 near-clones. v2 is 5 different strategies across 4 shapes, 4 of them on
    build-CONFIRMED shapes (stop / session_market / two_entry_market).

Each: one filter (orthogonal context) + one trigger (the event), or N independent legs.
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from generate import from_design  # type: ignore[import-not-found]  # noqa: E402

INSTALL = r"C:\StrategyQuantX"
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "engine", "out", "breakout_set_v2")

designs = [
    # 1 — breakout done right: STOP entry at a volatility band, gated by trending regime.
    {"name": "RegimeBreakoutStop", "shape": "stop",
     "filter": "FilterRegimeTrending", "trigger": "EntriesBreakout", "price_pool": "LevelsVolBands",
     "roles": {"FilterRegimeTrending": "regime context (orthogonal to the break)",
               "EntriesBreakout": "breakout event", "LevelsVolBands": "buy-stop level (upper band)"},
     "thesis": "Breakouts only pay in a trending regime; rest a buy-stop at a volatility band so "
               "you fill only if price clears noise. Regime, event and level are independent — real confluence."},

    # 2 — same idea, orthogonal vol filter + structural prior-period level.
    {"name": "VolBreakoutStop", "shape": "stop",
     "filter": "FilterVolExpansion", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
     "roles": {"FilterVolExpansion": "volatility expanding (independent of price level)",
               "EntriesBreakout": "breakout event", "LevelsPriorPeriod": "buy-stop at a prior-period high"},
     "thesis": "A break with expanding volatility behind it, entered on a stop at the prior day/week "
               "high — vol confirms fuel, the level confirms the break is structural, the stop avoids chasing."},

    # 3 — counter-philosophy: buy the DIP inside an uptrend. Genuinely orthogonal (trend vs oversold).
    {"name": "TrendDipBuy", "shape": "market",
     "filter": "FilterTrendDirection", "trigger": "EntriesMeanRevert",
     "roles": {"FilterTrendDirection": "uptrend regime (direction)",
               "EntriesMeanRevert": "oversold snap-back (timing)"},
     "thesis": "Buy an oversold snap-back ONLY while price holds above its trend MA — trend gives the "
               "directional edge, the oversold cross gives entry timing, and the two are uncorrelated."},

    # 4 — momentum where it's supposed to work: trending regime + session/day gate (confirmed shape).
    {"name": "RegimeMomentumSession", "shape": "session_market",
     "filter": "FilterRegimeTrending", "trigger": "EntriesMomentum",
     "roles": {"FilterRegimeTrending": "trending regime (momentum only pays when trending)",
               "EntriesMomentum": "momentum zero/signal cross"},
     "thesis": "Momentum crosses are noise in chop; take them only in a trending regime, and let the "
               "skeleton's day gate skip the weakest session — orthogonal regime + timing."},

    # 5 — two uncorrelated long edges in ONE strategy (build-confirmed two-entry shape).
    {"name": "DualEdgeLong", "shape": "two_entry_market",
     "entry_a": "EntriesBreakout", "entry_b": "EntriesMeanRevert",
     "roles": {"EntriesBreakout": "leg A: buy strength (breakout)",
               "EntriesMeanRevert": "leg B: buy weakness (dip)"},
     "thesis": "Two opposite long setups booked as independent legs (own MagicNumber + bar-exit): the "
               "breakout leg carries trending regimes, the dip leg carries the chop — diversification in one chart."},
]

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    written, failed = [], []
    for d in designs:
        try:
            p = from_design(d, install=INSTALL, outdir=OUTDIR)
            written.append((d["name"], d["shape"], p))
            print("OK  ", d["name"], f"({d['shape']})", "\n")
        except (SystemExit, Exception) as e:  # noqa: BLE001
            failed.append((d["name"], str(e)))
            print(f"FAIL {d['name']}: {type(e).__name__}: {e}\n")
    print("=" * 60)
    print(f"{len(written)}/{len(designs)} generated")
    for n, e in failed:
        print(f"  FAILED {n}: {e}")
