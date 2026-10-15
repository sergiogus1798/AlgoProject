#!/usr/bin/env python3
"""edgeCost on trades built by hand: oos1 only, the common repricer's cost as the denominator."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market import reprice  # noqa: E402
from studies.readings.edgeCost import costs, many, one  # noqa: E402
from studies.screening.analysis import onepass  # noqa: E402

COSTS = {
    "point_value": 10.0,
    "tick_size": 0.1,
    "spread": 0.2,
    "slippage": 0.1,
    "commission_method": "SizeBased",
    "rounds": True,
    "commission": 1.0,
    "swap_long": -2.0,
    "swap_short": -2.0,
    "triple": 2,
    "rollover": 23,
    "tick_step": None,
}
BARS = pd.DataFrame(
    {"Open": 100 + np.cumsum(np.random.default_rng(0).normal(0, 0.3, 400))},
    index=pd.date_range("2020-01-01", periods=400, freq="1h"),
)
CFG = {"verdict": {"min_edge_spreads": 2.0, "action": "mark"}}


def trades() -> pd.DataFrame:
    """Two identities, IS and OOS rows, longs and shorts, some held over a rollover."""
    rng, rows = np.random.default_rng(1), []
    for identity in ("a", "b"):
        for sample in ("IS", "OOS"):
            for _ in range(30):
                i = int(rng.integers(0, 350))
                rows.append(
                    {
                        "identity": identity,
                        "sample": sample,
                        "Open time": BARS.index[i],
                        "Close time": BARS.index[i + int(rng.integers(1, 40))],
                        "Type": rng.choice(["Buy", "Sell"]),
                        "Size": 0.5 + rng.random(),
                    }
                )
    return pd.DataFrame(rows)


def test_edge_equals_the_gates_edge_mean_oos(monkeypatch: pytest.MonkeyPatch) -> None:
    """Known answer: on the same oos1 trades, edgeCost's edge_mean is the gate's edge_mean_oos."""
    monkeypatch.setattr(costs, "warnings", lambda asset: [])
    t = trades()
    oos = t[t["sample"] == "OOS"]
    priced = costs.price(oos, BARS, COSTS)
    # the gate's own table, built the way level 1a builds it
    enter, leave = (BARS.index.get_indexer(oos[k]) for k in ("Open time", "Close time"))
    side = np.where(oos["Type"] == "Sell", -1.0, 1.0)
    pnl, cost = reprice.pnl(
        reprice.fills(BARS, enter),
        reprice.fills(BARS, leave),
        oos["Open time"].to_numpy(),
        oos["Close time"].to_numpy(),
        side,
        oos["Size"].to_numpy(),
        COSTS,
    )
    gate = onepass.edge_mean(
        pd.DataFrame({"identity": oos["identity"].to_numpy(), "pnl": pnl, "cost": cost})
    )
    names = pd.Series({"a": "Strategy a", "b": "Strategy b"})
    panel = many.run(priced, names, CFG, {})["panel"]
    for identity, name in names.items():
        assert panel.loc[name, "edge_mean"] == pytest.approx(gate[identity])
        assert one.measure(priced[priced["identity"] == identity])[
            "edge_mean"
        ] == pytest.approx(gate[identity])


def test_per_trade_reads_only_oos(monkeypatch: pytest.MonkeyPatch) -> None:
    """IS rows never reach the table, and the costs are the oos1 segment's."""
    seen = {}
    monkeypatch.setattr(costs, "read_bars", lambda feed, tf: BARS)
    monkeypatch.setattr(
        reprice, "costs", lambda feed, segment: seen.setdefault("s", segment) and COSTS
    )
    t = trades()
    assert len(costs.per_trade(t, "X_M1", "H1")) == (t["sample"] == "OOS").sum()
    assert seen["s"] == "oos1"


def test_off_grid_trade_is_refused() -> None:
    """A trade stamped between bars cannot be repriced from a bar open."""
    t = (
        trades()
        .head(3)
        .assign(**{"Open time": BARS.index[5] + pd.Timedelta(minutes=7)})
    )
    with pytest.raises(ValueError, match="strategies"):
        costs.price(t, BARS, COSTS)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
