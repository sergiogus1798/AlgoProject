#!/usr/bin/env python3
"""Step 20's rule: its cut is the bank 21 and 24 read from, and only the study's DESCARTAR fails."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import survivors


def test_step_20_cuts_descartar_and_keeps_revisar() -> None:
    """Step 20 carries a cut (the bank 21 and 24 read from) and its rule drops only the
    study's DESCARTAR: REVISAR and MANTENER mothers stay among the survivors."""
    from pipeline.autopilot import criteria, judge

    spec = judge.settings()["steps"]["20"]
    assert (
        spec["cut"]
        == judge.settings()["steps"]["16"]["cut"]
        == survivors.bank(judge.settings(), "21")
    )
    key = "blindJoint.verdict_csv.drop"
    found = pd.DataFrame({"who": ["d", "r", "m"], "key": key, "value": [1.0, 0.0, 0.0]})
    got = criteria.outcomes(found, ["d", "r", "m"], spec["rules"])
    assert {w for w, (state, _) in got.items() if state != "fail"} == {
        "r",
        "m",
    } and got["d"][0] == "fail"


if __name__ == "__main__":
    test_step_20_cuts_descartar_and_keeps_revisar()
    print("ok")
