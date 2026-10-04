#!/usr/bin/env python3
"""Known-answer tests: MC Retest reconstruction of a simulation with no trades, and `underwater`."""

import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.mcRetest.model import recon
from studies.breakage.mcRetest.verdict import fragility


def test_empty_simulation_reads_zero() -> None:
    """Sims [100, -50], [], [200]: NetProfit [50, 0, 200] (was [50, 200, 200]); an empty last one is fine."""
    pnl = np.array([10000, -5000, 20000], dtype=np.int64)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = recon.frame(pnl, np.array([0, 2, 2, 3]), 10000.0)
        last = recon.frame(pnl, np.array([0, 2, 3, 3]), 10000.0)
    assert np.allclose(got["NetProfit"], [50, 0, 200]), got["NetProfit"]
    assert not np.isinf(got["AvgTrade"]).any()
    assert np.allclose(last["NetProfit"], [50, 200, 0])


def test_empty_simulation_after_a_multi_trade_one() -> None:
    """Offsets [0, 3, 3] over [100, 50, 0.. ]: NetProfit [150, 0] (clamping gave [..cut short..])."""
    pnl = np.array([10000, 5000, 0], dtype=np.int64)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = recon.frame(pnl, np.array([0, 3, 3]), 10000.0)
    assert np.allclose(got["NetProfit"], [150, 0]), got["NetProfit"]
    from studies.breakage.mcRetest.model import drawdown
    assert np.allclose(drawdown.reduce(np.add, np.array([1., 2, 4]), np.array([0, 3, 3])), [7, 0])


def test_underwater_counts_the_starting_balance() -> None:
    """P/L [-50, -10, 20] is under its start on all three trades: 1.0 (was 0.333)."""
    out = fragility.underwater(np.array([-50.0, -10.0, 20.0]), np.array([0, 3]))
    assert abs(out[0] - 1.0) < 1e-12, out


if __name__ == "__main__":
    test_empty_simulation_reads_zero()
    test_empty_simulation_after_a_multi_trade_one()
    test_underwater_counts_the_starting_balance()
    print("ok")
