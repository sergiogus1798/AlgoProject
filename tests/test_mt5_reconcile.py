#!/usr/bin/env python3
"""weeklyReconciler on known answers: the week's bounds, deals into trades, pairing, each gap, MAE from M1, an empty week."""

import json
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import openpyxl
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import fleetpaths
from core.study import blocks
from mt5.fleet import magics
from mt5.reconcile import (
    floating,
    judge,
    live,
    register,
    report,
    run,
    sqxside,
    week as weeks,
)

INST = {"tick_size": 0.01, "point_value": 100.0}
ZONES = ("EETUS", "EETUS")
WEEK = "2026-W38"  # Monday 2026-09-14 … Sunday 2026-09-20
CFG = yaml.safe_load(run.CONFIG.read_text(encoding="utf-8"))
CFG["pairing"]["entry_tolerance_bars"] = 1


def sqx_trades() -> pd.DataFrame:
    """Four H1 trades inside the week, both sides, 0.1 lots, and one the week before."""
    opens = pd.to_datetime(
        [
            "2026-09-10 09:00",
            "2026-09-14 06:00",
            "2026-09-15 12:00",
            "2026-09-16 22:00",
            "2026-09-18 03:00",
        ]
    )
    return pd.DataFrame(
        {
            "Ticket": [1, 2, 3, 4, 5],
            "Type": ["Buy", "Buy", "Sell", "Buy", "Sell"],
            "Open time": opens,
            "Open price": [150.0, 151.0, 152.0, 153.0, 154.0],
            "Size": 0.1,
            "Close time": opens + pd.Timedelta(hours=5),
            "Close price": [150.5, 151.4, 151.7, 152.8, 154.2],
            "Profit/Loss": [5.0, 4.0, 3.0, -2.0, -2.0],
        }
    )


def as_live(frame: pd.DataFrame, lots: float = 0.3) -> pd.DataFrame:
    """The same trades as the account would hold them: its own lot, P&L in proportion."""
    return frame.drop(columns="Ticket").assign(
        Size=lots, **{"Profit/Loss": frame["Profit/Loss"] * lots / frame["Size"]}
    )


def got(
    sqx: pd.DataFrame,
    lived: pd.DataFrame,
    bars: pd.DataFrame | None = None,
    zones: tuple[str, str] = ZONES,
) -> dict:
    """One strategy's reconciliation of WEEK at H1."""
    return judge.reconcile(sqx, lived, WEEK, "H1", INST, zones, bars, CFG)


def test_week_bounds() -> None:
    """ISO weeks on the server's clock: Monday 00:00 in, the next Monday 00:00 out."""
    assert weeks.bounds("2026-W38") == (
        pd.Timestamp("2026-09-14"),
        pd.Timestamp("2026-09-21"),
    )
    assert weeks.bounds("2026-W01")[0] == pd.Timestamp(
        "2025-12-29"
    )  # ISO, not calendar
    edge = pd.DataFrame(
        {
            "Open time": pd.to_datetime(
                [
                    "2026-09-13 23:59",
                    "2026-09-14 00:00",
                    "2026-09-20 23:59",
                    "2026-09-21 00:00",
                ]
            )
        }
    )
    assert list(weeks.cut(edge, WEEK)["Open time"].dt.day) == [14, 20]
    # A feed on UTC: Sunday 22:30 there is Monday 01:30 on the EETUS server — next week's trade
    late = (
        sqx_trades()
        .iloc[[1]]
        .assign(
            **{
                "Open time": pd.Timestamp("2026-09-20 22:30"),
                "Close time": pd.Timestamp("2026-09-21 03:30"),
            }
        )
    )
    assert (
        got(late, late.iloc[:0], zones=("UTC", "EETUS"))["summary"]["sqx_trades"] == 0
    )
    assert got(late, late.iloc[:0])["summary"]["sqx_trades"] == 1
    try:
        weeks.bounds("2026-38")
        raise AssertionError("a malformed week was accepted")
    except SystemExit as stop:
        assert "AAAA-Wss" in str(stop)


