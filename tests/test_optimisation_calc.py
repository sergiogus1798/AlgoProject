#!/usr/bin/env python3
"""Known-answer tests: wfm per-cell Sharpe, the MC Retest ratio, the SPP design levels."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.wfm.measure import equity


def test_wfm_cell_sharpe_rolls_a_weekend_close_to_monday() -> None:
    """Fri 10, Sun 500, Mon -20, Tue 30: the Sunday close counts on Monday (480), Sharpe 10.35."""
    close = pd.to_datetime(["2024-01-05", "2024-01-07", "2024-01-08", "2024-01-09"])
    trades = pd.DataFrame(
        {
            "strategy": "s",
            "sample": "OOS",
            "result": "c",
            "Close time": close,
            "Profit/Loss": [10.0, 500.0, -20.0, 30.0],
        }
    )
    got = equity.per_cell(trades, "s")["sharpe"].iloc[0]
    assert abs(got - 10.35) < 0.01, got


if __name__ == "__main__":
    test_wfm_cell_sharpe_rolls_a_weekend_close_to_monday()
    print("ok")


def test_negative_original_is_no_ratio() -> None:
    """A strategy that lost in the original has no 'share kept': -200 against -100 is not 2.0."""
    from studies.breakage.mcRetest.verdict import scoring

    result = {
        "s": {
            "original_net": -100.0,
            "fragility": {"net_p5": {"point": -200.0}},
            "modes": {"perturbed": True},
        }
    }
    from studies.breakage.mcRetest.inputs import tasks

    key = next(k for k, r in tasks.ROLE.items() if r == "execution")
    result = {key: result["s"]}
    assert scoring._kept(result, "execution") == 1.0, "no valid ratio: the neutral 1.0"


def test_design_levels_widen_on_the_right_side_of_a_negative_original() -> None:
    """Original -10, min_span 0.3: the span reaches -13..-7 (it was -7..-13, the wrong side)."""
    from studies.breakage.spp.model import profile

    levels = pd.DataFrame({"level": np.arange(-20.0, 1.0)})
    call_ = {"center": -10.0, "argmax": -10.0, "from": -10.0, "to": -10.0}
    got = profile.design_levels(levels, call_, -10.0, 8, 0.3)
    assert min(got) <= -13 and max(got) >= -7, got
