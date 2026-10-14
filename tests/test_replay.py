#!/usr/bin/env python3
"""engines.market.replay: the stop walk on bars built by hand, and the delay-0 replay against SQX's stop harvests."""

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import DATA  # noqa: E402
from engines.market.replay import inputs, reconcile, walk  # noqa: E402


def bars(n: int = 60) -> pd.DataFrame:
    """Flat bars at 100 with a 1-wide range: ATR(20) is 1 everywhere."""
    return pd.DataFrame(
        {"Open": 100.0, "High": 100.5, "Low": 99.5, "Close": 100.0},
        index=pd.date_range("2024-01-01", periods=n, freq="30min"),
    )


def one(
    b: pd.DataFrame, kind: str, leave: int, delay: int = 0, latency: bool = False
) -> walk.Walked:
    """A single long entered at bar 30 at the open, stop 2 ATR under the fill."""
    return walk.replay(b, trade(kind, leave), delay, latency)


def trade(kind: str, leave: int, close: float = 0.0) -> pd.DataFrame:
    """One long row as `inputs.ready` shapes it: entry bar 30, stop 2 ATR, slippage 0.1."""
    keys = (
        "enter",
        "leave",
        "Close type",
        "offset",
        "side",
        "coef",
        "tick",
        "cap",
        "Close price",
        "slippage",
    )
    row = (30, leave, kind, 0.0, 1.0, 2.0, 0.01, 10, close, 0.1)
    return pd.DataFrame({k: [v] for k, v in zip(keys, row, strict=True)})


def test_stop_hit_in_the_first_bar_that_reaches_it() -> None:
    """Known answer: level 98; bar 33's low 97.9 stops it there, at the level."""
    b = bars()
    b.iloc[33, b.columns.get_loc("Low")] = 97.9
    w = one(b, "Exit Signal", 40)
    assert (
        w["stopped"][0] and w["leave"][0] == 33 and np.isclose(w["exit_raw"][0], 98.0)
    )


def test_gap_through_fills_at_the_open() -> None:
    """A bar that opens under the level fills there, not at the level (SQX, 58 of 910 NIKKEI stops)."""
    b = bars()
    b.iloc[33, [b.columns.get_loc("Open"), b.columns.get_loc("Low")]] = [97.0, 96.5]
    w = one(b, "Exit Signal", 40)
    assert w["leave"][0] == 33 and np.isclose(w["exit_raw"][0], 97.0)


def test_level_reads_the_bar_before_the_entry() -> None:
    """No look-ahead: a huge range on the entry bar itself leaves the level alone; one bar earlier moves it."""
    b = bars()
    b.iloc[30, [b.columns.get_loc("High"), b.columns.get_loc("Low")]] = [110.0, 99.0]
    assert np.isclose(one(b, "Exit Signal", 40)["stop_level"][0], 98.0)
    b = bars()
    b.iloc[29, b.columns.get_loc("High")] = 110.0
    assert one(b, "Exit Signal", 40)["stop_level"][0] < 98.0


def test_delay_moves_what_it_should() -> None:
    """Exit After X Bars moves with the entry; a signal exit stays unless latency; a signal exit
    passed by the delayed entry drops the trade; an SQX stop that no longer fires is unknown."""
    b = bars()
    assert one(b, "Exit After X Bars", 35, delay=2)["leave"][0] == 37
    assert one(b, "Exit Signal", 35, delay=2)["leave"][0] == 35
    assert one(b, "Exit Signal", 35, delay=2, latency=True)["leave"][0] == 37
    assert one(b, "Exit Signal", 31, delay=2)["dropped"][0]
    w = one(b, "SL", 33, delay=1)
    assert w["unknown"][0] and w["leave"][0] == 42  # entry 31 + cap 10 + 1
    assert one(b, "Exit After X Bars", 59, delay=40)["dropped"][
        0
    ]  # entry past the last bar
    with pytest.raises(ValueError, match="no delay rule"):
        one(b, "Trailing Stop", 40)


def test_reconcile_counts_agreement() -> None:
    """A replay that equals SQX reads rate 1; flipping one exit bar reads (n-1)/n."""
    b = bars()
    b.iloc[33, b.columns.get_loc("Low")] = 97.9
    w = one(b, "SL", 33)
    m = reconcile.reconcile(w, trade("SL", 33, 98.0 - 0.1), 1e-6)
    assert m["rate"] == 1.0 and m["stops_within"] == 1.0
    m = reconcile.reconcile(w, trade("SL", 34, 97.9), 1e-6)
    assert m["rate"] == 0.0


HARVESTS = sorted(glob.glob(str(DATA / "harvest" / "*" / "Stop_p90" / "*")))


@pytest.mark.skipif(not HARVESTS, reason="no Stop_p90 harvest in AlgoData")
@pytest.mark.parametrize("folder", HARVESTS[-3:])
def test_delay_zero_reproduces_sqx(folder: str) -> None:
    """Acceptance (§3.2), skipped (not passed) without a Stop_p90 harvest on disk: at delay 0 at least 99 % of the trades leave in SQX's bar for SQX's reason, 98 % of the stops within 2 ticks."""
    r = inputs.ready(Path(folder))
    t = r["trades"]
    w = walk.replay(r["bars"], t, 0, False)
    m = reconcile.reconcile(w, t, 2 * float(t["tick"].max()))
    assert m["rate"] >= 0.99, m["rate"]
    assert m["stops_within"] >= 0.98, m["stops_within"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