def test_identical_lists_pair_with_zero_gaps() -> None:
    """The account did exactly the backtest, at three times its lot: every gap is zero."""
    s = got(sqx_trades(), as_live(sqx_trades()))
    assert (
        s["summary"]["sqx_trades"],
        s["summary"]["live_trades"],
        s["summary"]["paired"],
    ) == (4, 4, 4)
    assert (
        s["summary"]["sqx_only"]
        == s["summary"]["live_only"]
        == s["summary"]["clock_h"]
        == 0
    )
    for column in (
        "entry_gap_min",
        "entry_gap_pts",
        "pnl_gap_pts",
        "pnl_gap_cur",
        "close_gap_min",
    ):
        assert s["pairs"][column].abs().max() < 1e-9, column
    assert abs(s["summary"]["pnl_cur_sqx_paired"] - 9.0) < 1e-9  # 3.0 booked at 0.1, ×3


def test_missing_live_trade_names_its_sqx_twin() -> None:
    """The EA skipped one entry: it is listed with the SQX ticket; an extra live one is listed too."""
    lived = as_live(sqx_trades()).drop(index=3)
    s = got(sqx_trades(), lived)
    assert s["summary"]["paired"] == 3 and list(s["sqx_only"]["Ticket"]) == [4]
    assert s["sqx_only"]["Open time"].iloc[0] == pd.Timestamp("2026-09-16 22:00")
    extra = pd.concat(
        [
            as_live(sqx_trades()),
            as_live(sqx_trades())
            .iloc[[2]]
            .assign(**{"Open time": pd.Timestamp("2026-09-17 15:00")}),
        ],
        ignore_index=True,
    )
    s = got(sqx_trades(), extra)
    assert s["summary"]["live_only"] == 1 and s["summary"]["sqx_only"] == 0
    assert s["live_only"]["Open time"].iloc[0] == pd.Timestamp("2026-09-17 15:00")
    assert "falta en real: ticket 4" in report.say(
        WEEK, {("ftmo", "S"): got(sqx_trades(), lived)}, lived.iloc[:0]
    )


def test_constant_clock_shift_is_recovered() -> None:
    """The server one hour ahead of the feed: read off the trades, not reported as a gap."""
    lived = judge.clocks.shifted(as_live(sqx_trades()), 1)
    s = got(sqx_trades(), lived)
    assert s["summary"]["clock_h"] == 1 and s["summary"]["paired"] == 4
    assert s["pairs"]["entry_gap_min"].abs().max() == 0


def test_planted_slip_is_exact() -> None:
    """A buy filled 3 points worse live: +3 points of price, +3 against, −3 of P&L, to the cent."""
    lived = as_live(sqx_trades())
    lived.loc[1, "Open price"] += 3 * INST["tick_size"]
    row = got(sqx_trades(), lived)["pairs"].iloc[0]
    assert (
        abs(row["entry_gap_pts"] - 3) < 1e-9 and abs(row["entry_slip_pts"] - 3) < 1e-9
    )
    assert abs(row["pnl_gap_pts"] + 3) < 1e-9
    lived = as_live(sqx_trades())
    lived.loc[2, "Open price"] += 3 * INST["tick_size"]  # a sell filled HIGHER: better
    row = got(sqx_trades(), lived)["pairs"].iloc[1]
    assert (
        abs(row["entry_gap_pts"] - 3) < 1e-9 and abs(row["entry_slip_pts"] + 3) < 1e-9
    )


