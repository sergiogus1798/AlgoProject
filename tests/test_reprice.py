#!/usr/bin/env python3
"""The common repricer against SQX's own P/L on audited trades, and against cases worked out by hand."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import load
from engines.market import reprice

# 267 of the 1,312 audited Buy trades of Trade_NIKKEI225_M30_volatilidadL (A 4.9.301, B 16.11.437,
# C 14.3.479): every 6th, every one opening or closing in the 23:00 hour, every one over a
# weekend; `open_bar` / `close_bar` are the raw M30 opens. scratch/encargo44/fixture_reprice.py.
AUDITED = Path(__file__).parent / "fixtures" / "reprice_audited.csv"
# The costs those tasks ran with, frozen here: the card is recalibrated, the trades are not.
NIKKEI = {"point_value": 0.063137, "tick_size": 0.01, "commission_method": "PercentageBased",
          "commission": 0.0, "swap_long": -4.78, "swap_short": -1.87, "triple": 4, "rollover": 23}
POINTS = {"build": (304.11, 106.44), "oos1": (474.91, 166.22)}      # spread, slippage

# Hand cases: 6 USD per 1.0 of price (point value 2 x 3 lots), 0.09 of price a round trip.
HAND = {"point_value": 2.0, "tick_size": 0.01, "spread": 0.05, "slippage": 0.02,
        "commission_method": "PercentageBased", "commission": 0.0, "swap_long": -3.6,
        "swap_short": -1.8, "triple": 4, "rollover": 23}
DAY = (np.datetime64("2024-01-08T10:00"), np.datetime64("2024-01-08T15:00"))      # a Monday


def test_audited_trades_reproduce_sqx() -> None:
    """A, B and C on build and oos1, unmoved: per trade within 0.02 USD + 2 ticks x PV x size."""
    t = pd.read_csv(AUDITED, parse_dates=["open_time", "close_time"])
    for (name, segment), g in t.groupby(["strategy", "segment"]):
        spread, slippage = POINTS[segment]
        c = {**NIKKEI, "spread": spread * 0.01, "slippage": slippage * 0.01}
        got, cost = reprice.pnl(g["open_bar"], g["close_bar"], g["open_time"], g["close_time"],
                                1, g["size"], c)
        tolerance = 0.02 + 2 * c["tick_size"] * c["point_value"] * g["size"]
        over = np.abs(got - g["sqx_pnl"]) - tolerance
        assert (over <= 0).all(), f"{name} {segment}: worst trade {over.max():+.4f} USD over"
        gross = c["point_value"] * g["size"] * (g["close_bar"] - g["open_bar"])
        assert (np.abs(got + cost - gross) <= tolerance).all(), f"{name} {segment}: pnl + cost is not the gross"
        assert (cost > 0).all(), f"{name} {segment}: a trade was charged nothing"


def test_flat_price_loses_exactly_its_cost() -> None:
    """Same open in and out, no night, costs on the tick: 6 x (0.05 + 2 x 0.02) = 0.54 both ways."""
    got, cost = reprice.pnl(100.0, 100.0, *DAY, 1, 3.0, HAND)
    assert got == -0.54 and cost == 0.54, (got, cost)


def test_long_and_short_are_symmetric() -> None:
    """The same 10.00 move costs both sides the same 0.54: +59.46 long (100.07 -> 109.98),
    -60.54 short (99.93 -> 110.02, the spread on the entry)."""
    got, cost = reprice.pnl(100.0, 110.0, *DAY, np.array([1, -1]), 3.0, HAND)
    assert np.allclose(got, [59.46, -60.54], atol=1e-9), got
    assert np.allclose(cost, 0.54, atol=1e-9), cost
    assert reprice.pnl(100.0, 100.0, *DAY, -1, 3.0, HAND)[0] == -0.54


def test_nights() -> None:
    """Rollover 23:00 Monday to Friday, Friday three; open <= T < close."""
    d = lambda s: np.datetime64(f"2024-01-{s}")
    cases = [("08T10:00", "08T15:00", 0),      # Monday, never reaches 23:00
             ("08T22:30", "09T00:00", 1),      # Monday night
             ("05T22:30", "05T23:30", 3),      # Friday night
             ("05T23:00", "05T23:30", 3),      # opened ON the rollover: charged
             ("05T22:30", "05T23:00", 0),      # closed ON the rollover: not charged
             ("06T10:00", "07T23:30", 0),      # Saturday and Sunday
             ("04T12:00", "09T12:00", 5)]      # Thursday 1, Friday 3, Monday 1
    got = reprice.nights(np.array([d(a) for a, _, _ in cases]), np.array([d(b) for _, b, _ in cases]), HAND)
    assert got.tolist() == [n for _, _, n in cases], got


def test_triple_swap_night() -> None:
    """Flat over a Friday 23:00: 3 nights x 6 x fill x 3.6 % / 360 on top of the 0.54."""
    fri = (np.datetime64("2024-01-05T22:30"), np.datetime64("2024-01-05T23:30"))
    long, _ = reprice.pnl(100.0, 100.0, *fri, 1, 3.0, HAND)        # fill 100.07 -> swap 0.180126
    short, _ = reprice.pnl(100.0, 100.0, *fri, -1, 3.0, HAND)      # fill 99.93, 1.8 % -> 0.089937
    assert (long, short) == (-0.72, -0.63), (long, short)


def test_swap_in_points_and_a_credit() -> None:
    """Forex: a night is 6 x tick_step x points. Long -50 pays 0.30, short +20 is paid 0.12."""
    c = {**HAND, "tick_step": 0.001, "swap_long": -50.0, "swap_short": 20.0}
    mon = (np.datetime64("2024-01-08T22:30"), np.datetime64("2024-01-09T00:00"))
    got, cost = reprice.pnl(100.0, 100.0, *mon, np.array([1, -1]), 3.0, c)
    assert np.allclose(got, [-0.84, -0.42], atol=1e-9) and np.allclose(cost, [0.84, 0.42], atol=1e-9), (got, cost)


def test_cost_off_the_tick_rounds_the_fill() -> None:
    """Tick 0.25, spread 0.30, slippage 0.05: in at 100.35 -> 100.25, out at 99.95 -> 100.00."""
    c = {**HAND, "tick_size": 0.25, "spread": 0.30, "slippage": 0.05}
    got, cost = reprice.pnl(100.0, 100.0, *DAY, 1, 3.0, c)
    assert got == -1.5 and np.isclose(cost, 2.4), (got, cost)      # paid 6 x 0.25, declared 6 x 0.40


def test_commission_once_on_the_open() -> None:
    """0.01 % of the entry notional (6 x 100.07), or 8 USD per lot: on top of the 0.54."""
    pct, _ = reprice.pnl(100.0, 100.0, *DAY, 1, 3.0, {**HAND, "commission": 0.01})
    lot, _ = reprice.pnl(100.0, 100.0, *DAY, 1, 3.0,
                         {**HAND, "commission_method": "SizeBased", "commission": 8.0})
    assert (pct, lot) == (-0.60, -24.54), (pct, lot)


def test_any_shape_and_fills() -> None:
    """A (draws, trades) block prices like its rows; fills() is the bar open at a position."""
    bars = pd.DataFrame({"Open": [100.0, 101.0, 103.0, 99.0]},
                        index=pd.date_range("2024-01-08 10:00", periods=4, freq="30min"))
    entry, leave = np.array([[0, 1], [2, 0]]), np.array([[1, 3], [3, 2]])
    px = reprice.fills(bars, entry)
    assert px.tolist() == [[100.0, 101.0], [103.0, 100.0]]
    got, cost = reprice.pnl(px, reprice.fills(bars, leave), bars.index.to_numpy()[entry],
                            bars.index.to_numpy()[leave], 1, 3.0, HAND)
    assert got.shape == cost.shape == (2, 2)
    assert np.allclose(got, [[5.46, -12.54], [-24.54, 17.46]], atol=1e-9), got


def test_costs_come_from_the_card() -> None:
    """One path: the card's points times its tick, its own triple night and rollover hour."""
    card, c = load("NIKKEI225"), reprice.costs("NIKKEI225_M1", "oos1")
    assert c["tick_size"] == 0.01 and (c["triple"], c["rollover"]) == (4, 23)
    assert c["point_value"] == card["instrument"]["point_value"]
    assert np.isclose(c["spread"], card["costs"]["spread_oos"]["use"] * 0.01)
    assert np.isclose(c["slippage"], card["costs"]["slippage_oos"]["use"] * 0.01)
    assert c["swap_long"] == card["costs"]["swap_long"]["use"] < 0
    assert set(c) == set(reprice.Costs.__annotations__) and c["tick_step"] is None
    fx, yen = reprice.costs("EURUSD_M1", "oos1"), load("USDJPY")
    assert np.isclose(fx["tick_step"], 0.00001) and (fx["triple"], fx["rollover"]) == (2, 23)
    assert reprice.costs("USDJPY_M1", "oos1")["swap_short"] == yen["costs"]["swap_short"]["use"]

