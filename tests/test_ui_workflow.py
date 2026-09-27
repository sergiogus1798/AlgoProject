"""The workflow rail, both sides: the route on real projects, the blind door, and the widget offscreen."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.paths import ROOT  # noqa: E402
from ui.daemon.workflow import derive  # noqa: E402
from ui.daemon.workflow.api import ROUTER  # noqa: E402
from ui.daemon.workflow.steps import STEPS  # noqa: E402

PROJECT = "USDJPY_workflow_profiling_v1"
STATES = {"done", "running", "pending", "blocked", "sealed", "missing"}
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"


def route(project: str) -> dict:
    """GET /api/workflow on a daemon holding only this router."""
    app = FastAPI()
    app.include_router(ROUTER)
    r = TestClient(app).get("/api/workflow", params={"project": project})
    assert r.status_code == 200, r.text
    return r.json()


def test_route() -> dict:
    """The real project: every step in WORKFLOW order, the contract's keys, the ledger's door."""
    data = route(PROJECT)
    assert [s["n"] for s in data["steps"]] == [s["n"] for s in STEPS]
    for s in data["steps"]:
        assert set(s) >= {"n", "title", "kind", "studies", "state", "why", "in", "out", "day"}
        assert s["state"] in STATES and s["why"], s
    by = {s["n"]: s for s in data["steps"]}
    assert by["8"]["state"] == "done" and (by["8"]["in"], by["8"]["out"]) == (200, 96)
    assert data["blind"]["sealed"] is False and data["blind"]["done"] == ["17", "18", "19"]
    assert data["oos2"]["looks"] > 0 and not data["oos2"]["virgin"]
    assert data["oos2"]["allowed"] is None
    return data


def test_unknown_project() -> None:
    """A project nothing knows: no crash, 1-3 missing, 20 blocked by the gate's own sentence."""
    data = route("Test_no_such_project")
    by = {s["n"]: s for s in data["steps"]}
    assert by["1"]["state"] == "missing" and by["5"]["state"] == "missing"
    assert by["20"]["state"] == "blocked" and "ciego" in by["20"]["why"]


def test_seal() -> None:
    """While the door is shut a finished 17 is an envelope without numbers; 18.5 is not blind."""
    ctx = {"blind": {"sealed": True, "done": ["17"], "text": "faltan [18, 19]"}}
    done = derive.step("done", "wfc: rho 0.25", 2, 2, "2026-09-26")
    sealed = derive.seal({"n": "17"}, done, ctx)
    assert sealed["state"] == "sealed" and sealed["in"] is None and "rho" not in sealed["why"]
    assert derive.seal({"n": "18.5"}, done, ctx) is done
    assert derive.seal({"n": "18"}, derive.step("pending", "x"), ctx)["state"] == "pending"
    on_disk = derive.seal({"n": "18"}, done, ctx)
    assert on_disk["state"] == "sealed" and "backfill" in on_disk["why"]


def test_widget(data: dict) -> None:
    """The rail draws the real project, a click emits the step, and two grabs are saved."""
    from ui.desktop.theme import QSS
    from ui.desktop.workflow.rail import WorkflowRail
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(QSS)
    SHOTS.mkdir(parents=True, exist_ok=True)
    rail = WorkflowRail()
    rail.project = PROJECT
    rail.resize(440, 1680)
    rail.show_workflow(data)
    opened = []
    rail.open_step.connect(opened.append)
    rail.rows[7].mouseReleaseEvent(None)
    assert opened and opened[0]["n"] == "8" and rail.rows[7].chosen
    assert "Paso 8" in rail.rows[7].toolTip()
    rail.show()
    app.processEvents()
    rail.grab().save(str(SHOTS / "C-workflow.png"))
    shut = {**data, "blind": {"sealed": True, "done": ["17", "18"],
                              "text": "faltan [19]"},
            "steps": [{**s, "state": "sealed", "in": None, "out": None}
                      if s["n"] in ("17", "18") else
                      {**s, "state": "running"} if s["n"] == "19" else
                      {**s, "state": "blocked"} if s["n"] == "20" else s
                      for s in data["steps"]]}
    rail.show_workflow(shut)
    app.processEvents()
    rail.grab().save(str(SHOTS / "C-workflow-sealed.png"))


if __name__ == "__main__":
    real = test_route()
    test_unknown_project()
    test_seal()
    test_widget(real)
    print("ok")
