#!/usr/bin/env python3
"""A population study on one strategy's page (feedback 2026-09-29 §4.5): its rows, its bars,
its grid line and its scaled siblings; nothing of another strategy; None when none names it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui.daemon.results.slice import slice_for, verdict_row, whole

POPULATION = {"strategy": None, "identity": None, "tabs": [
    {"name": "scaled", "note": "n", "blocks": [
        {"kind": "grid", "rows": ["A", "B"], "cols": ["x"], "values": [[1.0], [2.0]]},
        {"kind": "bars", "items": [{"label": "A", "value": 1}, {"label": "B", "value": 2}]},
        {"kind": "table", "columns": ["mother", "timeframe"],
         "rows": [["A", "H4"], ["B", "H4"]]},
        {"kind": "table", "columns": ["strategy"], "rows": [["A_ScaledH4"], ["AB"]]},
        {"kind": "verdict", "text": "3 de 90"}]},
    {"name": "agg", "blocks": [{"kind": "table", "columns": ["", "valor"], "rows": [["x", 1]]}]}]}


def test_only_this_strategy() -> None:
    """A's grid line, bar, table row and sibling survive; B, «AB» and the aggregate tab go."""
    got = slice_for(POPULATION, "A")
    assert [t["name"] for t in got["tabs"]] == ["scaled"] and got["sliced"]
    grid, bars, table, siblings = got["tabs"][0]["blocks"]
    assert grid["rows"] == ["A"] and grid["values"] == [[1.0]]
    assert [i["label"] for i in bars["items"]] == ["A"]
    assert table["rows"] == [["A", "H4"]] and siblings["rows"] == [["A_ScaledH4"]]
    assert got["tabs"][0]["note"].startswith("Corrida de toda la población")
    assert slice_for(POPULATION, "C") is None
    assert POPULATION["tabs"][0]["blocks"][0]["rows"] == ["A", "B"]      # never mutated


def test_verdict_row_and_whole() -> None:
    """Nothing names it: its verdict.csv row when it has one, else the population as it is,
    each tab saying so."""
    row = verdict_row(POPULATION, {"strategy": "C", "identity": "x", "verdict": "DUDOSA"}, "C")
    assert row["tabs"][0]["blocks"][0]["rows"] == [["C", "DUDOSA"]]
    shown = whole(POPULATION, "C")
    assert len(shown["tabs"]) == 2 and shown["tabs"][1]["note"].startswith("Este estudio lee")


if __name__ == "__main__":
    test_only_this_strategy()
    test_verdict_row_and_whole()
    print("ok")
