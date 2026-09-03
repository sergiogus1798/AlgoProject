"""gen_group_example.py — worked template for authoring random groups.

Builds four pools, one of each shape, from your bootstrapped catalog:
  1. INLINE Condition  — fresh boolean rules (simpleRules + a Close>EMA comparison)
  2. INLINE Value      — bare indicator value lines (EMA / ATR …) for a price/level slot
  3. HYBRID Condition  — a pool of your existing boolean CBlock_* custom blocks
  4. HYBRID Value      — a pool of your existing Price-level CBlock_* custom blocks

A group is a MENU the builder samples one item from per strategy. An item is FLAT —
a single rule or one comparison; compound AND/OR logic belongs in a custom block,
then pooled by reference (HYBRID).

The keys below are chosen from YOUR catalog at runtime, so this runs as-is. When you
author for real, open `catalog.md` and pick the rules / value atoms / blocks you want.

Run:
  python examples/gen_group_example.py catalog.json out.xml
  python engine/validate.py out.xml --catalog catalog.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from engine.groups import (  # noqa: E402
    load_catalog, inline_item, is_greater, is_lower, number,
    hybrid_ref, make_group, wrap_groups,
)


def _pick(preferred, available, n):
    """Prefer recognizable keys if this install has them; else take what it has."""
    chosen = [k for k in preferred if k in available]
    chosen += [k for k in available if k not in chosen]
    return chosen[:n]


def build(catalog_path: str) -> list[str]:
    _, T, B = load_catalog(catalog_path)
    raw = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    rules, values = raw.get("rules", {}), raw.get("values", {})
    groups: list[str] = []

    # 1 — INLINE Condition: a couple of simpleRules + one comparison.
    rule_keys = _pick(["MomRising", "HMARising", "RSIRising", "ATRRising", "StdDevRising"],
                      list(rules), 2)
    cond_items = [inline_item(T[k], optimize={p: "default" for p in _periods(T[k])})
                  for k in rule_keys]
    if "Close" in T and "EMA" in T:                       # Close > EMA(opt)
        cond_items.append(is_greater(inline_item(T["Close"]),
                                     inline_item(T["EMA"], optimize={"#Period#": "10:60:5"})))
    if "RSI" in T:                                         # RSI < 30 (threshold via a constant)
        cond_items.append(is_lower(inline_item(T["RSI"]), number("30")))
    if cond_items:
        groups.append(make_group("InlineFilters_Example", "Condition", cond_items,
                                 category="Examples"))

    # 2 — INLINE Value: bare indicator value lines for a price/level slot.
    val_keys = _pick(["EMA", "SMA", "ATR", "Highest", "Lowest"], list(values), 3)
    val_items = [inline_item(T[k], optimize={p: "default" for p in _periods(T[k])})
                 for k in val_keys]
    if val_items:
        groups.append(make_group("InlineLevels_Example", "Value", val_items,
                                 category="Examples"))

    # 3 — HYBRID Condition: a pool of your existing boolean custom blocks.
    cond_blocks = [k for k, v in B.items() if v.get("returnType") == "boolean"][:5]
    if cond_blocks:
        groups.append(make_group("MyConditionBlocks_Example", "Condition",
                                 [hybrid_ref(B[k]) for k in cond_blocks], category="Examples"))

    # 4 — HYBRID Value: a pool of your existing Price-level custom blocks.
    level_blocks = [k for k, v in B.items() if v.get("type") == "Price level"][:5]
    if level_blocks:
        groups.append(make_group("MyLevelBlocks_Example", "Value",
                                 [hybrid_ref(B[k]) for k in level_blocks], category="Examples"))

    return groups


def _periods(elem) -> list[str]:
    """Keys of the period/double knobs on an atom (so the example optimizes them)."""
    out = []
    for p in elem.findall("Param"):
        if p.get("paramType") == "period" or p.get("type") == "double":
            if p.get("controlType") != "combo" and p.get("key"):
                out.append(p.get("key"))
    return out


def main(argv):
    catalog_path = argv[0] if argv else "catalog.json"
    out_path = argv[1] if len(argv) > 1 else "out.xml"
    groups = build(catalog_path)
    Path(out_path).write_text(wrap_groups(groups), encoding="utf-8")
    print(f"wrote {out_path}  ({len(groups)} groups)")
    print(f"validate:\n  python engine/validate.py {out_path} --catalog {catalog_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
