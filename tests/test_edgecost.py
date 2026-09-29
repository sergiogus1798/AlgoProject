#!/usr/bin/env python3
"""edgeCost's gross reconstruction, reconciliation and edge maths on trades built by hand.

Review BLOCKER (2026-09-26): a single `SPREAD_SHARE = 0.5` was wrong even for feeds it was
never checked against. `spread_share.measure()` replaces it, and is tested here against
synthetic bars built so the answer is known — never against real `AlgoData/bars/*` files,
which are machine-specific data and may not exist on another machine (CODESTYLE rule 6).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.edgeCost import costs, many, one, spread_share  # noqa: E402

TICK, POINT_VALUE, SPREAD = 0.1, 10.0, 2.0   # declared spread, in points, "today"
FEED, TIMEFRAME = "TESTFEED_M1_test", "H1"

# commission.use, owner 2026-09-29: one {method, value} per segment, never a flat figure.
ZERO_COMMISSION = {"build": {"method": "SizeBased", "value": 0.0},
                   "oos1": {"method": "SizeBased", "value": 0.0},
                   "oos2": {"method": "SizeBased", "value": 0.0}}
FOREX = {"symbol": "TESTX", "class": "forex", "instrument": {"tick_size": TICK,
         "point_value": POINT_VALUE},
        "costs": {"spread": {"use": SPREAD, "why": "test"},
                  "commission": {"use": ZERO_COMMISSION, "why": "test"},
                  "slippage_is": {"use": 0.0, "why": "test"},
                  "slippage_oos": {"use": 0.0, "why": "test"},
                  "swap_long": {"use": 0.0, "why": "test"},
                  "swap_short": {"use": 0.0, "why": "test"}}}

MEASURED_OFFSET = 0.1   # the price-unit spread this test pretends to measure off the bars


def trades_by_hand() -> pd.DataFrame:
    """Three trades whose gross, cost and edge are known by construction. Size never constant."""
    rows = [{"Open price": 100.0, "Close price": 101.0, "Size": 3.0},
            {"Open price": 50.0, "Close price": 49.0, "Size": 1.0},
            {"Open price": 200.0, "Close price": 202.0, "Size": 5.0}]
    direction = 1
    df = pd.DataFrame(rows)
    df["Type"] = "Buy"
    df["Open time"] = pd.to_datetime(["2020-01-06 10:00", "2020-01-07 15:00", "2020-01-08 20:00"])
    df["Close time"] = df["Open time"]
    df["sample"] = "IS"
    df["identity"] = "strat-a"
    df["Profit/Loss"] = (df["Close price"] - df["Open price"]) * direction * df["Size"] * POINT_VALUE
    return df


def stub_measure() -> None:
    """Replace spread_share.measure with a fixed, known answer — no real bar file needed."""
    spread_share.measure = lambda trades, feed, timeframe: {"IS": MEASURED_OFFSET, "OOS": MEASURED_OFFSET}


def main() -> None:
    """Gross, reconciliation and edge against the numbers worked out on paper above."""
    assert len({3.0, 1.0, 5.0}) == 3, "the fixture must vary Size, never hold it constant"
    real_measure = spread_share.measure
    stub_measure()
    try:
        priced = costs.per_trade(trades_by_hand(), FOREX, FEED, TIMEFRAME)
    finally:
        spread_share.measure = real_measure

    # spread_cost = MEASURED_OFFSET (price units) * point_value * Size — the ACTUAL cost,
    # never a fraction of the declared spread.
    expected_spread_cost = [MEASURED_OFFSET * POINT_VALUE * s for s in (3.0, 1.0, 5.0)]
    assert priced["spread_cost"].round(6).tolist() == expected_spread_cost, priced["spread_cost"].tolist()
    assert priced["commission_cost"].eq(0.0).all()

    expected_gross = [33.0, -9.0, 105.0]   # P/L + 0 commission + spread_cost above
    assert priced["gross"].round(6).tolist() == expected_gross, priced["gross"].tolist()

    # cost_today uses the DECLARED spread (2.0 points), never the measured one: it is "what
    # this would cost today", the encargo's own definition of the edge's unit.
    expected_cost_today = [SPREAD * TICK * POINT_VALUE * s for s in (3.0, 1.0, 5.0)]
    assert priced["cost_today"].round(6).tolist() == expected_cost_today, priced["cost_today"].tolist()

    recon = costs.reconcile(priced)
    assert abs(recon["corr"] - 1.0) < 1e-9, f"exact-by-construction trades must reconcile: {recon}"
    assert abs(recon["resid_mean"]) < 1e-9

    got = one.measure(priced)
    mean_cost_today = sum(expected_cost_today) / 3
    assert abs(got["mean_gross"] - 43.0) < 1e-9, got["mean_gross"]
    assert abs(got["median_gross"] - 33.0) < 1e-9, got["median_gross"]
    assert abs(got["mean_cost"] - mean_cost_today) < 1e-9, got["mean_cost"]
    assert abs(got["edge_mean"] - 43.0 / mean_cost_today) < 1e-9, got["edge_mean"]
    assert abs(got["edge_median"] - 33.0 / mean_cost_today) < 1e-9, got["edge_median"]
    assert got["breakeven_multiple"] == got["edge_mean"]

    # The verdict: no owner threshold in this test crosses the fixture's edge, so it must pass.
    cfg = {"verdict": {"min_edge_spreads": 2.0, "action": "mark"}}
    result = one.run("strat-a", priced, recon, cfg, FOREX, identity="strat-a")
    assert result["verdict"]["state"] == "pass", result["verdict"]
    assert result["tabs"][0]["name"] == "reconcile", "reconciliation must render before the headline"
    assert result["tabs"][1]["name"] == "headline"
    assert "Reconciliación" in result["verdict"]["meaning"], "the verdict text must lead with it"
    assert result["summary"]["costs_provisional"] is False, "forex with no PROVISIONAL why"

    # A no_forex asset carries no commission warning: issue 26 settled once per trade (2026-09-27).
    no_forex = {**FOREX, "class": "no_forex",
               "segments": {"build": {"spread": "is"}, "oos1": {"spread": "oos"}},
               "costs": {**FOREX["costs"], "spread_is": FOREX["costs"]["spread"],
                        "spread_oos": FOREX["costs"]["spread"]}}
    del no_forex["costs"]["spread"]
    warn_codes = {w["code"] for w in costs.warnings(no_forex)}
    assert "issue26" not in warn_codes, warn_codes

    # A PROVISIONAL cost stamps the result, forex or not.
    stood_in = {**FOREX, "costs": {**FOREX["costs"],
               "spread": {"use": SPREAD, "why": "PROVISIONAL, not agreed with the broker"}}}
    assert {"provisional"} <= {w["code"] for w in costs.warnings(stood_in)}

    # many.run() must find the same strategy and the same numbers through the population path.
    stub_measure()
    try:
        names = pd.Series({"strat-a": "Strategy 1.1.1"})
        panel = many.run(priced, names, cfg, FOREX)["panel"]
    finally:
        spread_share.measure = real_measure
    row = panel.loc["Strategy 1.1.1"]
    assert abs(row["edge_mean"] - got["edge_mean"]) < 1e-9
    assert row["verdict"] == "MANTENER"

    # action=drop below the bar must ask curate to discard it.
    cfg_drop = {"verdict": {"min_edge_spreads": 100.0, "action": "drop"}}
    panel_drop = many.run(priced, names, cfg_drop, FOREX)["panel"]
    assert panel_drop.loc["Strategy 1.1.1", "verdict"] == "DESCARTAR"

    # A feed with no bar library entry must refuse outright, never fall back to a guess.
    try:
        spread_share.measure(trades_by_hand(), "NO_SUCH_FEED_ANYWHERE", "H1")
        raise AssertionError("an unmeasured feed must raise, not silently price at some default")
    except SystemExit:
        pass

    # A sample with too few trades to trust a median must also refuse, on a feed whose bars
    # DO exist — the count check, not the missing-file check, must be what fires here.
    real_bar_source, real_read_bars = spread_share.bar_source, spread_share.read_bars
    bars = pd.DataFrame({"Open": [100.0] * 200}, index=pd.date_range("2020-01-01", periods=200,
                                                                     freq="1h"))
    spread_share.bar_source = lambda feed: Path(__file__)   # any file that exists
    spread_share.read_bars = lambda feed, timeframe: bars
    try:
        few = trades_by_hand().iloc[:2]   # 2 < MIN_TRADES
        spread_share.measure(few, FEED, TIMEFRAME)
        raise AssertionError("fewer than MIN_TRADES trades must refuse, not average anyway")
    except SystemExit:
        pass
    finally:
        spread_share.bar_source, spread_share.read_bars = real_bar_source, real_read_bars

    print("ok")


if __name__ == "__main__":
    main()
