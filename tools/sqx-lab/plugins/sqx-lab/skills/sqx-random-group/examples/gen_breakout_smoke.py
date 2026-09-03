"""gen_breakout_smoke.py — smoke pool to prove the new install (2953) resolves CBlock_* refs.

A 5-item HYBRID Condition group of long-side channel/level break triggers. Knobs frozen
(a smoke test proves resolution on import, not optimization). Run from the skill root:

  python gen_breakout_smoke.py
  python engine/validate.py BreakoutTriggersLong_Smoke.xml --catalog catalog.json
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.groups import load_catalog, hybrid_ref, make_group, wrap_groups  # noqa: E402

KEYS = [
    "CBlock_CloseAboveDCUpper_Brk",     # Donchian upper break
    "CBlock_CloseAboveBBUpper_Brk",     # Bollinger upper break
    "CBlock_CloseAboveKCUpper_Brk",     # Keltner upper break
    "CBlock_CloseAbovePrevDayHigh_Brk", # prior-day high break
    "CBlock_CloseAboveHHLLUpper_Brk",   # N-bar highest break
]


def main():
    _, _, B = load_catalog("catalog.json")
    missing = [k for k in KEYS if k not in B]
    if missing:
        raise SystemExit(f"NOT IN CATALOG: {missing}")
    grp = make_group("BreakoutTriggersLong_Smoke", "Condition",
                     [hybrid_ref(B[k]) for k in KEYS], category="Breakout")
    out = SKILL_ROOT / "BreakoutTriggersLong_Smoke.xml"
    out.write_text(wrap_groups([grp]), encoding="utf-8")
    print(f"wrote {out}  (1 group, {len(KEYS)} items)")


if __name__ == "__main__":
    main()
