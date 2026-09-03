"""gen_gold_grid.py — wave-3 XAUUSD screening grid (13 stop_long templates).

Overnight evidence (2026-07-19): both producers were stop-entry + session window
(Gold_Levels_Regime_Stop 72, Gold_Session_ORB_Stop 28); every market-entry template
yielded ~1 and MTF 0. So the grid converts EVERY untested filter x trigger combo to
the proven stop_long shape:

  filters : Filt_SessionGold  Filt_VolCoil  Filt_RegimeTrending  Filt_TrendUp_Long  Filt_TrendQuality
  triggers: Brk_PrevLevels_Long  Brk_SessionORB_Long  Brk_SweepReclaim_Long

15 cells minus the 2 already-run winners (SessionGold x ORB, RegimeTrending x PrevLevels)
= 13 new templates, all from existing custom blocks / gold pools. Screened at 5 min/task,
survivors promoted to a 60-min real run.

Run (from the sqx-strategy-template skill folder):
  python gen_gold_grid.py
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

POOL = "Lvl_BreakoutEntry_Long"

FILTERS = {
    "Session": "Filt_SessionGold",
    "Coil": "Filt_VolCoil",
    "Regime": "Filt_RegimeTrending",
    "TrendUp": "Filt_TrendUp_Long",
    "TrendQ": "Filt_TrendQuality",
}
TRIGGERS = {
    "Levels": "Brk_PrevLevels_Long",
    "ORB": "Brk_SessionORB_Long",
    "Sweep": "Brk_SweepReclaim_Long",
}
ALREADY_RUN = {("ORB", "Session"), ("Levels", "Regime")}

SPECS = []
for t_short, trigger in TRIGGERS.items():
    for f_short, filt in FILTERS.items():
        if (t_short, f_short) in ALREADY_RUN:
            continue
        SPECS.append(dict(
            name=f"Gold_{t_short}_{f_short}_Stop", shape="stop_long",
            filter=filt, trigger=trigger, price_pool=POOL,
            thesis=f"Grid cell {trigger} x {filt} in the proven stop-entry + "
                   "session-window shape (wave-3 screen).",
        ))


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)
    for spec in SPECS:
        path = generate.from_design(spec, install=INSTALL, outdir=OUTDIR)
        print(f"  {spec['name']:26s} {path}")
    print(f"done — {len(SPECS)} templates in {OUTDIR}")


if __name__ == "__main__":
    main()
