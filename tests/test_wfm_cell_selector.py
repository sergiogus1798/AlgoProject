#!/usr/bin/env python3
"""WFM's «Celda» selector: each option picks exactly one equity chart of the matrix tab, and the
other blocks of the tab stay for every option. Reads the Nikkei strategy contract when on disk."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import paths
from ui.desktop.blocks.pick import shown


def test_cell_selector_picks_one_chart() -> None:
    """Two cells draw different lines; the same count of untagged blocks stays."""
    files = sorted(
        (paths.DATA / "reports").glob(
            "Trade_NIKKEI225_M30_volatilidadL/WFM/*/wfm/estrategias/*.json"
        )
    )
    if not files:
        return
    tab, sel = next(
        (t, s)
        for t in json.loads(files[-1].read_text())["tabs"]
        for s in t.get("selectors", [])
        if s["key"] == "celda"
    )
    a, b = (
        shown(tab, {"celda": sel["options"][0]}),
        shown(tab, {"celda": sel["options"][5]}),
    )
    lines = lambda bl: [x for x in bl if x["kind"] == "lines"]  # noqa: E731
    assert len(lines(a)) == len(lines(b)) == 1 and lines(a) != lines(b)
    assert len(a) == len(b)
    assert all(
        x["select"]["celda"] in sel["options"] for x in tab["blocks"] if x.get("select")
    )


if __name__ == "__main__":
    test_cell_selector_picks_one_chart()
    print("ok")
