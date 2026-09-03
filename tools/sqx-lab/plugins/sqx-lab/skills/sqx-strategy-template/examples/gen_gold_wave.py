"""gen_gold_wave.py — the XAUUSD template wave (8 long-only templates, 4 archetypes).

T2 MTF trend-gated breakout   (mtf_filter_long, build-confirmed) — existing groups
T1 Session/ORB breakout       (stop_long + market_long)          — NEW Filt_SessionGold + Brk_SessionORB_Long
T3 Coil -> expansion breakout (stop_long)                        — NEW Filt_VolCoil
T4 Prior-level break          (stop_long + market_long)          — NEW Brk_PrevLevels_Long

The 4 NEW groups come from ../sqx-random-group/gold_groups.xml (validated, not yet
imported into the install). They are merged in-memory at generate time; the emitted
.sqx embeds every group it references, so each template is self-contained. Import
gold_groups.xml into AlgoWizard separately so the groups are also editable in the GUI.

Run (from the sqx-strategy-template skill folder):
  python gen_gold_wave.py
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from engine import generate  # noqa: E402

INSTALL = r"C:\StrategyQuantX"
GOLD_GROUPS = os.path.join(HERE, "..", "sqx-random-group", "gold_groups.xml")
OUTDIR = os.path.join(HERE, "engine", "out", "gold_wave")

_orig_install_groups = generate._install_groups


def _merged_groups(install):
    groups = _orig_install_groups(install)
    for g in ET.parse(GOLD_GROUPS).getroot().iter("Group"):
        groups[g.get("name")] = g
    return groups


generate._install_groups = _merged_groups

POOL = "Lvl_BreakoutEntry_Long"

SPECS = [
    # T2 — MTF trend-gated breakout (existing groups only)
    dict(name="Gold_MTF_Donchian_TrendUp", shape="mtf_filter_long",
         daily_filter="Filt_TrendUp_Long", trigger="Brk_ChannelDonchian_Long", price_pool=POOL,
         thesis="H1 Donchian breakouts aligned with the DAILY uptrend follow through; gold trends."),
    dict(name="Gold_MTF_Thrust_MomUp", shape="mtf_filter_long",
         daily_filter="Filt_MomentumUp_Long", trigger="Brk_ThrustRangeExp_Long", price_pool=POOL,
         thesis="Range-expansion thrusts with daily momentum behind them continue intraday."),
    dict(name="Gold_MTF_VolBands_Regime", shape="mtf_filter_long",
         daily_filter="Filt_RegimeTrending", trigger="Brk_VolatilityBands_Long", price_pool=POOL,
         thesis="Volatility-band breaks only when the daily regime is trending, not choppy."),
    # T1 — session/ORB breakout (new session groups)
    dict(name="Gold_Session_ORB_Stop", shape="stop_long",
         filter="Filt_SessionGold", trigger="Brk_SessionORB_Long", price_pool=POOL,
         thesis="Gold sets its daily extreme in the London/NY overlap ~70% of days; "
                "session-anchored breakouts entered on a stop ride that move."),
    dict(name="Gold_Session_ORB_Mkt", shape="market_long",
         filter="Filt_SessionGold", trigger="Brk_SessionORB_Long",
         thesis="Market-entry twin of Gold_Session_ORB_Stop (immediate fill on the session trigger)."),
    # T3 — coil -> expansion breakout (new coil filter)
    dict(name="Gold_Coil_Thrust_Stop", shape="stop_long",
         filter="Filt_VolCoil", trigger="Brk_ThrustRangeExp_Long", price_pool=POOL,
         thesis="Volatility contraction precedes expansion; thrust breaks out of a coil carry."),
    # T4 — prior-level break with regime/trend context (new level triggers)
    dict(name="Gold_Levels_Regime_Stop", shape="stop_long",
         filter="Filt_RegimeTrending", trigger="Brk_PrevLevels_Long", price_pool=POOL,
         thesis="Prior day/week highs act as breakout levels when the regime is trending."),
    dict(name="Gold_Levels_TrendUp_Mkt", shape="market_long",
         filter="Filt_TrendUp_Long", trigger="Brk_PrevLevels_Long",
         thesis="Prior-level reclaims in an uptrend, filled at market."),
]


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)
    for spec in SPECS:
        path = generate.from_design(spec, install=INSTALL, outdir=OUTDIR)
        print(f"  {spec['shape']:16s} {path}")
    print(f"done — {len(SPECS)} templates in {OUTDIR}")


if __name__ == "__main__":
    main()
