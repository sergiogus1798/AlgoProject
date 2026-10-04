"""mt5.report.start_check on a real tester report and its journal: 22 % history and a start moved to 2008-12-03."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import MT5_DATA  # noqa: E402
from mt5 import report, wine  # noqa: E402

RUN = MT5_DATA / "tests" / "V100545_Strategy_10_1_79_hantec_USDJPY.h_H1_2008-07-01_2026-09-24_ohlc_m1"
JOURNAL = wine.data_dir() / "Tester" / "logs" / "20260930.log"

summary, deals = report.read(RUN / "report.htm")
got = report.start_check(summary, report.trades(deals), JOURNAL.read_bytes().decode("utf-16"),
                         "AlgoProject\\V100545_Strategy_10_1_79.ex5", "2008-07-01")
print(got)
assert got == {"history_quality_pct": 22.0, "first_trade": "2022-06-08", "start_asked": "2008-07-01",
               "start_actual": "2008-12-03", "start_changed": True}
# the 2022-06-01 run of the same day was not moved
other = report.start_check({"History Quality": "76%"}, report.trades(deals),
                           JOURNAL.read_bytes().decode("utf-16"),
                           "AlgoProject\\V101227_Strategy_10_1_79.ex5", "2022-06-01")
assert not other["start_changed"] and other["history_quality_pct"] == 76.0
print("ok")
