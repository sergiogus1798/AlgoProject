#!/usr/bin/env python3
"""MetaTracker's stop risk, weekend and news rules at their edges, the hours[] floors, the reasons' order, and the fixture's three lights."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import fleetpaths
from mt5.fleet.app import floors, read, risk, rules, state
from mt5.newsfilter.firms import FIRMS

NOW = 1790953200 + 10800  # server epoch of the fixture's 18:00 Friday
H = 3600
FTMO = {
    "size": 10000.0,
    "daily_loss": 0.05,
    "max_loss": 0.10,
    "max_loss_mode": "static",
    "daily_basis": "balance",
}
HANTEC = {**FTMO, "size": 100000.0, "daily_basis": "max_be"}


def pos(
    symbol: str,
    side: str,
    volume: float,
    now: float,
    sl: float,
    tick: float = 1e-5,
    value: float = 1.0,
    friday: int = 0,
) -> dict:
    """A schema-2 position with the tick data that stop risk reads."""
    return {
        "symbol": symbol,
        "side": side,
        "volume": volume,
        "price_current": now,
        "sl": sl,
        "tick_size": tick,
        "tick_value_loss": value,
        "friday_close": friday,
    }


def release(
    minutes: float,
    code: str = "nonfarm-payrolls",
    country: str = "US",
    importance: int = 3,
) -> dict:
    """A calendar release `minutes` after NOW."""
    return {
        "time": round(NOW + minutes * 60),
        "code": code,
        "country": country,
        "currency": "USD",
        "importance": importance,
        "name": "Evento",
    }


def levels(found: list) -> list[str]:
    """Just the levels of a list of reasons."""
    return [lvl for lvl, _ in found]


def check_stops() -> None:
    """Loss at the SL per direction, SL in profit, no SL, and the strict comparison with a floor."""
    assert (
        abs(risk.position_loss(pos("EURUSD", "buy", 1.0, 1.09500, 1.09100)) + 400.0)
        < 1e-6
    )
    assert (
        abs(risk.position_loss(pos("EURUSD", "sell", 0.3, 1.0948, 1.0990)) + 126.0)
        < 1e-6
    )
    assert (
        abs(risk.position_loss(pos("EURUSD", "buy", 1.0, 1.0950, 1.0960)) - 100.0)
        < 1e-6
    )
    assert risk.position_loss(pos("EURUSD", "buy", 1.0, 1.0950, 0.0)) is None
    beat = {
        "schema": 2,
        "equity": 10000.0,
        "positions": [pos("EURUSD", "buy", 1.0, 1.0950, 1.0910)],
    }
    floor = {"daily_floor": 9600.0, "max_floor": 9000.0}
    r = risk.reading(beat, floor)
    assert (
        abs(r["equity_at_stops"] - 9600.0) < 1e-6 and r["breaks"] == []
    )  # touching is not below
    beat["equity"] = 9999.0
    assert risk.reading(beat, floor)["breaks"] == ["daily"]
    assert risk.reasons(risk.reading(beat, floor)) == [
        ("red", "Los stops romperían el suelo diario")
    ]
    assert risk.reading(beat, {"daily_floor": 9600.0, "max_floor": 9700.0})[
        "breaks"
    ] == ["daily", "max"]
    both = {
        **beat,
        "positions": [*beat["positions"], pos("XAUUSD", "buy", 1.0, 2650.0, 0.0, 0.01)],
    }
    r = risk.reading(both, floor)
    assert (
        r["no_sl"] == 1
        and r["losses"][1] is None
        and risk.reasons(r)[-1] == ("red", "Posición sin SL")
    )
    old = risk.reading(
        {"equity": 1.0, "positions": [{"sl": 0.0}, {"sl": 1.0}]}, None
    )  # schema 1
    assert (
        old["equity_at_stops"] is None
        and old["no_sl"] == 1
        and old["losses"] == [None, None]
    )


def check_weekend() -> None:
    """3 h and 1 h before the close are the yellow and red edges; past the close is red; no close, nothing."""

    def one(left_s: int, close: int | None = None) -> list:
        """The weekend reasons of one position `left_s` seconds from its close."""
        return rules.weekend(
            [
                pos(
                    "EURUSD",
                    "buy",
                    1,
                    1,
                    1,
                    friday=NOW + left_s if close is None else close,
                )
            ],
            NOW,
        )

    assert one(3 * H + 1) == [] and levels(one(3 * H)) == ["yellow"]
    assert levels(one(H + 1)) == ["yellow"] and levels(one(H)) == ["red"]
    assert levels(one(0)) == ["red"] and "ya pasó el cierre" in one(-60)[0][1]
    assert one(0, close=0) == []


def check_news() -> None:
    """The yellow edge at 30 min, the firm's window (FTMO 2 min, Hantec 3 min), the lists, and which symbols move."""
    ftmo, hantec = FIRMS["ftmo"], FIRMS["hantec"]
    eur = [pos("EURUSD", "buy", 1, 1, 1)]

    def lv(minutes: float, firm: dict = ftmo, **kw) -> list:
        """The levels for one release `minutes` away."""
        return levels(rules.news(eur, [release(minutes, **kw)], firm, NOW))

    assert lv(30) == ["yellow"] and lv(30.02) == []
    assert (
        lv(2.02) == ["yellow"]
        and lv(2) == ["red"]
        and lv(-2) == ["red"]
        and lv(-2.02) == []
    )
    assert lv(3, hantec) == ["red"] and lv(3.02, hantec) == ["yellow"]
    assert lv(10, code="retail-sales") == [] and lv(
        10, hantec, code="retail-sales"
    ) == ["yellow"]  # FTMO's list vs every HIGH
    assert lv(10, hantec, importance=2) == []
    jp = [pos("JP225", "buy", 1, 1, 1)]
    assert (
        rules.news(jp, [release(10)], ftmo, NOW) == []
        and rules.news(jp, [release(10)], hantec, NOW) == []
    )
    oil = release(10, code="eia-crude-oil-stocks-change")
    assert levels(rules.news([pos("USOIL", "buy", 1, 1, 1)], [oil], ftmo, NOW)) == [
        "yellow"
    ]
    assert rules.news(eur, [oil], ftmo, NOW) == []
    assert (
        "sólo calendario MT5"
        in rules.news(eur, [release(10)], hantec, NOW, note=" (sólo calendario MT5)")[
            0
        ][1]
    )
    stage = {"firm": "hantec", "news_ok": True, "weekend_ok": False}
    beat = {
        "schema": 2,
        "positions": [pos("EURUSD", "buy", 1, 1, 1, friday=NOW + 1)],
        "news": [release(1)],
    }
    assert levels(rules.reasons(beat, stage, NOW)) == [
        "red"
    ]  # news allowed, weekend is not
    assert rules.reasons({**beat, "schema": 1}, stage, NOW) == []


