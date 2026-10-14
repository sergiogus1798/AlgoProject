#!/usr/bin/env python3
"""The panel's three compositions and its variant filters, on a synthetic C3 table."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.variants import filters, look, panel
from ledger import gate

CFG = {"floor_is_per_param": 15, "floor_oos_per_year": 10, "min_variants": 3}


def table(mother_is: int = 300) -> pd.DataFrame:
    """Mother, a canary, an exact copy of the mother, a thin-inside one, a thin-outside one, two good.

    The outside floor reads the oos1 trade count; the `oos2` columns are noise the filters must ignore.
    """
    rows = [("P00000", "origin", mother_is, 40, 10, 1, 2), ("C1", "canary", 300, 40, 9, 9, 9),
            ("P1", "lhs", 300, 40, 10, 1, 2), ("P2", "lhs", 30, 40, 5, 5, 5),
            ("P3", "lhs", 300, 5, 6, 6, 6), ("P4", "lhs", 300, 40, 7, 8, 9),
            ("P5", "lhs", 300, 40, 8, 1, 3)]
    out = pd.DataFrame(rows, columns=["variant_id", "stratum", "NumberOfTrades (build+oos1)",
                                      "NumberOfTrades (oos1)", "NetProfit (build)",
                                      "NetProfit (oos1)", "NetProfit (oos2)"])
    return out.assign(**{"NumberOfTrades (oos2)": 99})


def test_three_compositions_with_distinct_keys() -> None:
    """c1, c2, c3 are three keys; `build -> oos1` alone is no longer a composition."""
    assert [panel.key(c) for c in panel.COMPOSITIONS] == ["c1", "c2", "c3"]
    assert len({panel.label(c) for c in panel.COMPOSITIONS}) == 3
    with pytest.raises(StopIteration):
        panel.key((("build",), ("oos1",)))


def test_filters_count_each_one(monkeypatch: pytest.MonkeyPatch) -> None:
    """Controls, inside floor 15*k, exact duplicates, outside floor 10/yr, in that order, counted."""
    monkeypatch.setattr(gate, "seal", lambda *a: None)
    comp = panel.KEYS["c1"]
    kept, n = filters.screen(table(), comp, k=6, years_oos1=2.75, symbol="XAUUSD", cfg=CFG)
    assert n["controles"] == 1 and n["suelo_dentro"] == 1 and n["duplicados"] == 1
    assert n["suelo_fuera"] == 1 and n["quedan"] == 3 and not n["sin_dato"]
    assert list(kept["variant_id"]) == ["P00000", "P4", "P5"]       # the mother stays, the copy goes


def test_oos2_changes_no_survivor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Duplicates and the outside floor read build and oos1 only: wild oos2 columns keep the same variants."""
    monkeypatch.setattr(gate, "seal", lambda *a: None)
    base, n = filters.screen(table(), panel.KEYS["c1"], 6, 2.75, "XAUUSD", cfg=CFG)
    wild = table().assign(**{"NumberOfTrades (oos2)": [0, 0, 0, 0, 0, 0, 0],
                             "NetProfit (oos2)": [1.0, 2, 3, 4, 5, 6, 7]})
    got, m = filters.screen(wild, panel.KEYS["c1"], 6, 2.75, "XAUUSD", cfg=CFG)
    assert list(got["variant_id"]) == list(base["variant_id"]) == ["P00000", "P4", "P5"] and m == n


def test_values_are_an_input_and_a_mother_under_the_floor_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    """The measure comes from the caller; a mother below a floor warns and that floor is not applied."""
    monkeypatch.setattr(gate, "seal", lambda *a: None)
    vals = pd.DataFrame({"e_is": [1.0, 2.0], "e_oos": [1.0, 2.0]}, index=["P4", "P5"])
    kept, n = filters.screen(table(mother_is=50), panel.KEYS["c1"], 6, 2.75, "XAUUSD",
                             values=vals, cfg=CFG)
    assert n["suelo_dentro"] == 0 and n["avisos"] and n["sin_valor"] == 2
    assert list(kept["variant_id"]) == ["P4", "P5"] and n["sin_dato"]


def test_screen_stops_at_the_seal(monkeypatch: pytest.MonkeyPatch) -> None:
    """oos2 is not read when the seal refuses: the PermissionError comes before the duplicates."""
    def shut(*a: object) -> None:
        """A closed seal."""
        raise PermissionError("sellado")
    monkeypatch.setattr(gate, "seal", shut)
    with pytest.raises(PermissionError):
        filters.screen(table(), panel.KEYS["c1"], 6, 2.75, "XAUUSD", cfg=CFG)
    assert look.panel is panel


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
