#!/usr/bin/env python3
"""Every block kind of every real study result draws offscreen, and nothing raises."""

import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QPointF, QRectF  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402

from core.paths import DATA  # noqa: E402
from ui.desktop.blocks import chart, kinds, result, tabpage  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

PER_STUDY = 3          # strategy files sampled per study; every population file is drawn
SYNTHETIC = [          # kinds no stored report carries yet, so they are built here
    {"kind": "scatter", "title": "s", "x_label": "IS", "y_label": "OOS", "quadrants": True,
     "points": [{"x": -1.0, "y": 0.5, "label": "a", "group": "g1"},
                {"x": 2.0, "y": -0.3, "label": "b", "group": "g2"}],
     "fit": {"slope": 0.1, "intercept": 0.0, "r": 0.2}},
    {"kind": "verdict", "label": "PASA", "state": "pass", "score": 81.0, "meaning": "m",
     "parts": [{"label": "p", "state": "watch", "value": None, "note": "n"}]},
    {"kind": "callout", "text": "El 39,7 % de las simulaciones rindieron peor que el backtest "
     "real en Profit Factor.", "state": "watch"},
    {"kind": "list", "title": "t", "note": "n",
     "items": [{"title": "Shuffle sequence", "text": "d1"},
              {"title": "Resample sequence", "text": "d2"}]},
]


def fixtures() -> list[Path]:
    """Every population result, and a few strategy results of each study."""
    root = DATA / "reports"
    out, per = [], defaultdict(int)
    for f in sorted(root.glob("**/*.json")):
        if f.name == "manifest.json" or f.name.startswith("design_brief"):
            continue
        if f.parent.name == "estrategias":
            study = f.parent.parent.name
            per[study] += 1
            if per[study] > PER_STUDY:
                continue
        elif f.stem != f.parent.name:
            continue
        out.append(f)
    return out


def check_file(path: Path, view: result.ResultView, seen: Counter) -> None:
    """Draw every block of one result through `kinds.draw`, then the whole page."""
    data = json.loads(path.read_text(encoding="utf-8"))
    for tab in data["tabs"]:
        for b in tab["blocks"]:
            w = kinds.draw(b)
            assert not (isinstance(w, QLabel) and "No se pudo dibujar" in w.text()), \
                f"{path}: {b['kind']} «{b.get('title')}» failed: {w.text()}"
            w.resize(1100, w.sizeHint().height())
            w.grab()                # paints; PySide re-raises a paintEvent error from here
            for c in w.findChildren(chart.Canvas):     # the hover sentence, across the width
                for x in range(0, c.width(), 37):
                    c.tip(QPointF(x, c.height() / 2), QRectF(c.rect()))
            seen[b["kind"]] += 1
        if tab.get("selectors"):
            chosen = {s["key"]: s["default"] for s in tab["selectors"]}
            assert tabpage.shown(tab, chosen), f"{path}: tab {tab['name']} default draws nothing"
    view.show(data, {"stale": True, "config_hash": data["config_hash"], "current_hash": "x"})
    for i in range(view.tabs.count() if data["tabs"] else 0):
        view.tabs.setCurrentIndex(i)


def main() -> None:
    """Draw the real reports, the synthetic kinds, a comparison and the fallbacks."""
    start = time.time()
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(QSS)
    view = result.ResultView()
    seen: Counter = Counter()
    files = fixtures()
    assert files, "no study reports under AlgoData/reports"
    for f in files:
        check_file(f, view, seen)
    for b in SYNTHETIC:
        kinds.draw(b).grab()
        seen[b["kind"]] += 1
    assert set(seen) == set(kinds.WIDGETS), f"kinds never drawn: {set(kinds.WIDGETS) - set(seen)}"
    empty = kinds.draw({"kind": "grid", "title": "t", "rows": ["a"], "cols": [], "values": [[]],
                        "scale": "discrete", "levels": None, "labels": None})
    empty.grab()    # 2026-09-27: a grid with rows and no column segfaulted the window here
    bad = kinds.draw({"kind": "pie", "title": "t"})
    assert isinstance(bad, QLabel) and "desconocido" in bad.text()
    print("a KeyError traceback follows on purpose: a broken block must become a red line")
    broken = kinds.draw({"kind": "bars", "title": "t"})
    assert isinstance(broken, QLabel) and "No se pudo dibujar" in broken.text()
    pops = [f for f in files if f.parent.name != "estrategias"]
    left, right = (json.loads(pops[i].read_text(encoding="utf-8")) for i in (0, -1))
    view.compare(left, right, ("a", "b"))
    view.show(None, None)
    view.grab()
    print(f"ok: {len(files)} results, blocks per kind {dict(seen)}, {time.time() - start:.1f} s")


if __name__ == "__main__":
    main()