# Hourly bars of that Monday from 10:00. The M1 feed has no minute before 12:07 in the 12:00 bar.
BARS = pd.DataFrame({"Open": [100.0, 101.0, 103.0, 99.0], "Low": [99.5, 100.5, 101.5, 98.0],
                     "High": [101.5, 102.5, 103.5, 99.5]},
                    index=pd.date_range("2024-01-08 10:00", periods=4, freq="1h"))
MINUTES = pd.DataFrame({"Open": 0.0}, index=pd.DatetimeIndex(
    ["2024-01-08 10:00", "2024-01-08 11:00", "2024-01-08 12:07", "2024-01-08 12:08", "2024-01-08 13:00"]))


def harvested(side: str, close: str, kind: str, price: float) -> pd.DataFrame:
    """One 3-lot trade in at 10:00, as a harvest carries it."""
    return pd.DataFrame({"identity": "s", "Type": side, "Open time": BARS.index[:1], "Size": 3.0,
                         "Close time": pd.Timestamp(f"2024-01-08 {close}"), "Close type": kind,
                         "Close price": price})


def test_a_stop_fills_at_sqx_price_and_a_late_stamp_at_its_bar() -> None:
    """By hand. Long in at 100.07; stopped at 102.00 in the 12:00 bar SQX books 101.98:
    6 x 1.91 = 11.46, not the 17.46 of that bar's open. Short in at 99.93, stopped at 102.00 in
    the 11:00 bar, booked 102.02: -12.54. Both are charged 6 x 0.09. A bar exit stamped at
    12:07, the bar's first minute, is the 12:00 bar's open: 6 x (102.98 - 100.07) = 17.46."""
    source, reprice.source = reprice.source, lambda feed, columns: MINUTES
    try:
        for side, close, kind, price, bar, stop, pnl in (
                ("Buy", "12:00", "SL", 101.98, 2, 102.0, 11.46),
                ("Sell", "11:00", "SL", 102.02, 1, 102.0, -12.54),
                ("Buy", "12:07", "Exit After X Bars", 102.98, 2, np.nan, 17.46)):
            got = reprice.real(harvested(side, close, kind, price), BARS, HAND, "X_M1").iloc[0]
            assert (got["enter"], got["leave"]) == (0, bar) and np.isclose(got["pnl"], pnl), got
            assert np.isclose(got["cost"], 0.54) and np.isclose(got["stop"], stop, equal_nan=True)
        stamps = pd.to_datetime(["2024-01-08 12:00", "2024-01-08 12:07", "2024-01-08 12:08",
                                 "2024-01-08 09:59"]).to_numpy()
        assert reprice.located(BARS, stamps, "X_M1").tolist() == [2, 2, -1, -1]
        assert reprice.located(BARS, stamps, None).tolist() == [2, -1, -1, -1]
        for close, kind, price in (("12:08", "Exit After X Bars", 102.98),   # not the first minute
                                   ("12:00", "SL", 101.30),      # below the bar: 101.5 - 0.07
                                   ("12:00", "Trailing", 102.0)):               # never measured
            try:
                reprice.real(harvested("Buy", close, kind, price), BARS, HAND, "X_M1")
            except ValueError as refused:
                assert "['s']" in str(refused)
            else:
                raise AssertionError((close, kind, price))
    finally:
        reprice.source = source
    drawn = harvested("Buy", "12:00", "SL", 101.98).drop(columns=["Close type", "Close price"])
    assert reprice.real(drawn, BARS, HAND).iloc[0]["pnl"] == 17.46      # no Close type: bar opens


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_reprice: ok")
