#!/usr/bin/env python3
"""MT5 Bridge › Verificar's side-by-side trades (owner, 2026-09-30: paired by entry time):
one row per SQX entry in the feed's clock, three columns per firm, and a firm's light off
drops exactly its three."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mt5.verify import sidebyside
from ui.desktop.mt5bridge.render import filtered


def pairs(hours: int, pnl: list[float]) -> pd.DataFrame:
    """Two SQX trades shifted to a firm's server clock; MT5 opened only the first."""
    opened = pd.to_datetime(["2025-01-02 10:00", "2025-01-03 11:00"]) + pd.Timedelta(hours=hours)
    return pd.DataFrame({"Type": ["Buy", "Sell"], "Open time": opened, "Profit/Loss USD": pnl,
                         "Open time_mt5": [opened[0], pd.NaT], "Profit/Loss USD_mt5": [9.0, None]})


def test_rows_are_sqx_entries_and_lights_drop_columns() -> None:
    """Both firms' shifted entries land on the same two rows; hiding FTMO keeps Hantec whole."""
    got = sidebyside.table({"ftmo": {"pairs": pairs(2, [10.0, -5.0]), "hours": 2},
                            "hantec": {"pairs": pairs(3, [11.0, -4.0]), "hours": 3}})
    assert [r[:2] for r in got["rows"]] == [["2025-01-02 10:00", "Buy"],
                                            ["2025-01-03 11:00", "Sell"]]
    assert got["rows"][0][3] == "2025-01-02 12:00" and got["rows"][0][6] == "2025-01-02 13:00"
    assert got["rows"][1][3] == "" and got["rows"][1][4] is None
    shown = filtered({"tabs": [{"blocks": [got]}]}, {"hantec"})["tabs"][0]["blocks"][0]
    assert shown["columns"] == ["entrada SQX", "tipo", "Hantec · P&L SQX",
                                "Hantec · entrada MT5", "Hantec · P&L MT5"]
    assert shown["rows"][0] == ["2025-01-02 10:00", "Buy", 11.0, "2025-01-02 13:00", 9.0]


if __name__ == "__main__":
    test_rows_are_sqx_entries_and_lights_drop_columns()
    print("ok")
