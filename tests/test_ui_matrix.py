"""The population matrix offscreen: real databank through the real routes, a batch run, the curate strip, 5,000 rows timed."""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtCore import QItemSelectionModel, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.paths import ROOT  # noqa: E402
from ui.daemon.results.api import ROUTER as RESULTS  # noqa: E402
from ui.daemon.runner import api as runner  # noqa: E402
from ui.desktop import client  # noqa: E402

PROJECT, BANK = "USDJPY_workflow_profiling_v1", "Results"
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"
STATES = ("pass", "fail", "watch", "info", "none")
QUEUED: list[dict] = []


def wire() -> TestClient:
    """Point the window's client at an in-process daemon; queued jobs are recorded, never started."""
    app = FastAPI()
    app.include_router(RESULTS)
    app.include_router(runner.ROUTER)
    tc = TestClient(app)

    def get(path: str, **params: str) -> dict:
        """`client.get` over the in-process app."""
        r = tc.get(f"/api/{path}", params=params)
        r.raise_for_status()
        return r.json()

    def post(path: str, body: dict) -> dict:
        """`client.post` over the in-process app."""
        r = tc.post(f"/api/{path}", json=body)
        r.raise_for_status()
        return r.json()

    client.get, client.post = get, post
    runner.jobs.start = lambda label, argv, about: QUEUED.append(argv) or {"id": str(len(QUEUED))}
    return tc


def test_real(app: QApplication) -> None:
    """The real databank: present columns, skipped line, click → selection + signals, run, curate."""
    from ui.desktop.matrix import menus
    from ui.desktop.matrix.view import Matrix
    from ui.desktop.selection import SELECTION
    m = Matrix()
    m.resize(1500, 900)
    SELECTION.choose(project=PROJECT, databank=BANK)
    assert m.where == (PROJECT, BANK), m.where
    keys = [c["key"] for c in m.model.columns]
    assert keys == m.data["present"] and "gate" in keys, keys
    # 200 judged by the reports, plus the databank's files today — a strategy no study has
    # judged is still a row (ui/daemon/loader/find.roster).
    assert m.model.rowCount() == len(m.data["strategies"]) >= 200
    assert "no es un estudio del catálogo" in m.lost.text() and m.lost.isVisibleTo(m)
    gate = 2 + keys.index("gate")
    assert m.model.headerData(gate, Qt.Horizontal) == "Puerta IS/OOS"
    assert "ELIMINA" in m.model.headerData(gate, Qt.Horizontal, Qt.ToolTipRole)
    studies, populations = [], []
    m.open_study.connect(studies.append)
    m.open_population.connect(populations.append)
    m.cell_clicked(m.model.index(0, gate))
    assert studies == ["gate"] and SELECTION.now["identity"] == m.model.strategy(0)["identity"]
    m.header_clicked(gate)
    assert populations == ["gate"]
    m.every.setChecked(True)
    assert m.model.columnCount() == 2 + len(m.catalogue)
    m.every.setChecked(False)
    menus.want(m, "gate", "pass", False)
    assert all(m.model.state(i, "gate") != "pass" for i in m.model.rows)
    m.model.sort(gate, Qt.AscendingOrder)
    m.show()
    app.processEvents()
    m.table.selectRow(0)
    m.table.selectionModel().select(m.model.index(1, 0), QItemSelectionModel.Select |
                                    QItemSelectionModel.Rows)
    m.runbar.study.setCurrentIndex(m.runbar.study.findData("edgeCost"))
    answer = m.runbar.run(*m.where, "USDJPY", [m.model.strategy(r)["strategy"] for r in (0, 1)])
    assert len(answer["jobs"]) == 2 and len(QUEUED) == 2, answer
    m.run_selected()
    assert len(QUEUED) == 4 and "en cola" in m.runbar.answer.text()
    m.runbar.study.addItem("gate", "gate")
    m.runbar.study.setCurrentIndex(m.runbar.study.count() - 1)
    m.run_selected()
    assert "población entera" in m.runbar.answer.text(), m.runbar.answer.text()
    texts = lambda sec: [a.text() for a in menus.column_menu(m, sec).actions()]  # noqa: E731
    assert any("/curate" in t for t in texts(gate))
    assert not any("/curate" in t for t in texts(2 + keys.index("snoopingScreen")))
    menus.show_curate(m, "gate")
    assert "/curate" in m.strip.command.text() and m.strip.isVisibleTo(m)
    app.processEvents()
    m.grab().save(str(SHOTS / "F-matrix-real.png"))
    menus.clear_filters(m)
    m.strip.hide()
    app.processEvents()
    m.grab().save(str(SHOTS / "F-matrix-real-all.png"))


def synthetic(n: int) -> dict:
    """A matrix of n strategies over every present study of the catalogue, a tenth of cells stale."""
    keys = ["gate", "decay", "snoopingScreen", "crossmarket", "mcRetest", "monkey", "profitShape",
            "edgeCost", "conditionalMap", "exposure"]
    strategies = [{"strategy": f"Strategy {i // 100}.{i % 100}.{i % 7}", "identity": f"{i:064x}"}
                  for i in range(n)]
    cells = {s["identity"]: {k: {"state": STATES[(i * 7 + j * 3) % 5], "label": STATES[(i + j) % 5],
                                 "stale": (i + j) % 10 == 0, "day": "2026-09-26"}
                             for j, k in enumerate(keys) if (i + j) % 6}
             for i, s in enumerate(strategies)}
    return {"studies": keys, "present": keys, "strategies": strategies, "cells": cells,
            "skipped": [{"path": "2026-09-26/edgeCost", "reason": "sin identidad", "n": 12}]}


def test_many(app: QApplication) -> None:
    """5,000 rows × 10 studies: load, sort, filter and a first paint each well under a second."""
    from ui.desktop.matrix import menus
    from ui.desktop.matrix.view import Matrix
    real_get = client.get
    fake = synthetic(5000)
    client.get = lambda path, **p: fake if path == "matrix" else real_get(path, **p)
    m = Matrix()
    m.reread()
    m.resize(1700, 1000)
    m.show()
    t = time.perf_counter()
    m.load("Test_synthetic", "Results")
    app.processEvents()
    took = {"load+paint": time.perf_counter() - t}
    t = time.perf_counter()
    m.model.sort(5, Qt.AscendingOrder)
    app.processEvents()
    took["sort"] = time.perf_counter() - t
    t = time.perf_counter()
    menus.want(m, "gate", "fail", False)
    m.model.refilter("Strategy 1")
    app.processEvents()
    took["filter"] = time.perf_counter() - t
    t = time.perf_counter()
    m.table.scrollToBottom()
    app.processEvents()
    took["scroll"] = time.perf_counter() - t
    m.grab().save(str(SHOTS / "F-matrix-5000.png"))
    print({k: f"{v:.3f} s" for k, v in took.items()}, m.model.rowCount(), "filas visibles")
    assert max(took.values()) < 1.0, took
    client.get = real_get


if __name__ == "__main__":
    from ui.desktop.theme import QSS
    wire()
    qt = QApplication.instance() or QApplication([])
    qt.setStyleSheet(QSS)
    SHOTS.mkdir(parents=True, exist_ok=True)
    test_real(qt)
    test_many(qt)
    print("ok")
