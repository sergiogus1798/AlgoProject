#!/usr/bin/env python3
"""The MC Retest perturbation ranges a task randomises within, taken from assets/."""

import re

from core.assetdata import mc_retest

# The three methods that draw a value from a range, each named by the key its range
# carries in `assets/symbols/<SYM>.yaml`. All three are absolute point ranges.
RANDOMIZE = {"spread": "RandomizeSpread", "slippage": "RandomizeSlippage",
             "min_distance": "RandomizeMinDistance"}


def set_ranges(text: str, data: dict) -> dict[str, int]:
    """Put this asset's declared MC Retest ranges into a task, in place.

    Args:
        text: A task XML.
        data: One asset as load() returned it.

    Returns:
        Range name to how many <Method> blocks were rewritten, and the new text under
        "text". Unlike a cost, these live in the task's own <Method> blocks and not in
        <InstrumentInfo>, so they ARE writable — the registry never sees them. A range
        still at null, or one the asset does not declare at all, is skipped rather than
        invented, and only a `use="true"` method is touched: the ranges of a method the
        task does not run are left as the donor wrote them.
    """
    out = {"text": text}
    for name, method in RANDOMIZE.items():
        span = mc_retest(data).get(name, {"min": None, "max": None})
        if span["min"] is None or span["max"] is None:
            out[name] = 0
            continue
        pattern = (rf'(<Method use="true" type="{method}">\s*<Params>\s*'
                   rf'<Param key="Min"[^>]*>)[^<]*(</Param>\s*<Param key="Max"[^>]*>)[^<]*(</Param>)')
        out["text"], out[name] = re.subn(pattern,
                                         rf"\g<1>{span['min']}\g<2>{span['max']}\g<3>",
                                         out["text"])
    return out
