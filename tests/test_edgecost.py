#!/usr/bin/env python3
"""edgeCost's gross reconstruction, reconciliation and edge maths on trades built by hand."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.edgeCost import costs, inputs, many, one  # noqa: E402

TICK, POINT_VALUE, SPREAD = 0.1, 10.0, 2.0   # spread in points

FOREX = {"symbol": "TESTX", "class": "forex", "instrument": {"tick_size": TICK,
         "point_value": POINT_VALUE},
        "costs": {"spread": {"use": SPREAD, "why": "test"},
                  "commission": {"use": 0.0, "why": "test"},
                  "slippage_is": {"use": 0.0, "why": "test"},
                  "slippage_oos": {"use": 0.0, "why": "test"},
                  "swap_long": {"use": 0.0, "why": "test"},
                  "swap_short": {"use": 0.0, "why": "test"}}}


def trades_by_hand() -> pd.DataFrame:
    """Three trades whose gross, cost and edge are known by construction. Size never constant."""
    rows = [{"Open price": 100.0, "Close price": 101.0, "Size": 3.0},   # +30, cost 3, gross 33
            {"Open price": 50.0, "Close price": 49.0, "Size": 1.0},     # -10, cost 1, gross -9
            {"Open price": 200.0, "Close price": 202.0, "Size": 5.0}]   # +100, cost 5, gross 105
    direction = 1
    df = pd.DataFrame(rows)
    df["Type"] = "Buy"
    df["Open time"] = pd.to_datetime(["2020-01-06 10:00", "2020-01-07 15:00", "2020-01-08 20:00"])
    df["Close time"] = df["Open time"]
    df["sample"] = "IS"
    df["identity"] = "strat-a"
    df["Profit/Loss"] = (df["Close price"] - df["Open price"]) * direction * df["Size"] * POINT_VALUE
    return df


def main() -> None:
    """Gross, reconciliation and edge against the numbers worked out on paper above."""
    assert len({3.0, 1.0, 5.0}) == 3, "the fixture must vary Size, never hold it constant"
    priced = costs.per_trade(trades_by_hand(), FOREX)

    # Spread cost = 0.5 * spread_points * tick * point_value * Size (the half-spread
    # convention measured in knowhow/export/fill-and-pricing.md).
    expected_cost = [3.0, 1.0, 5.0]
    assert priced["spread_cost"].round(6).tolist() == expected_cost, priced["spread_cost"].tolist()
    assert priced["commission_cost"].eq(0.0).all()

    expected_gross = [33.0, -9.0, 105.0]
    assert priced["gross"].round(6).tolist() == expected_gross, priced["gross"].tolist()

    recon = costs.reconcile(priced)
    assert abs(recon["corr"] - 1.0) < 1e-9, f"exact-by-construction trades must reconcile: {recon}"
    assert abs(recon["resid_mean"]) < 1e-9

    got = one.measure(priced)
    assert abs(got["mean_gross"] - 43.0) < 1e-9, got["mean_gross"]        # (33-9+105)/3
    assert abs(got["median_gross"] - 33.0) < 1e-9, got["median_gross"]
    assert abs(got["mean_cost"] - 3.0) < 1e-9, got["mean_cost"]           # (3+1+5)/3
    assert abs(got["edge_mean"] - 43.0 / 3.0) < 1e-9, got["edge_mean"]
    assert abs(got["edge_median"] - 11.0) < 1e-9, got["edge_median"]      # 33/3
    assert got["breakeven_multiple"] == got["edge_mean"]

    # The verdict: no owner threshold in this test crosses the fixture's edge, so it must pass.
    cfg = {"verdict": {"min_edge_spreads": 2.0, "action": "mark"}}
    result = one.run("strat-a", priced, recon, cfg, FOREX, identity="strat-a")
    assert result["verdict"]["state"] == "pass", result["verdict"]
    assert result["summary"]["costs_provisional"] is False, "forex with no PROVISIONAL why"

    # A no_forex asset always carries the issue-26 warning, unresolved by this module.
    no_forex = {**FOREX, "class": "no_forex",
               "costs": {**FOREX["costs"], "spread_is": FOREX["costs"]["spread"],
                        "spread_oos": FOREX["costs"]["spread"]}}
    del no_forex["costs"]["spread"]
    warn_codes = {w["code"] for w in costs.warnings(no_forex)}
    assert "issue26" in warn_codes, warn_codes

    # A PROVISIONAL cost stamps the result, forex or not.
    stood_in = {**FOREX, "costs": {**FOREX["costs"],
               "spread": {"use": SPREAD, "why": "PROVISIONAL, not agreed with the broker"}}}
    assert {"provisional"} <= {w["code"] for w in costs.warnings(stood_in)}

    # many.run() must find the same strategy and the same numbers through the population path.
    names = pd.Series({"strat-a": "Strategy 1.1.1"})
    panel = many.run(priced, names, cfg, FOREX)["panel"]
    row = panel.loc["Strategy 1.1.1"]
    assert abs(row["edge_mean"] - got["edge_mean"]) < 1e-9
    assert row["verdict"] == "MANTENER"

    # action=drop below the bar must ask curate to discard it.
    cfg_drop = {"verdict": {"min_edge_spreads": 100.0, "action": "drop"}}
    panel_drop = many.run(priced, names, cfg_drop, FOREX)["panel"]
    assert panel_drop.loc["Strategy 1.1.1", "verdict"] == "DESCARTAR"

    print("ok")


if __name__ == "__main__":
    main()
