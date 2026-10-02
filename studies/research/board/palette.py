#!/usr/bin/env python3
"""The free hole's block families for an idea of one family, by the two rules of the dossier's §5."""

import argparse

from sqx.blocks.taxonomy import family_blocks
from studies.research.board.inputs import CONFIG

RELATION = {"orthogonal": "ortogonal: lee otra clase de dato que la condición fija",
            "counter": "contratendencia: lo contrario de la condición fija",
            "same_data": "mismo dato, otra lectura",
            "alike": "FUERA: dos iguales, sólo encarece la entrada",
            "own": "FUERA: la propia familia de la condición fija"}


def relation(fixed: str, other: str, rules: dict) -> str:
    """How a hole family relates to the fixed condition's family (taxonomy keys)."""
    if other == fixed:
        return "own"
    if rules["data"][other] != rules["data"][fixed]:
        return "orthogonal"
    alike, counter = rules["alike"], rules["counter"]
    if fixed in alike and other in alike:
        return "alike"
    if {fixed, other} & {counter} and {fixed, other} & set(alike):
        return "counter"
    return "same_data"


def hole(family: str, role: str | None = "signal") -> list[dict]:
    """The families the free hole may draw from, heaviest first, with their blocks.

    Args:
        family: The idea's family in the profile's key (`momentum`, `ruptura`…).
        role: The block role asked of `family_blocks`; None for every role.

    Returns:
        One row per taxonomy family: `family`, `relation`, `weight` (0 = kept out), `why`
        and `blocks` (key → its weight in that family; empty when kept out).
    """
    rules = CONFIG["palette"]
    fixed = CONFIG["taxonomy_family"][family]
    rows = []
    for other in rules["data"]:
        rel = relation(fixed, other, rules)
        weight = rules["weights"].get(rel, 0)
        rows.append({"family": other, "relation": rel, "weight": weight, "why": RELATION[rel],
                     "blocks": family_blocks(other, rules["min_block_weight"], role=role)
                     if weight else {}})
    return sorted(rows, key=lambda r: (-r["weight"], r["family"]))


def main() -> None:
    """Print the hole's families for one idea family, with how many blocks each brings."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("family", choices=list(CONFIG["taxonomy_family"]))
    ap.add_argument("--blocks", type=int, default=8, help="bloques de ejemplo por familia")
    a = ap.parse_args()
    print(f"Hueco libre para una idea de {a.family} ({CONFIG['taxonomy_family'][a.family]}):")
    for r in hole(a.family):
        some = ", ".join(list(r["blocks"])[:a.blocks])
        print(f"  peso {r['weight']}  {r['family']:<15} {len(r['blocks']):>3} bloques  {r['why']}"
              + (f"\n          {some}" if some else ""))


if __name__ == "__main__":
    main()
