#!/usr/bin/env python3
"""MetaTracker on known answers: each firm's day start, the two floors, what makes a figure approximate, each light."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mt5.fleet.app import floors, read, state

GMT = 1790979700  # 2026-10-02 22:21:40 UTC; the servers read 01:21 of the 3rd
OFFSET = 10800
MIDNIGHT = GMT - 4900 + OFFSET  # server epoch of the server's own 00:00
FTMO = {
    "size": 10000.0,
    "daily_loss": 0.05,
    "max_loss": 0.10,
    "max_loss_mode": "static",
    "daily_basis": "balance",
}
HANTEC = {**FTMO, "size": 100000.0, "daily_basis": "max_be"}


def beat(
    balance: float,
    equity: float,
    positions: list = (),
    deals: list = (),
    written: int = GMT,
) -> dict:
    """A beacon beat with only what the floors and the lights read."""
    return {
        "written_gmt": written,
        "server_time": written + OFFSET,
        "day_start": MIDNIGHT,
        "balance": balance,
        "equity": equity,
        "positions": list(positions),
        "deals_today": list(deals),
        "connected": 1,
        "autotrading": 1,
        "account_trade_allowed": 1,
        "account_trade_expert": 1,
    }


def deal(server_time: int, profit: float) -> dict:
    """A closing deal with a 2-unit commission."""
    return {
        "time": server_time,
        "profit": profit,
        "swap": 0.0,
        "commission": -2.0,
        "fee": 0.0,
    }


def main() -> None:
    """Run every check; an assertion names what broke."""
    # Prague's midnight is 22:00 UTC in summer; New York + 7 h is 21:00 UTC, the server's own 00:00.
    assert floors.day_start(GMT, "Europe/Prague") == GMT - 1300
    assert floors.day_start(GMT, "EETUS") == GMT - 4900 == MIDNIGHT - OFFSET

    # FTMO: a deal booked between the server's midnight and Prague's belongs to yesterday.
    deals = [deal(MIDNIGHT + 600, -100.0), deal(MIDNIGHT + 4000, -48.0)]
    f = floors.reading(beat(9700.0, 9650.0, deals=deals), FTMO, "Europe/Prague")
    assert (
        f["start_balance"] == 9750.0
        and f["daily_floor"] == 9250.0
        and f["approx"] == []
    )
    assert f["daily_room"] == 400.0 and abs(f["daily_left"] - 0.8) < 1e-9
    assert f["max_floor"] == 9000.0 and abs(f["max_left"] - 0.65) < 1e-9
    # Before Prague's midnight the firm's day began yesterday and the beat does not reach it.
    early = beat(9700.0, 9700.0, written=GMT - 3000)
    assert len(floors.reading(early, FTMO, "Europe/Prague")["approx"]) == 1

    # Hantec: 5 % of the day's starting balance; a position carried over midnight makes it approximate.
    f = floors.reading(beat(93491.54, 93491.54), HANTEC, "EETUS")
    assert (
        abs(f["daily_floor"] - 93491.54 * 0.95) < 1e-6
        and f["approx"] == []
        and f["max_floor"] == 90000.0
    )
    carried = [{"time": MIDNIGHT - 5000}]
    assert (
        len(
            floors.reading(beat(93491.54, 93600.0, positions=carried), HANTEC, "EETUS")[
                "approx"
            ]
        )
        == 1
    )
    assert (
        floors.reading(
            beat(93491.54, 93600.0, positions=[{"time": MIDNIGHT + 60}]),
            HANTEC,
            "EETUS",
        )["approx"]
        == []
    )

    # Lights, worst first: silence over a floor, a floor over a switch.
    ok = floors.reading(beat(9750.0, 9750.0), FTMO, "Europe/Prague")
    near = floors.reading(
        beat(9750.0, 9350.0), FTMO, "Europe/Prague"
    )  # 100 of 500 left
    assert state.light(beat(9750.0, 9750.0), ok, GMT + 30) == (state.GREEN, "Operando")
    assert state.light(beat(9750.0, 9350.0), near, GMT + 30) == (
        state.RED,
        "Cerca del suelo diario",
    )
    low = floors.reading(
        beat(9200.0, 9200.0), FTMO, "Europe/Prague"
    )  # 200 of 1000 left to the total
    assert state.light(beat(9200.0, 9200.0), low, GMT + 30) == (
        state.RED,
        "Cerca del suelo total",
    )
    off = {**beat(9750.0, 9750.0), "autotrading": 0}
    assert state.light(off, ok, GMT + 30) == (state.YELLOW, "AutoTrading apagado")
    assert state.light({**off, "equity": 9350.0}, near, GMT + 30)[0] == state.RED
    assert state.light(off, near, GMT + read.CFG["silence_s"] + 1) == (
        state.SILENT,
        "Calla 5 min",
    )
    assert state.light(beat(1.0, 1.0), None, GMT)[0] == state.UNKNOWN
    print("test_fleet_floors: ok")


if __name__ == "__main__":
    main()
