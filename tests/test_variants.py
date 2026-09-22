#!/usr/bin/env python3
"""Golden-file test for sqx.variants: a rewriter that breaks silently fabricates a wrong study."""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.variants import tuples
from sqx.variants.build import rewrite

FIXTURE = Path(__file__).parent / "fixtures" / "strategy.sqx"
GOLDEN = Path(__file__).parent / "fixtures" / "variants.golden.json"
VARIANT_ID = "P00042"
NAME = "Strategy 1.25.215 P00042"
# Two ints and two doubles: writing 95.0 into an int parameter is not the same file as 95,
# and a tuple that only ever touched ints would never show it.
TUPLE = {"AroonCrossesPeriod1": 88.0, "StochasticKPeriod1": 21.0,
         "ProfitTargetCoef1": 14.25, "StopLossCoef1": 7.0}


def digest(blob: bytes) -> str:
    """Short hash of one member.

    Args:
        blob: The member's bytes.

    Returns:
        First 16 hex characters of its SHA-256.
    """
    return hashlib.sha256(blob).hexdigest()[:16]


def parse() -> dict:
    """Everything the rewriter produces from the fixture, for all three shapes.

    Returns:
        The values read back, both name fields, the stamp, the tuple hash, and a digest
        of every member of every shape. The digests are what catch a change that leaves
        the parsed fields looking right.
    """
    parent = rewrite.members(FIXTURE)
    parts = rewrite.variant(parent, VARIANT_ID, NAME, TUPLE)
    portfolio = parts[rewrite.PORTFOLIO].decode("utf-8")
    settings = parts[rewrite.SETTINGS].decode("utf-8")
    return {"values": rewrite.values(portfolio),
            "result_name": rewrite.RESULT_NAME.search(settings).group(0),
            "strategy_name": rewrite.STRATEGY_NAME.search(settings).group(0),
            "stamp": rewrite.stamped(portfolio),
            "tuple_hash": tuples.tuple_hash(TUPLE),
            "shapes": {shape: {name: digest(blob) for name, blob in parts.items()
                               if keep(name)}
                       for shape, keep in rewrite.SHAPES.items()}}


def invariants() -> list[str]:
    """Properties that must hold whatever the golden file says.

    Returns:
        One message per broken invariant. `--bless` refuses to write while any is broken,
        so blessing a genuinely changed output cannot also bless a corrupted one.

        The load-bearing one is the last: rewriting the parent's own tuple back into the
        parent has to reproduce the parent's `strategy_Portfolio.xml` byte for byte apart
        from the stamp. It ties the reader and the writer together, so a regex that
        matched the wrong block, a number formatted a new way or a lost member fails even
        if someone regenerates the golden file over the top.
    """
    parent = rewrite.members(FIXTURE)
    portfolio = parent[rewrite.PORTFOLIO].decode("utf-8")
    parts = rewrite.variant(parent, VARIANT_ID, NAME, TUPLE)
    new = parts[rewrite.PORTFOLIO].decode("utf-8")
    out = []

    read_back = {k: float(v) for k, v in rewrite.values(new).items() if k in TUPLE}
    if read_back != TUPLE:
        out.append(f"values did not survive the round trip: {read_back} != {TUPLE}")
    if rewrite.values(new)["StochasticDPeriod1"] != rewrite.values(portfolio)["StochasticDPeriod1"]:
        out.append("a parameter outside the tuple was rewritten")
    if "<Fingerprint" in parts[rewrite.SETTINGS].decode("utf-8"):
        out.append("the inherited fingerprint is still there")
    if set(parts) != set(parent):
        out.append("variant() changed the member list; only save() may do that")
    for name in set(parent) - {rewrite.PORTFOLIO, rewrite.SETTINGS}:
        if parts[name] != parent[name]:
            out.append(f"{name} was modified and must not be")

    same = rewrite.variant(parent, VARIANT_ID, NAME,
                           {k: float(v) for k, v in rewrite.values(portfolio).items()
                            if k in TUPLE})
    if same[rewrite.PORTFOLIO].decode("utf-8").replace(
            f"<!--variant_id:{VARIANT_ID}-->", "") != portfolio:
        out.append("rewriting the parent's own tuple did not reproduce the parent")
    return out


def main() -> None:
    """Compare against the golden file, or write it when run with --bless."""
    broken = invariants()
    for message in broken:
        print(f"test_variants: INVARIANT — {message}")
    result = parse()
    if "--bless" in sys.argv:
        if broken:
            sys.exit("test_variants: refusing to bless while an invariant is broken")
        GOLDEN.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"blessed {GOLDEN}")
        return
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if result == expected and not broken:
        print("test_variants: ok")
        return
    if result != expected:
        print("test_variants: FAILED — the rewriter no longer produces this file")
        print(json.dumps(result, indent=2)[:2000])
    sys.exit(1)


if __name__ == "__main__":
    main()
