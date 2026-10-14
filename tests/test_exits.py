#!/usr/bin/env python3
"""`sqx.projects.orders.exits_set`: a portfolio with an exit method set vs one that exits by condition only.

RandomizeExitParameters over a population with no exit method set hangs SQX for ever (🔬 2026-10-06),
so the probe that switches it off must tell the two apart on the Params SQX always writes.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects.orders import exits_set  # noqa: E402

text = (Path(__file__).parent / "fixtures" / "nostop_portfolio.xml").read_text()
assert exits_set(text), "the fixture has an exit method set"
none = re.sub(
    r'(<Param\b[^>]*\bexitMethod="true"[^>]*>)(.*?)(</Param>)',
    lambda m: (
        m.group(1)
        + (
            '<Formula key="SQ.Formulas.SLPT.None" />'
            if "<Formula" in m.group(2)
            else "0"
        )
        + m.group(3)
    ),
    text,
    flags=re.S,
)
assert not exits_set(none), "every exit method at .None or 0 means nothing to perturb"
bars = re.sub(
    r'(<Param\b[^>]*key="#ExitAfterBars\.ExitAfterBars#"[^>]*>)0(</Param>)',
    r"\1ExitAfterBars1\2",
    none,
)
assert bars != none and exits_set(bars), "a variable name counts as set"
print("ok")
