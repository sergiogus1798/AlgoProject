"""gen_gold_alt_wave.py — creative second-wave XAUUSD templates (3, long-only).

The dip-buy archetype (see gen_gold_alt_groups.py): gold's structural official-sector
bid means swept lows that RECLAIM are high-quality long entries — the mirror image of
the breakout wave. Entry at market (the reclaim itself is the confirmation).

  Gold_Sweep_TrendUp_Mkt   market_long   classic trend filter (fleet group, referenced)
  Gold_Sweep_TrendQ_Mkt    market_long   statistical trend-quality filter (new pool)
  Gold_TwoLeg_Sweep_ORB    two_entry     dip-buy leg + session-breakout leg, independent

Groups come from the install + BOTH local gold XMLs merged in-memory; the emitted .sqx
embeds every group it references. Run from the sqx-strategy-template skill folder:
  python gen_gold_alt_wave.py
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

_orig_install_groups = generate._install_groups


def _merged_groups(install):
    groups = _orig_install_groups(install)
    for f in GROUP_FILES:
        for g in ET.parse(f).getroot().iter("Group"):
            groups[g.get("name")] = g
    return groups


generate._install_groups = _merged_groups

SPECS = [
    dict(name="Gold_Sweep_TrendUp_Mkt", shape="market_long",
         filter="Filt_TrendUp_Long", trigger="Brk_SweepReclaim_Long",
         thesis="Structural central-bank bid: a swept prior low that reclaims, inside "
                "an uptrend, is a bought dip — enter on the reclaim."),
    dict(name="Gold_Sweep_TrendQ_Mkt", shape="market_long",
         filter="Filt_TrendQuality", trigger="Brk_SweepReclaim_Long",
         thesis="Dip-reclaims only when the tape is statistically trending "
                "(Hurst/KER/entropy) — quality gate without naming a direction."),
    dict(name="Gold_TwoLeg_Sweep_ORB", shape="two_entry_market",
         entry_a="Brk_SweepReclaim_Long", entry_b="Brk_SessionORB_Long",
         thesis="Two independent gold edges in one book: dip-buy reclaims + session "
                "breakouts; each leg its own magic number and time exit."),
]


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)
    for spec in SPECS:
        path = generate.from_design(spec, install=INSTALL, outdir=OUTDIR)
        print(f"  {spec['shape']:18s} {path}")
    print(f"done — {len(SPECS)} templates in {OUTDIR}")


if __name__ == "__main__":
    main()
