#!/usr/bin/env python3
"""`kept.rows` on a hand-built scorecard and harvest: the name link, the oos1 cut, the R scale."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import kept


def make() -> tuple[pd.DataFrame, pd.DataFrame]:
    """A three-strategy scorecard and a four-day harvest, IS ending on day two."""
    card = pd.DataFrame(
        {
            "strategy": ["A", "B", "C"],
            "oos_worst_day_r": [-1.0, -2.0, -3.0],
            "dd_esperado_r": [5.0, 6.0, None],
            "oos_net_per_year_r": [10.0, 5.0, 1.0],
        },
        index=pd.Index(["ia", "ib", "ic"], name="identity"),
    )
    days = pd.date_range("2020-01-01", periods=4)  # IS ends day 2, oos1 is days 3-4
    eq = [
        pd.DataFrame({"day": days, "identity": i, "equity": v, "sample": s})
        for i, vals in {"ia": [0, 100, 100, 300], "ib": [0, 0, 0, 0]}.items()
        for s, v in (("IS", vals[:2] * 2), ("OOS", vals))
    ]
    eq = pd.concat(eq)
    return card, eq[(eq["sample"] == "OOS") | (eq["day"] <= days[1])]


def test_rows() -> None:
    """A name absent gets no row, the curve starts after IS in R, a repeated name raises."""
    card, eq = make()
    got, curve = kept.rows(card, ["A", "Z"], eq, 100.0)
    assert (
        list(got["strategy"]) == ["A"] and got.loc[0, "oos_worst_day_r"] == -1.0
    )  # Z: no row
    assert list(curve["equity_r"]) == [0.0, 2.0] and curve["day"].min() > pd.Timestamp(
        "2020-01-02"
    )
    card.loc["ib", "strategy"] = "A"
    try:
        kept.rows(card, ["A"], eq, 100.0)
        raise AssertionError("a name held twice must raise")
    except ValueError:
        pass


if __name__ == "__main__":
    test_rows()
    print("ok")
