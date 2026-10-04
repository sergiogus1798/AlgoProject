#!/usr/bin/env python3
"""Known-answer test: the MC Retest's analytic PSR is the ORIGINAL's per-trade PSR, never the PSR
of one net total per simulation (which saturates at 1.0 and keeps the edge veto from firing)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import significance
from studies.breakage.mcRetest import run


def test_psr_is_per_trade_of_the_original() -> None:
    """500 trades N(2, 100): per-trade PSR ~0.67 < the 0.90 gate, while 1,000 re-runs net positive."""
    rng = np.random.default_rng(0)
    trades = rng.normal(2.0, 100.0, 500)
    sims = rng.normal(2.0, 100.0, (1000, 500))
    cents = pd.DataFrame({"sim": np.repeat(np.arange(1000), 500), "pnl": sims.ravel()})
    seen: dict = {}
    run.store.load_pnl = lambda **kw: cents
    run.store.load_trades = lambda **kw: pd.DataFrame({"pnl": trades})
    run.per_task = lambda *a, **kw: {}
    run.attribution.describe = lambda *a, **kw: {}
    run.gates.check = lambda body, *a: seen.update(body) or []
    run.scoring.subscores = lambda *a: {}
    run.scoring.verdict = lambda *a: "x"
    run.one({}, None, None, {}, "1.2.3", 0.0, {})
    expected = significance.psr(trades, 0.0)["psr"]
    assert abs(seen["psr"]["psr"] - expected) < 1e-9, seen["psr"]
    assert seen["psr"]["n"] == 500 and seen["psr"]["psr"] < 0.9


def test_old_ingest_without_pnl_stops_with_a_message() -> None:
    """An ingest that predates the per-trade P/L must stop in Spanish, not raise KeyError."""
    run.store.load_trades = lambda **kw: pd.DataFrame({"x": [1.0]})
    try:
        run.battery({}, {}, None, None, {})
    except SystemExit as stop:
        assert "repite el ingest" in str(stop)
    else:
        raise AssertionError("no SystemExit")


if __name__ == "__main__":
    test_psr_is_per_trade_of_the_original()
    test_old_ingest_without_pnl_stops_with_a_message()
    print("ok")
