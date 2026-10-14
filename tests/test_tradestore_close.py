#!/usr/bin/env python3
"""The trade library keeps `Close type` and `Close price`: `reprice.real` needs both to fill a stop."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from core import tradepack  # noqa: E402

CSV = (
    "Ticket;Symbol;Type;Open time;Open price;Size;Close time;Close price;Profit/Loss;Balance;"
    "Sample type;Close type;MAE ($);MFE ($);Time in trade;Comment\n"
    "1;X;Buy;2024.01.02 10:00:00;100;1;2024.01.02 11:00:00;99.5;-50;99950;IST;SL;60;5;1h;\n"
    "2;X;Buy;2024.01.03 10:00:00;100;1;2024.01.03 12:00:00;101;100;100050;IST;Exit Signal;3;120;2h;\n"
)


def test_pack_keeps_close_type_and_price(tmp_path: Path) -> None:
    """A stop and a signal exit both come out of `pack` with their type and recorded price."""
    csv = tmp_path / "S.csv"
    csv.write_text(CSV)
    tradepack.WORKERS = 1
    tradepack.pack([csv], tmp_path / "trades.parquet", False)
    got = pd.read_parquet(tmp_path / "trades.parquet")
    assert got["Close type"].astype(str).tolist() == ["SL", "Exit Signal"]
    assert got["Close price"].tolist() == [99.5, 101.0]
