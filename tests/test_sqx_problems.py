"""core.sqxfile.strategy_problems decodes SQX's «Strategy Problems» bitmask on a real strategy (value 8)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import sqxfile  # noqa: E402
from core.paths import MASTER  # noqa: E402

PATH = MASTER / "user/projects/GBPJPY_H1/databanks/RetestPairs/Strategy 9.19.191.sqx"
got = sqxfile.strategy_problems(PATH)
print(got)
assert got == {"value": 8, "reasons": ["TooShortTrades"], "unknown": 0}
print("ok")
