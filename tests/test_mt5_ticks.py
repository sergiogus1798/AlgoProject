#!/usr/bin/env python3
"""Step 26's optional real-ticks pass: three curves per firm on the merged chart, the verdicts
named by model, and the firm's own state left to the first pass."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mt5.verify import ticks


def piece(state: str, mt5: list[float]) -> dict:
    """A `judge.firm_result` cut down to what the tab reads."""
    days = pd.to_datetime(["2025-01-02", "2025-01-03"])
    return {"label": "FTMO", "daily_sqx": pd.Series([1.0, 1.0], index=days),
            "daily_mt5": pd.Series(mt5, index=days),
            "verdict": {"kind": "verdict", "label": "Validada", "meaning": "m", "firm": "ftmo"},
            "lonely": {"kind": "table", "title": "t", "firm": "ftmo"},
            "summary": {"firm": "ftmo", "state": state, "mt5_trades": 2}}


def test_three_curves_and_named_verdicts() -> None:
    """One firm with both passes draws SQX once and MT5 twice, each MT5 leg named by its model."""
    pieces, summaries = {}, {}
    ticks.keep(pieces, summaries, "ftmo", piece("pass", [1.0, 0.5]), "dir")
    assert [s["label"] for s in ticks.chart(pieces, "ohlc_m1")["series"]] == ["SQX · FTMO",
                                                                               "MT5 · FTMO"]
    ticks.keep(pieces, summaries, "ftmo", piece("fail", [0.5, 0.2]), "dir")
    assert summaries["ftmo"]["state"] == "pass" and summaries["ftmo"]["ticks_state"] == "fail"
    series = ticks.chart(pieces, "ohlc_m1")["series"]
    assert [s["label"] for s in series] == ["SQX · FTMO", "MT5 OHLC M1 · FTMO",
                                            "MT5 Real ticks · FTMO"]
    assert {s["firm"] for s in series} == {"ftmo"} and series[2]["values"] == [0.5, 0.7]
    first, _, second, _ = ticks.named(pieces["ftmo"], "ohlc_m1") + ticks.named(
        pieces["ftmo"]["ticks"], ticks.MODEL)
    assert first["label"] == "Validada · OHLC M1" and second["label"] == "Validada · Real ticks"


if __name__ == "__main__":
    test_three_curves_and_named_verdicts()
    print("ok")
