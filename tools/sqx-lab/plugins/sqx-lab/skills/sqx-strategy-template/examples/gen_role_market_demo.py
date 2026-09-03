"""Demo the NEW role_market shape: regime AND trigger AND NOT veto, bound to the 2953 install.

This is the lab-step proof: it must self-validate (blocks resolve, 3 #Group# holes embedded).
Build-confirmation in AlgoWizard is still required to earn the shape its check mark.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from generate import from_design  # type: ignore[import-not-found]  # noqa: E402

INSTALL = r"C:\StrategyQuantX"
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "engine", "out", "role_market_demo")

spec = {
    "name": "TrendBreakout_VetoMeanRevert", "shape": "role_market",
    "regime": "FilterTrendDirection",   # RC1 — context: only while uptrend holds
    "trigger": "EntriesBreakout",        # RC2 — the entry event
    "veto": "EntriesMeanRevert",         # RC3 — NOT: skip the break if a reversal/oversold signal co-fires
    "roles": {"FilterTrendDirection": "regime", "EntriesBreakout": "trigger",
              "EntriesMeanRevert": "veto (negated)"},
    "thesis": "Take trend-aligned breakouts, but VETO any that coincide with a mean-reversion "
              "signal — those are exhaustion breaks more likely to fail.",
}

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    p = from_design(spec, install=INSTALL, outdir=OUTDIR)
    print("\nwritten:", p)
