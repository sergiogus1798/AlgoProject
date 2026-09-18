#!/usr/bin/env python3
"""Golden-file test for core.sqxretest: the Monte Carlo Retest reader every later number rests on."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import sqxretest

FIXTURE = Path(__file__).parent / "fixtures" / "retest.sqx"
GOLDEN = Path(__file__).parent / "fixtures" / "retest.golden.json"
# Enough of the 148 to catch a shifted or mis-decoded blob without pinning the whole table.
WATCHED = ("NetProfit", "Drawdown", "NumberOfTrades", "ProfitFactor", "MaxLoss", "StandardDev")


def parse() -> dict:
    """Everything core.sqxretest reads out of the fixture.

    Returns:
        The simulation layout with a per-simulation census, the original P/L, the eleven
        confidence levels reduced to the watched metrics, and the declared provenance.
        The census is what catches a reader that silently drops or reorders a simulation.
    """
    sims = sqxretest.simulations(FIXTURE)
    offsets, pnl = sims["offsets"], sims["pnl"]
    census = [{"index": int(i),
               "trades": int(offsets[k + 1] - offsets[k]),
               "sum_cents": int(pnl[offsets[k]:offsets[k + 1]].sum()),
               "first": int(pnl[offsets[k]]),
               "last": int(pnl[offsets[k + 1] - 1])}
              for k, i in enumerate(sims["index"])]
    levels = sqxretest.levels(FIXTURE)
    original = sqxretest.original(FIXTURE)
    return {"simulations": census,
            "total_trades": int(pnl.size),
            "offsets_end": int(offsets[-1]),
            "original": {"trades": int(original.size), "sum_cents": int(original.sum()),
                         "stored_netprofit": round(
                             float(sqxretest.reference(FIXTURE)["NetProfit"]), 4)},
            "levels": {str(level): {k: round(float(levels[level][k]), 4) for k in WATCHED}
                       for level in sorted(levels)},
            "level_metric_count": {str(level): len(levels[level]) for level in sorted(levels)},
            "reference_metric_count": len(sqxretest.reference(FIXTURE)),
            "meta": sqxretest.meta(FIXTURE),
            "settings": sqxretest.settings(FIXTURE)}


def invariants(result: dict) -> list[str]:
    """Properties that must hold whatever the fixture is, checked beside the golden file.

    Args:
        result: What parse() returned.

    Returns:
        One message per broken invariant. The first is the load-bearing one: it ties the
        binary decoder to the XML decoder, so a flipped byte order, a wrong header width or
        an off-by-one offset breaks it even if someone blesses the golden file over the top.
    """
    out = []
    bridge = result["original"]["sum_cents"] / 100.0
    stored = result["original"]["stored_netprofit"]
    # The .bin rounds every trade to a whole cent, so the sum may drift by up to one cent per
    # trade against the float SQX stored. Anything wider is a decoder bug, not rounding.
    if abs(bridge - stored) > 0.01 * result["original"]["trades"]:
        out.append(f"the original P/L sums to {bridge:.2f} but SQX stored {stored:.2f}: "
                   "the binary and the XML no longer agree")
    index = [s["index"] for s in result["simulations"]]
    if index != list(range(len(index))):
        out.append("simulation indices are not 0..n-1: they truncate at the tail, never gap")
    if result["offsets_end"] != result["total_trades"]:
        out.append("the last offset does not reach the end of the P/L array")
    if sorted(int(k) for k in result["levels"]) != list(sqxretest.CONFIDENCE):
        out.append("the eleven confidence levels are not the ones SQX produces")
    if set(result["level_metric_count"].values()) != {148}:
        out.append("a level blob no longer holds 148 metrics")
    if result["reference_metric_count"] != 152:
        out.append("the original blob no longer holds 152 metrics")
    return out


def main() -> None:
    """Compare against the golden file, or write it when run with --bless."""
    result = parse()
    broken = invariants(result)
    if "--bless" in sys.argv:
        if broken:
            print("test_sqxretest: REFUSING to bless — an invariant is broken")
            for message in broken:
                print("  invariant:", message)
            sys.exit(1)
        GOLDEN.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"blessed {GOLDEN}")
        return
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if result == expected and not broken:
        print("test_sqxretest: ok")
        return
    print("test_sqxretest: FAILED — core.sqxretest no longer reads this retest the same way")
    for message in broken:
        print("  invariant:", message)
    if result != expected:
        print(json.dumps(result, indent=2)[:2000])
    sys.exit(1)


if __name__ == "__main__":
    main()
