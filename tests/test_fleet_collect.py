#!/usr/bin/env python3
"""The collector on known answers: a beat's history row, skipping an unchanged beat, the floating min and max per ticket."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mt5.fleet import rows

GMT = 1790979700
OFFSET = 10800


def beat(profit: float, written: int = GMT, tickets: tuple = (11,)) -> dict:
    """A beat with one open position per ticket, each at the given floating profit."""
    positions = [{"ticket": t, "magic": 7, "symbol": "XAUUSD", "side": "buy", "volume": 0.1,
                  "time": GMT - 600, "profit": profit} for t in tickets]
    return {"login": 5, "written_gmt": written, "server_time": written + OFFSET, "balance": 10000.0,
            "equity": 10000.0 + profit, "floating": profit, "margin": 50.0, "connected": 1,
            "autotrading": 1, "ping_us": 20000, "positions": positions}


def main() -> None:
    """Check the three pure parts."""
    row = rows.history_row(beat(-12.5, tickets=(11, 12)))
    assert list(row) == rows.HISTORY_COLUMNS
    assert row["n_positions"] == 2 and row["equity"] == 9987.5 and row["floating"] == -12.5
    assert rows.server_day(beat(0)) == "2026-10-03"          # 22:21 UTC is 01:21 on the server

    assert rows.is_new(beat(0), None) and rows.is_new(beat(0), GMT - 30)
    assert not rows.is_new(beat(0), GMT)

    exc = {}
    for i, profit in enumerate([5.0, -20.0, 40.0, 10.0]):
        rows.update_excursions(exc, beat(profit, GMT + 60 * i))
    assert exc["11"]["min_profit"] == -20.0 and exc["11"]["max_profit"] == 40.0
    assert exc["11"]["last_seen"] == GMT + 180 and exc["11"]["magic"] == 7
    rows.update_excursions(exc, beat(1.0, GMT + 240, tickets=(12,)))
    assert exc["11"]["last_seen"] == GMT + 180 and exc["12"]["min_profit"] == 1.0   # a closed ticket is kept
    print("fleet collect: ok")


if __name__ == "__main__":
    main()
