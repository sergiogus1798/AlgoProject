#!/usr/bin/env python3
"""Cross timeframe's «Madre» selector (feedback 2026-10-04 b §10): choosing another mother must
change every per-mother block of the tab, and what is about all mothers says so in its title.
Reads the Nikkei contract when it is on disk; the synthetic case always runs."""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import paths
from studies.transfer.crossTF.equity import per_mother
from ui.daemon.results.slice import slice_for
from ui.desktop.blocks.pick import shown

TABLE = pd.DataFrame({"mother": ["A", "A", "B"], "x": [1, 2, 3]})


def _make(rows: pd.DataFrame) -> dict:
    """A table block with a scope tag, as the study builds its tables."""
    return {
        "kind": "table",
        "title": "t",
        "columns": ["mother", "x"],
        "rows": rows.values.tolist(),
        "select": {"scope": "Escalado"},
    }


def test_per_mother_blocks_follow_the_selector() -> None:
    """One block per mother keeps its own tags, and the window's `shown` picks only that one."""
    tab = {
        "selectors": [
            {"key": "mother", "options": ["A", "B"], "default": "A"},
            {"key": "scope", "options": ["Escalado"], "default": "Escalado"},
        ],
        "blocks": per_mother(_make, TABLE, ["A", "B"]),
    }
    assert [len(b["rows"]) for b in shown(tab, {"mother": "A"})] == [2]
    assert [len(b["rows"]) for b in shown(tab, {"mother": "B"})] == [1]
    only_a = slice_for({"tabs": [{**tab, "name": "t"}]}, "A")["tabs"][0]
    assert [s["key"] for s in only_a["selectors"]] == ["scope"] and len(
        only_a["blocks"]
    ) == 1
    assert "mother" not in only_a["blocks"][0]["select"]


def test_nikkei_contract() -> None:
    """Real contract: two mothers draw different tables and equity; the rest is titled as whole."""
    files = sorted(
        (paths.DATA / "reports").glob(
            "Trade_NIKKEI225_M30_volatilidadL/CrossTF/*/crossTF/crossTF.json"
        )
    )
    if not files:
        return
    tab = json.loads(files[-1].read_text())["tabs"][0]
    one, two = sorted(
        o for s in tab["selectors"] if s["key"] == "mother" for o in s["options"]
    )[:2]
    a, b = shown(tab, {"mother": one}), shown(tab, {"mother": two})
    for kind in ("lines", "table"):
        assert [x for x in a if x["kind"] == kind] != [
            x for x in b if x["kind"] == kind
        ], kind
    for blk in tab["blocks"]:
        if blk["kind"] in ("grid", "bars") and not blk.get("select", {}).get("mother"):
            assert "todas las madres" in blk["title"], blk["title"]


if __name__ == "__main__":
    test_per_mother_blocks_follow_the_selector()
    test_nikkei_contract()
    print("ok")
