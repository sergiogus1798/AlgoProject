"""gen_gold_short_wave.py — SHORT side of the top-6 gold templates.

The top-6 winners are long-only (built on the *_long skeletons). Their short twins are
generated here on the TWO-SIDED skeletons (stop / mtf_filter), which carry a short entry
whose conditions are filled by SQX's `generate="opposite"` mechanic — i.e. each bound
block's declared oppositeBlockKey (ORBBreakoutUp -> ORBBreakoutDown, PrevDayHigh ->
PrevDayLow, ...). So binding the SAME bullish groups yields a correct bearish mirror with
no new groups needed. Direction is enforced at the project level (MarketSides=short); the
long side stays present-but-untraded.

  Gold_Levels_TrendUp_Short   stop        Filt_TrendUp_Long   x Brk_PrevLevels_Long
  Gold_Levels_Session_Short   stop        Filt_SessionGold    x Brk_PrevLevels_Long
  Gold_ORB_TrendUp_Short      stop        Filt_TrendUp_Long   x Brk_SessionORB_Long
  Gold_Session_ORB_Short      stop        Filt_SessionGold    x Brk_SessionORB_Long
  Gold_MTF_Donchian_Short     mtf_filter  Filt_TrendUp_Long   x Brk_ChannelDonchian_Long
  Gold_MTF_VolBands_Short     mtf_filter  Filt_RegimeTrending x Brk_VolatilityBands_Long

Run (from the sqx-strategy-template skill folder):
  python gen_gold_short_wave.py
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from engine import generate  # noqa: E402

INSTALL = r"C:\StrategyQuantX"
GROUP_FILES = [
    os.path.join(HERE, "..", "sqx-random-group", "gold_groups.xml"),
    os.path.join(HERE, "..", "sqx-random-group", "gold_alt_groups.xml"),
]
OUTDIR = os.path.join(HERE, "engine", "out", "gold_wave")
POOL = "Lvl_BreakoutEntry_Long"

_orig = generate._install_groups


def _merged(install):
    g = _orig(install)
    for f in GROUP_FILES:
        for grp in ET.parse(f).getroot().iter("Group"):
            g[grp.get("name")] = grp
    return g


generate._install_groups = _merged

SPECS = [
    dict(name="Gold_Levels_TrendUp_Short", shape="stop",
         filter="Filt_TrendUp_Long", trigger="Brk_PrevLevels_Long", price_pool=POOL,
         thesis="Break of the prior day/week LOW in a downtrend (short mirror of the top long)."),
    dict(name="Gold_Levels_Session_Short", shape="stop",
         filter="Filt_SessionGold", trigger="Brk_PrevLevels_Long", price_pool=POOL,
         thesis="Prior-level breakdown during the London/NY session."),
    dict(name="Gold_ORB_TrendUp_Short", shape="stop",
         filter="Filt_TrendUp_Long", trigger="Brk_SessionORB_Long", price_pool=POOL,
         thesis="Session opening-range breakDOWN aligned with a downtrend."),
    dict(name="Gold_Session_ORB_Short", shape="stop",
         filter="Filt_SessionGold", trigger="Brk_SessionORB_Long", price_pool=POOL,
         thesis="The classic London/NY opening-range breakdown, sell-stop entry."),
    dict(name="Gold_MTF_Donchian_Short", shape="mtf_filter",
         daily_filter="Filt_TrendUp_Long", trigger="Brk_ChannelDonchian_Long", price_pool=POOL,
         thesis="H1 Donchian breakdown gated by the DAILY downtrend."),
    dict(name="Gold_MTF_VolBands_Short", shape="mtf_filter",
         daily_filter="Filt_RegimeTrending", trigger="Brk_VolatilityBands_Long", price_pool=POOL,
         thesis="Volatility-band breakdown, only when the daily regime is trending."),
]


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)
    for spec in SPECS:
        path = generate.from_design(spec, install=INSTALL, outdir=OUTDIR)
        print(f"  {spec['shape']:12s} {spec['name']:26s} {path}")
    print(f"done — {len(SPECS)} short templates in {OUTDIR}")


if __name__ == "__main__":
    main()
