#!/usr/bin/env python3
"""Step 20 only diagnoses (owner, 2026-10-15, C8 A): its cut stays the bank 21 and 24 read from,
and with no rule a DESCARTAR mother is not cut — the tail's only cut is 19.5."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import survivors


def test_step_20_keeps_its_bank_and_cuts_nobody() -> None:
    """The bank 21 and 24 read from is still 20's `cut`; its empty rules leave DESCARTAR in."""
    from pipeline.autopilot import criteria, judge

    spec = judge.settings()["steps"]["20"]
    assert (
        spec["cut"]
        == judge.settings()["steps"]["16"]["cut"]
        == survivors.bank(judge.settings(), "21")
    )
    assert spec["rules"] == []
    key = "blindJoint.verdict_csv.drop"
    found = pd.DataFrame({"who": ["d", "r"], "key": key, "value": [1.0, 0.0]})
    got = criteria.outcomes(found, ["d", "r"], spec["rules"])
    assert all(state != "fail" for state, _ in got.values())


if __name__ == "__main__":
    test_step_20_keeps_its_bank_and_cuts_nobody()
    print("ok")
