"""rounding.measure picks the rounding the trades were filled with."""

import numpy as np
import pandas as pd
import pytest

from engines.market import rounding


def _run(monkeypatch: pytest.MonkeyPatch, grid: bool) -> dict:
    """measure() on synthetic trades filled on the tick grid or unrounded."""
    index = pd.date_range("2024-01-02", periods=400, freq="h")
    rng = np.random.default_rng(1)
    px = 100 + rng.normal(0, 0.3, len(index)).cumsum()
    bars = pd.DataFrame(
        {"Open": px, "High": px + 5, "Low": px - 5, "Close": px}, index=index
    )
    cost = {
        "point_value": 1.0,
        "tick_size": 0.25,
        "spread": 0.1,
        "slippage": 0.0,
        "commission_method": "SizeBased",
        "commission": 0.0,
        "swap_long": 0.0,
        "swap_short": 0.0,
        "triple": 2,
        "rollover": 0,
        "tick_step": None,
    }
    monkeypatch.setattr(rounding.barstore, "read", lambda feed, tf: bars)
    monkeypatch.setattr(rounding.assetdata, "load", lambda s: {"sqx_symbol": "X_M1"})
    monkeypatch.setattr(
        rounding.reprice, "costs", lambda f, s, rounds: cost | {"rounds": rounds}
    )
    monkeypatch.setattr(rounding.thresholds, "value", lambda k: 0.01)
    n = 20
    trades = pd.DataFrame(
        {
            "strategy": "S",
            "Type": "Buy",
            "Sample type": "OOS1",
            "Close type": "Exit After X Bars",
            "Open time": index[: n * 10 : 10],
            "Close time": index[5 : n * 10 : 10],
            "Size": 1.0,
        }
    )
    enter = bars.loc[trades["Open time"], "Open"].to_numpy() + 0.1
    leave = bars.loc[trades["Close time"], "Open"].to_numpy()
    rd = (lambda x: np.round(x / 0.25) * 0.25) if grid else (lambda x: x)
    trades["Close price"] = leave
    trades["Profit/Loss"] = rd(leave) - rd(enter)
    return rounding.measure("X", trades, "build")


def test_tick_grid_fills_choose_tick(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fills on the 0.25 grid reprice exactly only when rounded."""
    assert _run(monkeypatch, True)["use"] == "tick"


def test_unrounded_fills_choose_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unrounded fills reprice exactly only when not rounded."""
    assert _run(monkeypatch, False)["use"] == "none"
