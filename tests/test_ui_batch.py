"""The variant batch: /api/batch never lets oos2 out, and «Lote» draws a real batch offscreen."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from core.paths import DATA, ROOT
from ui.daemon.batch import api, panel
from ui.desktop.batchview import tab

SHOTS = ROOT / "scratch" / "ui-plan" / "shots"
# Since F13 (2026-09-28): the one batch on disk, the Donchian mother's 150 variants over five
# axes. The batch folder without metrics.parquet and the 1,093-variant batch of the retired
# fixture (USDJPY_workflow_profiling_v1) have no counterpart: that refusal is built in a
# temporary folder, and the view is drawn on this batch only.
REAL = ("Test_USDJPY_donchianUpperCrossUp_M30", "Strategy_9.27.83")
VARIANTS, AXES = 150, 5


def http() -> TestClient:
    """A local app holding only the batch router; never the real daemon, never 8765."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    return TestClient(app)


def labels(value: object) -> list[str]:
    """Every key and every string inside a response."""
    if isinstance(value, dict):
        return [str(k) for k in value] + [s for v in value.values() for s in labels(v)]
    if isinstance(value, list):
        return [s for v in value for s in labels(v)]
    return [value] if isinstance(value, str) else []


def sealed_free(out: dict) -> None:
    """Assert nothing that left the route names oos2 or ALL."""
    bad = [s for s in labels(out) if "oos2" in s or "ALL" in s]
    assert not bad, bad


def test_real(c: TestClient) -> dict:
    """The real batch: its axes, both outcomes, the mother, and nothing sealed."""
    out = c.get("/api/batch", params=dict(zip(("project", "strategy"), REAL))).json()
    sealed_free(out)
    assert out["has_batch"] and "error" not in out, out.get("error")
    assert len(out["variants"]) == VARIANTS and set(out["outcomes"]) == set(panel.OUTCOMES)
    assert all(len(a["values"]) == VARIANTS for a in out["axes"]) and len(out["axes"]) == AXES
    assert out["variants"][out["mother"]] == "P00000"
    spaced = c.get("/api/batch", params={"project": REAL[0],
                                         "strategy": REAL[1].replace("_", " ")})
    assert spaced.json()["variants"] == out["variants"]
    assert c.get("/api/batch/has", params=dict(zip(("project", "strategy"), REAL))).json() == \
        {"has_batch": True}
    return out


def test_refusals(c: TestClient) -> None:
    """A folder without metrics.parquet and a mother without a batch each get a sentence."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "Strategy_9.9.9"
        work.mkdir()
        with mock.patch.object(panel, "folders", lambda p, s: [work]), \
                mock.patch.object(panel.where, "batch", lambda p, s, n: work):
            out = c.get("/api/batch", params={"project": "Fake", "strategy": "Strategy 9.9.9"})
    out = out.json()
    assert out["has_batch"] and "metrics.parquet" in out["error"], out
    none = c.get("/api/batch", params={"project": REAL[0], "strategy": "Strategy 0.0.0"}).json()
    assert none == {"has_batch": False, "error": none["error"]} and "no tiene lote" in none["error"]
    assert not c.get("/api/batch/has", params={"project": "X", "strategy": "S 1"}).json()["has_batch"]


def test_synthetic(c: TestClient) -> None:
    """A batch whose file holds every sealed spelling, a sealed parameter and a flat one."""
    frame = pd.DataFrame({
        "variant_id": ["P00000", "P00001", "P00002"], "stratum": ["origin", "factorial", "canary"],
        "origin": [True, False, False], "param_Period": [10.0, 20.0, 30.0],
        "param_Shift": [1.0, 1.0, 1.0], "param_oos2Len": [5.0, 6.0, 7.0],
        "NetProfit (build)": [1.0, -2.0, 3.0], "NetProfit (oos1)": [4.0, 5.0, -6.0],
        "NetProfit (oos2)": [7.0, 8.0, 9.0], "NetProfit (ALL)": [1.0, 1.0, 1.0],
        "NetProfit (oos1+oos2)": [2.0, 2.0, 2.0], "Drawdown (oos2)": [0.1, 0.2, 0.3]})
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "Strategy_9.9.9"
        work.mkdir()
        frame.to_parquet(work / "metrics.parquet")
        assert not any(panel.sealed(col) for col in panel.columns(work / "metrics.parquet"))
        with mock.patch.object(panel, "folders", lambda p, s: [work]), \
                mock.patch.object(panel.where, "batch", lambda p, s, n: work):
            out = c.get("/api/batch", params={"project": "Fake", "strategy": "Strategy 9.9.9"}).json()
    sealed_free(out)
    assert [a["label"] for a in out["axes"]] == ["Period"], out["axes"]
    assert out["fixed"] == [{"label": "Shift", "value": 1}] and "Shift = 1" in out["note"]
    held = {"has_batch": True, "variants": ["ALL"], "note": "x"}
    with mock.patch.object(panel, "batch", lambda p, s: held):
        leak = c.get("/api/batch", params={"project": "P", "strategy": "S"}).json()
    assert set(leak) == {"has_batch", "error"}, leak


def test_view(real: dict) -> None:
    """«Lote» offscreen: the real batch with hover and the selector, and a refusal."""
    app = QApplication.instance() or QApplication([])
    from ui.desktop.theme import QSS
    app.setStyleSheet(QSS)
    view = tab.BatchTab()
    view.resize(1280, 820)
    with mock.patch.object(tab.client, "get", lambda path, **kw: real):
        assert view.load(*REAL)
    view.show()
    app.processEvents()
    chart = view.chart
    xs = [chart.box().left(), chart.box().right()]
    assert chart.nearest(QPointF(xs[0] - 30, 100)) is None
    mother = real["mother"]
    y0 = chart.box().bottom() - (real["axes"][0]["values"][mother] - min(real["axes"][0]["values"])) \
        / (max(real["axes"][0]["values"]) - min(real["axes"][0]["values"])) * chart.box().height()
    hit = chart.nearest(QPointF(xs[0], y0))
    assert hit is not None and real["axes"][0]["values"][hit] == real["axes"][0]["values"][mother]
    assert chart.sentence(mother).startswith("P00000 (origin) — la madre")
    view.colour_by.setCurrentText("NetProfit (build)")
    assert chart.outcome == "NetProfit (build)"
    view.colour_by.setCurrentText("NetProfit (oos1)")
    app.processEvents()
    SHOTS.mkdir(parents=True, exist_ok=True)
    assert view.grab().save(str(SHOTS / "K-batch.png"))
    view.show_batch({"has_batch": True, "error": "el lote existe pero aún no tiene metrics.parquet"})
    assert not view.chart.isVisible() and "metrics.parquet" in view.note.text()


def main() -> None:
    """Run every check."""
    assert (DATA / "strategyPermutations" / REAL[0] / REAL[1] / "metrics.parquet").exists()
    c = http()
    real = test_real(c)
    test_refusals(c)
    test_synthetic(c)
    test_view(real)
    print("ok — /api/batch and «Lote»")


if __name__ == "__main__":
    main()
