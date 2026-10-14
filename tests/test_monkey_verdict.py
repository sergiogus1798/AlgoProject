#!/usr/bin/env python3
"""The monkey's headline call: a NaN p-value is «no medible», never a fail (encargo 68 D21)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.monkey import one

CFG = {"nulls": {"headline": "timing"}}
CHECKS = {"corr": 1.0, "fill": 0}


def test_nan_p_is_not_measurable() -> None:
    """Constant P&L gives a NaN statistic and a NaN p: «no medible», state none, with its reason."""
    said = one.call(float("nan"), 0.05, "sharpe", CFG, CHECKS)
    assert said["label"] == "no medible" and said["state"] == "none"
    assert "constante" in said["meaning"] and said["score"] is None


def test_finite_p_keeps_its_calls() -> None:
    """Below alpha beats the monkey; above, does not."""
    assert one.call(0.01, 0.05, "net", CFG, CHECKS)["state"] == "pass"
    assert one.call(0.40, 0.05, "net", CFG, CHECKS)["label"] == "no se distingue del mono"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))


def test_flat_run_has_no_sharpe_and_no_p() -> None:
    """A constant-P&L run has a NaN Sharpe (not inf), and so a NaN p: the call is «no medible»."""
    import numpy as np
    from engines.nulls import stats, verdict
    pnl = np.array([[5.0, 5.0, 5.0, 5.0], [1.0, -2.0, 3.0, 0.5]])
    got = stats.measure(pnl, ["sharpe"])["sharpe"]
    assert np.isnan(got[0]) and np.isfinite(got[1])
    assert np.isnan(verdict.pvalue(got[0], got[1:], "sharpe"))