def check_hours() -> None:
    """A beat's hours[] make the daily floor exact and give the day's worst equity."""
    gmt, off = 1790979700, 10800
    start = gmt - 1300 + off  # Prague's midnight, server epoch
    beat = {
        "schema": 2,
        "written_gmt": gmt,
        "server_time": gmt + off,
        "day_start": gmt - 4900 + off,
        "balance": 9700.0,
        "equity": 9650.0,
        "positions": [],
        "deals_today": [],
        "service_started": start - 600,
        "hours": [
            {
                "start": start - H,
                "balance0": 1.0,
                "equity0": 1.0,
                "low": 1.0,
                "high": 1.0,
            },
            {
                "start": start,
                "balance0": 9750.0,
                "equity0": 9760.0,
                "low": 9600.0,
                "high": 9800.0,
            },
            {
                "start": start + H,
                "balance0": 9750.0,
                "equity0": 9650.0,
                "low": 9500.0,
                "high": 9700.0,
            },
        ],
    }
    f = floors.reading(beat, FTMO, "Europe/Prague")
    assert (
        f["approx"] == []
        and f["start_balance"] == 9750.0
        and f["daily_floor"] == 9250.0
    )
    assert (
        f["worst_today"] == 9500.0 and f["today"] == 9650.0 - 9750.0
    )  # the hour before the day does not count
    carried = {
        **beat,
        "positions": [{"time": start - 99999}],
        "balance": 93491.54,
        "equity": 94100.0,
        "hours": [
            {
                "start": start,
                "balance0": 93491.54,
                "equity0": 94000.0,
                "low": 93900.0,
                "high": 94200.0,
            }
        ],
    }
    h = floors.reading(carried, HANTEC, "Europe/Prague")
    assert (
        h["approx"] == [] and abs(h["daily_floor"] - 94000.0 * 0.95) < 1e-6
    )  # max(balance, equity) at the day's start
    late = {**carried, "service_started": start + 60}
    assert len(floors.reading(late, HANTEC, "Europe/Prague")["approx"]) == 1
    assert (
        floors.reading({**carried, "hours": []}, HANTEC, "Europe/Prague")["worst_today"]
        is None
    )


def check_order() -> None:
    """All reasons are kept, silence first, reds before yellows, each group in the order given."""
    beat = {
        "written_gmt": 1000,
        "connected": 0,
        "autotrading": 1,
        "account_trade_allowed": 1,
        "account_trade_expert": 1,
    }
    floor = {"daily_left": 0.1, "max_left": 0.9}
    extra = [("yellow", "noticia"), ("red", "stops"), ("red", "sin SL")]
    found = state.reasons(beat, floor, 1010, extra)
    assert found == [
        ("red", "Cerca del suelo diario"),
        ("red", "stops"),
        ("red", "sin SL"),
        ("yellow", "noticia"),
        ("yellow", "Desconectado"),
    ]
    assert state.light(beat, floor, 1010, extra) == ("red", "Cerca del suelo diario")
    assert (
        state.reasons(beat, floor, 1000 + read.CFG["silence_s"] + 1, extra)[0][0]
        == "silent"
    )
    assert state.light(beat, None, 1010, [("red", "sin SL")]) == ("red", "sin SL")


def check_fixture() -> None:
    """The fixture fleet: one red by its stops, one red with no SL, one yellow by news and the weekend."""
    saved = fleetpaths.FLEET
    fleetpaths.FLEET = Path(__file__).resolve().parent / "fixtures" / "fleet"
    read.stage.cache_clear()
    try:
        rows = {r["beat"]["login"]: r for r in state.rows(NOW - 10800 + 20)}
        a, b, c = rows[900001], rows[900002], rows[900003]
        assert (a["light"], a["text"]) == ("red", "Los stops romperían el suelo diario")
        assert (b["light"], b["text"]) == ("red", "Posición sin SL") and b["floor"][
            "approx"
        ] == []
        assert (
            c["light"] == "yellow"
            and len(c["reasons"]) == 4
            and all("según catálogo" in t for _, t in c["reasons"][:2])
        )
        assert abs(a["risk"]["equity_at_stops"] - (a["beat"]["equity"] - 560.0)) < 1e-6
        assert a["floor"]["worst_today"] is not None and a["floor"]["approx"] == []
    finally:
        fleetpaths.FLEET = saved
        read.stage.cache_clear()


def main() -> None:
    """Run every check; an assertion names what broke."""
    for check in (
        check_stops,
        check_weekend,
        check_news,
        check_hours,
        check_order,
        check_fixture,
    ):
        check()
    print("test_fleet_risk_rules: ok")


if __name__ == "__main__":
    main()
