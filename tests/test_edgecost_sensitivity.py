#!/usr/bin/env python3
"""edgeCost's modelled swap and cost sensitivity, on trades whose answers are worked by hand."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.edgeCost import sensitivity, swap  # noqa: E402

CARD = {"class": "forex", "instrument": {"tick_size": 0.01, "point_value": 100.0},
        "swap": {"triple_swap_on": "WEDNESDAY", "rollout_hour": "23:00"},
        "costs": {"swap_long": {"use": 10.0}, "swap_short": {"use": -20.0}}}


def hand_trades() -> pd.DataFrame:
    """A: Mon->Tue 1 night. B: Tue->Thu crosses Tue and the triple Wed = 4. C: Wed 22:00-23:30 = 3."""
    t = pd.to_datetime
    return pd.DataFrame({
        "Open time": t(["2020-01-06 10:00", "2020-01-07 10:00", "2020-01-08 22:00"]),
        "Close time": t(["2020-01-07 10:00", "2020-01-09 10:00", "2020-01-08 23:30"]),
        "Size": [2.0, 1.0, 1.0], "Open price": [100.0] * 3, "direction": [1, -1, 1]})


def test_swap_nights_and_money() -> None:
    """tickStep = 0.001: one long night of size 1 = 100 * 0.001 * 10 = 1.0 credit."""
    tr = hand_trades()
    assert swap.charged_nights(tr["Open time"], tr["Close time"], CARD["swap"]).tolist() == [1, 4, 3]
    assert swap.swap_cost(tr, CARD).round(9).tolist() == [-2.0, 8.0, -3.0]
    weekend = pd.DataFrame({"Open time": pd.to_datetime(["2020-01-10 10:00"]),
                            "Close time": pd.to_datetime(["2020-01-13 10:00"])})
    assert swap.charged_nights(weekend["Open time"], weekend["Close time"], CARD["swap"]).tolist() == [3]
    never = {**CARD["swap"], "triple_swap_on": "NEVER"}
    assert swap.charged_nights(tr["Open time"], tr["Close time"], never).tolist() == [1, 2, 1]
    pct = {"class": "no_forex", "instrument": {"tick_size": 0.01, "point_value": 10.0}}
    one = swap.night_money(pct, 1.0, 2000.0, pd.Series([1]), 3.6, -3.6)
    assert abs(float(one[0]) - 2.0) < 1e-12, "percent swap is ANNUAL: size*pv*price*pct/100/360"


def test_breakeven_and_sensitivity() -> None:
    """Mean gross 20; mean costs commission 1, spread 2, slippage 1, swap 1 (total 5)."""
    p = pd.DataFrame({"gross_price": [10.0, 20.0, 30.0], "commission_cost": 1.0,
                      "spread_today": 2.0, "slippage_cost": 1.0, "swap_cost": [-2.0, 8.0, -3.0]})
    assert abs(sensitivity.breakeven(p) - 4.0) < 1e-12
    assert abs(sensitivity.breakeven(p, "swap") - 16.0) < 1e-12
    assert abs(sensitivity.breakeven(p, "spread") - 8.5) < 1e-12
    assert abs(sensitivity.breakeven(p, "commission") - 16.0) < 1e-12
    assert sensitivity.bites_first(p) == "spread"
    assert abs(sensitivity.net(p, 4.0).mean()) < 1e-12, "the edge is 0 at the breakeven multiple"
    assert abs(sensitivity.net(p, 0).mean() - 20.0) < 1e-12
    assert abs(sensitivity.profit_factor(sensitivity.net(p, 3.0)) - 31 / 16) < 1e-12
    table = sensitivity.sensitivity(p)
    assert len(table) == 5 * len(sensitivity.MULTIPLES)
    free = p.assign(swap_cost=-1.0)   # a credit never bites
    assert sensitivity.breakeven(free, "swap") != sensitivity.breakeven(free, "swap")


if __name__ == "__main__":
    test_swap_nights_and_money()
    test_breakeven_and_sensitivity()
    print("ok")