def test_mae_from_m1_to_the_cent() -> None:
    """Hand-made minutes: entry minute to the minute before the exit, wicks against the fill."""
    minutes = pd.date_range("2026-09-14 06:00", periods=6, freq="1min")
    bars = pd.DataFrame(
        {
            "High": [151.02, 151.10, 151.05, 151.30, 151.00, 159.0],
            "Low": [150.98, 150.90, 150.73, 150.95, 150.80, 140.0],
        },
        index=minutes,
    )
    one = pd.DataFrame(
        {
            "Type": ["Buy", "Sell"],
            "Open time": [minutes[0], minutes[1]],
            "Open price": [151.0, 151.0],
            "Size": [0.3, 0.3],
            "Close time": [minutes[5], minutes[4]],
            "Close price": [151.2, 150.9],
            "Profit/Loss": [6.0, 3.0],
        }
    )
    out = floating.rebuild(one, bars, INST["point_value"])
    # buy: worst Low of minutes 0-4 is 150.73 → −0.27 × 0.3 × 100; best High 151.30 → +9.00
    assert abs(out["mae"][0] + 8.10) < 0.005 and abs(out["mfe"][0] - 9.00) < 0.005
    # sell, minutes 1-3: worst High 151.30 → −9.00; best Low 150.73 → +8.10; minute 5 never counts
    assert abs(out["mae"][1] + 9.00) < 0.005 and abs(out["mfe"][1] - 8.10) < 0.005
    assert floating.rebuild(one, None, 100.0)["mae"].isna().all()
    outside = one.assign(**{"Close time": minutes[5] + pd.Timedelta(hours=1)})
    assert (
        floating.rebuild(outside, bars, 100.0)["mae"].isna().all()
    )  # no bar says: no figure
    # Both sides are rebuilt on the same bars, so identical trades have identical MAE at the live lot
    sqx = one.iloc[[0]].assign(Ticket=1, Size=0.1)
    pairs = got(sqx, one.iloc[[0]], bars)["pairs"]
    assert (
        abs(pairs["mae_live"].iloc[0] + 8.10) < 0.005
        and abs(pairs["mae_gap"].iloc[0]) < 1e-9
    )


def test_empty_week_is_clean() -> None:
    """No trade on either side is «sin operaciones», and still a valid result.json."""
    none = sqx_trades().iloc[:0]
    piece = got(none, as_live(none))
    assert (
        piece["summary"]["paired"] == 0
        and piece["summary"]["entry_slip_pts_mean"] is None
    )
    pieces = {("ftmo", "Strategy 1.2.3"): piece}
    assert "sin operaciones" in report.say(
        WEEK, pieces, none
    ) and "Semana sin operaciones" in report.say(WEEK, pieces, none)
    with tempfile.TemporaryDirectory() as tmp:
        out = report.finish(Path(tmp), WEEK, CFG, time.time(), pieces, none)
        stored = json.loads((Path(tmp) / "result.json").read_text(encoding="utf-8"))
        full = {("ftmo", "S"): got(sqx_trades(), as_live(sqx_trades()))}
        blocks.validate(report.finish(Path(tmp), WEEK, CFG, time.time(), full, none))
        assert len(pd.read_parquet(Path(tmp) / "pairs.parquet")) == 4
    assert out["verdict"] is None and stored["summary"]["totals"]["live_trades"] == 0


def deal(
    ticket: int,
    position: int,
    when: str,
    kind: int,
    entry: int,
    volume: float,
    price: float,
    profit: float = 0.0,
    magic: int = 7,
    commission: float = -0.5,
) -> dict:
    """One row as `history_deals_get(...)._asdict()` gives it: time in seconds, server clock."""
    return {
        "ticket": ticket,
        "order": ticket,
        "time": int(pd.Timestamp(when).timestamp()),
        "type": kind,
        "entry": entry,
        "magic": magic,
        "position_id": position,
        "volume": volume,
        "price": price,
        "commission": commission,
        "swap": 0.0,
        "profit": profit,
        "fee": 0.0,
        "symbol": "USDJPY",
        "comment": "",
    }


