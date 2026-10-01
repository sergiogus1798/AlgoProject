#!/usr/bin/env python3
"""Known answers for SQX's WFM objectives and area rule: one hand-built cell, one 6x5 matrix."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import wfmobjectives
from studies.optimisation.wfm.measure import gaterule

DAY = wfmobjectives.DAY_MS


def step(opt_from: int, opt_days: int, run_days: int, opt: dict, run: dict | None) -> object:
    """A `WalkForwardPeriod` whose stats `records` will hand back as given."""
    import xml.etree.ElementTree as ET
    p = ET.Element("WalkForwardPeriod", optimizeFrom=str(opt_from * DAY),
                   optimizeTo=str((opt_from + opt_days) * DAY + DAY - 1),
                   runFrom=str((opt_from + opt_days + 1) * DAY),
                   runTo=str((opt_from + opt_days + 1 + run_days) * DAY + DAY - 1))
    ET.SubElement(ET.SubElement(ET.SubElement(p, "OptimizationStats"), "stats"),
                  "SQStats").text = repr(opt)
    if run is not None:
        ET.SubElement(ET.SubElement(ET.SubElement(p, "RunStats"), "stats"),
                      "SQStats").text = repr(run)
    return p


def test_one_cell() -> None:
    """Three steps, the last never run: stability per day, the specials, the truncation."""
    real = wfmobjectives.sqxstats.records
    wfmobjectives.sqxstats.records = eval        # the blobs above are dict literals
    try:
        check()
    finally:
        wfmobjectives.sqxstats.records = real


def check() -> None:
    """The cell's numbers, worked by hand."""
    s = lambda n, pf, t, dd: {"NetProfit": n, "ProfitFactor": pf, "NumberOfTrades": t,
                              "DrawdownPct": dd}
    steps = [step(0, 100, 50, s(1000, 2.0, 40, 5), s(300, 1.5, 21, 8)),
             step(50, 100, 50, s(1000, 2.0, 40, 5), s(-100, 0.9, 30, 12)),
             step(100, 100, 50, s(500, 1.8, 20, 4), None)]
    # NetProfit per day: run 200 / 100 days over opt 2000 / 200 days -> 20 %.
    assert wfmobjectives._stability(steps, "NetProfit") == 20.0
    # PF is not per day: (1.5 + 0.9) / (2 + 2) -> 60 %.
    assert wfmobjectives._stability(steps, "ProfitFactor") == 60.0
    # Trades per day: 51 / 100 over 80 / 200 -> 127.5, truncated as SQX's Integer column.
    import xml.etree.ElementTree as ET
    run = ET.Element("RunResult")
    periods = ET.SubElement(run, "Periods")
    periods.extend(steps)
    assert wfmobjectives.value(run, None, {}, "stability", "NumberOfTrades") == 127.0
    assert wfmobjectives._special(steps, "WFPctOfProfitableRuns") == 50.0     # 1 of 2
    assert wfmobjectives._special(steps, "WFMaxProfitByRunInPct") == 150.0    # 300 of 200
    assert wfmobjectives._special(steps, "WFMinTradesInRun") == 21.0
    assert wfmobjectives._special(steps, "WFMaxPctDDbyRun") == 12.0


def test_area_and_centre() -> None:
    """The first best 4x4 rectangle wins, its centre is offset (1, 1)."""
    passed = np.zeros((6, 5), dtype=bool)
    passed[1:5, 1:5] = True                     # 16 in the rectangle at (1, 1)
    passed[0, 0] = True
    got = gaterule.area(passed, passed * 100, 4, 4, 12)
    assert got == {"passed": True, "count": 16, "corner": (1, 1), "centre": (2, 2)}
    small = gaterule.area(passed, np.arange(30).reshape(6, 5), 7, 7, 2)
    assert small["count"] == 1 and not small["passed"] and small["centre"] == (5, 4)


if __name__ == "__main__":
    test_one_cell()
    test_area_and_centre()
    print("ok")
