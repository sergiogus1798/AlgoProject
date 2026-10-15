"""The development pool takes only current-cost work (owner, 2026-10-15): no Test_Calib_*, nothing before 2026-10-01."""

import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from portfolio.common.construct import candidates  # noqa: E402

rows = {
    "Test_Calib_A": {"created": "2026-10-05 10:00"},
    "Trade_Old": {"created": "2026-09-30 23:59"},
    "Trade_New": {"created": "2026-10-01 00:00"},
}
with mock.patch.object(candidates, "_row", rows.get):
    got = {n: candidates.in_pool(n) for n in (*rows, "Unknown")}
assert got == {
    "Test_Calib_A": False,
    "Trade_Old": False,
    "Trade_New": True,
    "Unknown": False,
}, got
print("OK pool filter")
