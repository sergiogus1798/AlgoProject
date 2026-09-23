#!/usr/bin/env python3
"""The MC Retest perturbation ranges a task randomises within, taken from assets/."""

import re

from core.assetdata import mc_retest

# The two methods that draw a value from a range. `RandomizeMinDistance` has the same
# shape and is deliberately not here: the owner asked for these two.
RANDOMIZE = {"spread": "RandomizeSpread", "slippage": "RandomizeSlippage"}


def set_ranges(text: str, data: dict) -> dict[str, int]:
    """Put this asset's declared MC Retest ranges into a task, in place.

    Args:
        text: A task XML.
        data: One asset as load() returned it.

    Returns:
        Range name to how many <Method> blocks were rewritten, and the new text under
        "text". Unlike a cost, these live in the task's own <Method> blocks and not in
        <InstrumentInfo>, so they ARE writable — the registry never sees them. A range
        still at null is skipped rather than invented.
    """
    out = {"text": text}
    for name, method in RANDOMIZE.items():
        span = mc_retest(data)[name]
        if span["min"] is None or span["max"] is None:
            out[name] = 0
            continue
        pattern = (rf'(<Method use="true" type="{method}">\s*<Params>\s*'
                   rf'<Param key="Min"[^>]*>)[^<]*(</Param>\s*<Param key="Max"[^>]*>)[^<]*(</Param>)')
        out["text"], out[name] = re.subn(pattern,
                                         rf"\g<1>{span['min']}\g<2>{span['max']}\g<3>",
                                         out["text"])
    return out
