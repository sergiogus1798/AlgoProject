#!/usr/bin/env python3
"""Golden-file test for core.sqxfile: a parser that breaks silently poisons every analysis."""

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import sqxfile

FIXTURE = Path(__file__).parent / "fixtures" / "strategy.sqx"
GOLDEN = Path(__file__).parent / "fixtures" / "strategy.golden.json"


def parse() -> dict:
    """Everything core.sqxfile reads out of the fixture strategy.

    Returns:
        Identity hash, symbol and feed, every parameter, and a census of the rule tree —
        the census catches an XML change the flat fields would miss.
    """
    blocks = collections.Counter(
        (item.get("categoryType"), item.get("key")) for item in sqxfile.xml(FIXTURE).iter("Item"))
    return {"identity": sqxfile.identity(FIXTURE),
            "symbol": list(sqxfile.symbol(FIXTURE)),
            "parameters": sqxfile.parameters(FIXTURE),
            "blocks": {f"{c}/{k}": n for (c, k), n in sorted(blocks.items(), key=str)}}


def main() -> None:
    """Compare against the golden file, or write it when run with --bless."""
    result = parse()
    if "--bless" in sys.argv:
        GOLDEN.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"blessed {GOLDEN}")
        return
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if result == expected:
        print("test_sqxfile: ok")
        return
    print("test_sqxfile: FAILED — core.sqxfile no longer reads this strategy the same way")
    print(json.dumps(result, indent=2)[:2000])
    sys.exit(1)


if __name__ == "__main__":
    main()