def test_deals_become_trades_split_by_magic() -> None:
    """A position closed in two parts, one still open, a hand order and a deposit."""
    deals = [
        deal(1, 0, "2026-09-14 00:00", 2, 0, 0.0, 0.0, 10000.0, 0, 0.0),  # balance
        deal(2, 10, "2026-09-14 06:00", live.BUY, live.IN, 0.3, 151.0),
        deal(3, 10, "2026-09-14 09:00", live.SELL, live.OUT, 0.1, 151.3, 20.0, 0),
        deal(4, 10, "2026-09-14 11:00", live.SELL, live.OUT, 0.2, 151.6, 80.0, 0),
        deal(5, 11, "2026-09-15 12:00", live.SELL, live.IN, 0.3, 152.0),
        deal(6, 12, "2026-09-16 08:00", live.BUY, live.IN, 0.5, 150.0, magic=0),
        deal(7, 12, "2026-09-16 09:00", live.SELL, live.OUT, 0.5, 150.1, 30.0, 0),
    ]
    frame = live.trades(deals)
    assert len(frame) == 3 and list(frame["magic"]) == [7, 7, 0]
    first = frame.iloc[0]
    assert first["Type"] == "Buy" and first["Open time"] == pd.Timestamp(
        "2026-09-14 06:00"
    )
    assert first["Close time"] == pd.Timestamp("2026-09-14 11:00")
    assert (
        abs(first["Close price"] - 151.5) < 1e-9
        and abs(first["Profit/Loss"] - 98.5) < 1e-9
    )
    assert pd.isna(frame.iloc[1]["Close time"]) and frame.iloc[1]["Type"] == "Sell"
    assert live.trades([]).empty
    book = pd.DataFrame(
        {"magic": [7, 8], "strategy": ["A", "B"], "firm": ["ftmo", "ftmo"]}
    )
    split, strays = live.by_strategy(frame, "ftmo", book)
    assert len(split["A"]) == 2 and split["B"].empty and list(strays["magic"]) == [0]
    s = got(sqx_trades().iloc[:0], split["A"])["summary"]
    assert s["live_trades"] == 2 and s["live_open"] == 1 and s["live_only"] == 2


def test_owner_inputs_are_refused_in_spanish() -> None:
    """No magics.csv, an empty tolerance, an empty live account list: each stops with its reason."""
    raw = {"pairing": {"entry_tolerance_bars": None}, "live": {"accounts": None}}
    for key in ("pairing.entry_tolerance_bars", "live.accounts"):
        try:
            run.required(raw, key, "x")
            raise AssertionError(f"{key} has a default")
        except SystemExit as stop:
            assert "decisión del dueño" in str(stop)
    with (
        tempfile.TemporaryDirectory() as tmp,
        mock.patch.object(fleetpaths, "FLEET", Path(tmp)),
    ):
        try:
            register.read()
            raise AssertionError("an absent magics.csv was accepted")
        except SystemExit as stop:
            assert "falta el registro de magics" in str(stop)
        book = openpyxl.Workbook()
        book.active.title = "Cuentas"  # pyright: ignore[reportOptionalMemberAccess]  # a new workbook has an active sheet
        book["Cuentas"].append(["hoja", "firma"])
        book["Cuentas"].append(["FTMO_10k", "FTMO"])
        book.create_sheet("FTMO_10k").append(["symbol", "tf", "strategy", "magic"])
        book["FTMO_10k"].append(["EURUSD", "H1", "S1", None])
        book["FTMO_10k"].append(["GBPUSD", "H1", "S2", None])  # no magic saved
        book.save(fleetpaths.workbook())
        magics.add(1001, ("S1", "EURUSD", "H1"))
        magics.identify(1001, "aa", "s1.sqx")
        got = register.read()
        assert list(got["firm"]) == ["ftmo"] and list(got["magic"]) == [1001]
        assert len(magics.read()) == 1  # fill() assigned nothing for S2
        assert not register.live_in(got, pd.Timestamp("2000-01-01")).shape[0]


def test_sqx_window() -> None:
    """The retest's days: the warm-up before Monday, never past the day before SQX's last."""
    assert sqxside.window(WEEK, {"data": {"to": "2026-10-01"}}, 60) == (
        "2026-07-16",
        "2026-09-20",
    )
    assert sqxside.window(WEEK, {"data": {"to": "2026-09-19"}}, 60)[1] == "2026-09-18"
    try:
        sqxside.window(WEEK, {"data": {"to": "2026-09-14"}}, 60)
        raise AssertionError("a week SQX has no data for was accepted")
    except SystemExit as stop:
        assert "todavía no está" in str(stop)


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("ok")
