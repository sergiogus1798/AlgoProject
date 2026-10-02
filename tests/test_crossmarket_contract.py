#!/usr/bin/env python3
"""Cross Market's opening tables (owner, 2026-10-01): MinTRL reads «No alcanzable» in red when
the real Sharpe does not clear the reference one, never the number the squared negative gap
gave (USDCHF 35,426); «El backtest de cada mercado» shows Sharpe total, never the per-trade
one; every market reads by its short name; the verdict header carries no score; and the
equity lines take their style from their sign alone, the reference included."""

import os
import sys
from pathlib import Path

import pandas as pd

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt  # noqa: E402

from studies.transfer.crossmarket import one  # noqa: E402
from studies.transfer.crossmarket.contract import backtest  # noqa: E402
from ui.desktop.blocks import lines  # noqa: E402

REAL = {"net": 1000.0, "pf": 1.2, "dd": 300.0, "dd_pct": 0.03, "ret_dd": 3.3, "sharpe": 0.05}


def row(feed: str, needed: float | None, enough: bool) -> dict:
    """One market's row, as `orchestrate.market.tests` leaves the keys these tables read."""
    return {"feed": feed, "sharpe_total": 0.8, "min_track_benchmark": -0.04, "trades": 754,
            "min_track_needed": needed, "min_track_enough": enough, "pf": 1.1,
            "expectancy": 0.001, "real": REAL, "trades_all": 760}


def test_mintrl_unreachable_reads_no_alcanzable_in_red() -> None:
    """None from `min_track_record` is a red «No alcanzable»; a reachable one stays a number."""
    rows = pd.DataFrame([row("USDCHF_M1", None, False),
                         row("AUDUSD_M1", 120.0, True)])
    block = backtest.evidence(rows, row("USDJPY_M1", 900.0, False))
    mintrl = block["columns"].index("MinTRL")
    assert [r[mintrl] for r in block["rows"]] == ["No alcanzable", 120.0, 900.0]
    assert [s[mintrl] for s in block["states"]] == ["fail", None, "fail"]
    assert [r[0] for r in block["rows"]] == ["USDCHF", "AUDUSD", "USDJPY (base)"]


def test_master_shows_sharpe_total_only() -> None:
    """The per-trade Sharpe is gone from the table; Sharpe total sits in its place."""
    block = backtest.master(pd.DataFrame([row("AUDUSD_M1", 1.0, True)]),
                            row("USDJPY_M1", 1.0, True))
    assert "Sharpe total" in block["columns"]
    assert not any("por operación" in c for c in block["columns"])
    assert block["rows"][0][block["columns"].index("Sharpe total")] == 0.8
    assert block["rows"][0][0] == "AUDUSD"


def test_verdict_has_no_score_and_a_short_market_name() -> None:
    """The header used to read «DESCARTAR falla nota 0»: no score now, and the worst market by
    its short name."""
    summary = {"fraction": 0.0, "cleared": 0, "markets": 9,
               "worst_market": {"market": "USDCHF_M1", "pf": 0.8}}
    block = one.verdict(summary, {"verdict": {"breadth_floor": 0.5}})
    assert block["score"] is None
    assert block["parts"][0]["note"] == "USDCHF"


def test_line_style_follows_the_sign_only() -> None:
    """Nine series and a reference: past six the colours repeat but the style does not cycle —
    each ending below zero is dashed, each ending above solid, the reference too."""
    ends = [1, -1, 2, 3, -2, 4, 5, 6, -3]
    series = [{"label": str(i), "values": [0.0, float(e)], "role": "real"}
              for i, e in enumerate(ends)]
    series += [{"label": "base", "values": [0.0, 7.0], "role": "reference"},
               {"label": "base-", "values": [0.0, -7.0], "role": "reference"}]
    pens = lines._pens({"series": series, "auto_dash_negative": True})
    want = [Qt.DashLine if e < 0 else Qt.SolidLine for e in ends] + [Qt.SolidLine, Qt.DashLine]
    assert [style for _, style, _ in pens] == want


if __name__ == "__main__":
    test_mintrl_unreachable_reads_no_alcanzable_in_red()
    test_master_shows_sharpe_total_only()
    test_verdict_has_no_score_and_a_short_market_name()
    test_line_style_follows_the_sign_only()
    print("ok")
