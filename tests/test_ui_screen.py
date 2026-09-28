"""The F5 drawings' pure halves: what the screen report keeps is what the page draws, merges, partials, market rows."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton  # noqa: E402

APP = QApplication.instance() or QApplication([])

from core.paths import report_dir  # noqa: E402
from core.study.render import markdown, page  # noqa: E402
from ui.daemon.results import store  # noqa: E402
from ui.desktop.blocks import fuse, markets  # noqa: E402
from ui.desktop.blocks.head import head  # noqa: E402
from ui.desktop.blocks.screen import screen  # noqa: E402

PROJECT = "Test_USDJPY_donchianUpperCrossUp_M30"
ISOOS = report_dir(PROJECT, "Results", "2026-09-27") / "isOos" / "estrategias" / "Strategy 1.1.85.json"
CROSS = (report_dir(PROJECT, "Retest_Markets_-_Family", "2026-09-27") / "crossmarket" / "estrategias"
         / "Strategy 9.18.85(1).json")


def grid(title: str, select: dict) -> dict:
    """A 2 × 2 grid block tagged `select`."""
    return {"kind": "grid", "title": title, "note": "", "rows": ["1", "2"], "cols": ["a", "b"],
            "values": [[1.0, 2.0], [3.0, None]], "scale": "sequential", "levels": None,
            "labels": None, "select": select, "scale_range": [0.0, 4.0],
            "mark": {"row": "2", "col": "a", "label": "θ₀"}}


def surfaces() -> dict:
    """A marketSurfaces-shaped result: per-market grids over two segments, and a consensus tab."""
    markets_ = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD"]
    per = [grid(f"{m} — {s}", {"market": m, "segment": s}) for m in markets_ for s in ("build", "oos1")]
    return {"module": "x.marketSurfaces", "strategy": "S", "identity": None, "config_hash": "h",
            "computed_at": "t", "wall_s": 1.0, "verdict": None, "warnings": [], "glossary": [],
            "summary": {}, "tabs": [
                {"name": "rejillas", "title": "R", "note": "",
                 "selectors": [{"key": "market", "label": "Mercado", "options": markets_,
                                "default": "USDJPY"},
                               {"key": "segment", "label": "Tramo", "options": ["build", "oos1"],
                                "default": "build"}], "blocks": per},
                {"name": "consenso", "title": "C", "note": "",
                 "selectors": [{"key": "segment", "label": "Tramo", "options": ["build", "oos1"],
                                "default": "build"}],
                 "blocks": [grid(f"Consenso — {s}", {"segment": s}) for s in ("build", "oos1")]}]}


def drawn(result: dict) -> tuple[int, int]:
    """(blocks kept by the screen, blocks the static page draws of them)."""
    return (sum(len(t["blocks"]) for t in result["tabs"]),
            sum(len(page.shown(t)) for t in result["tabs"]))


def test_screen_draws_what_it_keeps() -> None:
    """Every block the screen keeps reaches the page and the markdown: the E3 result and a grouped tab."""
    e3 = json.loads(ISOOS.read_text(encoding="utf-8"))
    kept, shown = drawn(screen(e3, {}))
    assert kept == shown == 4, (kept, shown)
    got = screen(surfaces(), {"rejillas": {"_markets": ["EURUSD", "GBPUSD", "AUDUSD"],
                                          "segment": "oos1"}})
    kept, shown = drawn(got)
    assert kept == shown == 5, (kept, shown)       # 3 markets + consensus, and consensus tab's own
    titles = [b["title"] for b in got["tabs"][0]["blocks"]]
    assert titles == ["EURUSD — oos1", "GBPUSD — oos1", "AUDUSD — oos1", "Consenso — oos1"], titles
    assert "Mercado: EURUSD, GBPUSD, AUDUSD" in got["tabs"][0]["note"]
    md = markdown.render(got, "t")
    assert md.count("θ₀: fila 2, columna a") == 5, md


def test_split_and_picker() -> None:
    """Three markets on one scale plus the consensus of the same segment; a fourth press drops the oldest."""
    tab = surfaces()["tabs"][0]
    pool = [b for t in surfaces()["tabs"] for b in t["blocks"]]
    plain, maps, consensus = markets.split(tab, {"segment": "build"}, pool)
    assert plain == [] and [m["select"]["market"] for m in maps] == ["USDJPY", "EURUSD", "GBPUSD"]
    assert consensus["title"] == "Consenso — build"
    seen = []
    row = markets.picker(tab, ["USDJPY", "EURUSD", "GBPUSD"], seen.append)
    buttons = {b.text(): b for b in row.findChildren(QPushButton)}
    buttons["AUDUSD"].setChecked(True)
    assert seen[-1] == ["EURUSD", "GBPUSD", "AUDUSD"] and not buttons["USDJPY"].isChecked(), seen
    for m in ("EURUSD", "GBPUSD", "AUDUSD"):
        buttons[m].setChecked(False)
    assert seen[-1] == ["AUDUSD"] and buttons["AUDUSD"].isChecked(), seen   # never below one


def test_partials_and_merge() -> None:
    """The stored crossmarket result carries its re-run beside it; the merge swaps only that market."""
    stored, _ = store.load(CROSS)
    assert len(stored["partials"]) >= 1, stored.get("partials")
    part = stored["partials"][-1]["result"]
    only = part["only"]
    assert store.partials(CROSS.parent.parent / "crossmarket.json") == []
    got = fuse.merge(stored, part)
    assert got["verdict"] == stored["verdict"] and "partials" not in got
    tab = next(t for t in got["tabs"] if t["name"] == "random")
    theirs = [b for b in next(t for t in part["tabs"] if t["name"] == "random")["blocks"]
              if b.get("select")]
    mine = [b for b in tab["blocks"] if (b.get("select") or {}).get("mercado") == only]
    assert mine == theirs, (len(mine), len(theirs))
    old = next(t for t in stored["tabs"] if t["name"] == "random")["blocks"]
    assert len(tab["blocks"]) == len(old), (len(tab["blocks"]), len(old))
    assert only in fuse.notice(stored, part)
    top = head(part, None)                      # kept alive: its labels die with it
    words = " ".join(w.text() for w in top.findChildren(QLabel))
    assert "el veredicto sale del análisis entero" in words, words


if __name__ == "__main__":
    for test in (test_screen_draws_what_it_keeps, test_split_and_picker, test_partials_and_merge):
        test()
    print("ok: pantalla = página, rejillas lado a lado, parciales y fusión")
