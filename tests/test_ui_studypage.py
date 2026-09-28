"""The study page offscreen over the real routes in-process: result, drawer, history, compare,
and with `--run` one real edgeCost run (it writes a report under AlgoData/reports/)."""

import os
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import date
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.paths import ROOT  # noqa: E402
from ui.daemon import jobs, jobsapi  # noqa: E402
from ui.daemon.results import api as results  # noqa: E402
from ui.daemon.runner import api as runner  # noqa: E402
from ui.desktop import client  # noqa: E402
from ui.desktop.selection import SELECTION  # noqa: E402
from ui.desktop.studypage.page import StudyPage  # noqa: E402
from ui.desktop.studypage.views import StrategyPage  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

# Since F13 (2026-09-28): the USDJPY Donchian project; its gate ran on 09-27 and 09-28.
PROJECT, DATABANK, STRATEGY = ("Test_USDJPY_donchianUpperCrossUp_M30", "Results",
                               "Strategy 1.15.54")
RUN = "--run" in sys.argv
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"
SCRATCH = tempfile.TemporaryDirectory(prefix="ui-studypage-")


def serve() -> TestClient:
    """The results, runner and job routes in-process, and the window's client pointed at them.

    Never port 8765 and never bin/algoui: the owner may have the app open.
    """
    app = FastAPI()
    for r in (results.ROUTER, runner.ROUTER, jobsapi.ROUTER):
        app.include_router(r)
    http = TestClient(app)

    def get(path: str, **params: str) -> dict:
        """client.get over the in-process app."""
        got = http.get(f"/api/{path}", params=params)
        got.raise_for_status()
        return got.json()

    def post(path: str, body: dict) -> dict:
        """client.post over the in-process app."""
        got = http.post(f"/api/{path}", json=body)
        got.raise_for_status()
        return got.json()

    client.get, client.post = get, post
    jobs.LOGS = Path(SCRATCH.name)
    return http


def settle(app: QApplication, until: Callable[[], bool], seconds: float) -> None:
    """Run the event loop until a condition holds (the run bar polls on a QTimer)."""
    end = time.time() + seconds
    while not until():
        assert time.time() < end, "timed out"
        app.processEvents()
        time.sleep(0.05)


def shot(widget: object, name: str) -> None:
    """Save a grab for a person to look at."""
    SHOTS.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(SHOTS / f"E-{name}.png"))


def run_one(app: QApplication, page: StrategyPage) -> None:
    """One real edgeCost run of the strategy on screen, the page reloading on its end."""
    page.open_study("edgeCost")
    before = page.meta.get("computed_at") or ""
    page.bar.timer.setInterval(200)
    page.bar.run("one")
    assert page.bar.ids and not page.bar.one.isEnabled(), page.bar.error.text()
    settle(app, lambda: not page.bar.ids, 60)
    assert page.bar.error.text() == "", page.bar.error.text()
    assert page.meta["day"] == date.today().isoformat() and page.meta["computed_at"] >= before
    assert "100%" in page.bar.line.text(), page.bar.line.text()


def test_strategy(app: QApplication, http: TestClient) -> None:
    """Dots, result, drawer signing, compare with a rival; a real edgeCost run with --run."""
    bank = http.get("/api/matrix", params={"project": PROJECT, "databank": DATABANK}).json()
    ident = next(s["identity"] for s in bank["strategies"] if s["strategy"] == STRATEGY)
    SELECTION.choose(project=PROJECT, databank=DATABANK, strategy=STRATEGY, identity=ident,
                     asset=None)
    page = StrategyPage()
    page.resize(1600, 1050)
    assert page.where["asset"] == "USDJPY", page.where
    page.open_study("gate")
    assert page.studies.tabText(page.studies.currentIndex()) == "Puerta IS/OOS"
    assert page.cells["gate"]["state"] in ("pass", "fail") and page.view.results
    assert "elimina" in page.head.text()
    shot(page, "strategy")

    page.open_study("edgeCost")
    knob = page.drawer.editors["verdict.min_edge_spreads"][0]
    knob.setText("3.5")
    knob.editingFinished.emit()
    assert page.drawer.overrides() == ["verdict.min_edge_spreads=3.5"]
    shot(page.drawer, "drawer")
    page.drawer.reset()
    assert page.drawer.overrides() == []

    if RUN:
        run_one(app, page)
    else:
        print("    (sin --run: no se corre edgeCost de verdad; escribiría un informe del día en "
              "AlgoData/reports/ de este proyecto)")

    page.open_study("gate")                  # the gate judged every strategy of the databank
    rival = next(s for s in page.strategies if s["strategy"] != STRATEGY)
    page.history.versus.emit(rival["strategy"], rival["identity"])
    assert len(page.view.results) == 2 and not page.back.isHidden(), page.note.text()
    shot(page, "compare")

    page.open_study("replication")           # the runner refuses it; the catalogue says so
    assert page.bar.one.isHidden() and page.bar.many.isHidden(), page.bar.line.text()
    assert "No se corre desde aquí" in page.bar.line.text()
    page.bar.run("one")                      # pressed anyway: the daemon refuses too
    assert page.bar.error.text() and not page.bar.ids

    page.open_study("falsePositives")
    assert page.bar.one.isHidden() and "aún no existe" in page.bar.line.text()

    page.open_study("crossmarket")           # not run on Results: said, never borrowed
    assert page.view.results == [] and "otro databank" in page.note.text(), page.note.text()

    page.open_study("wfm")
    assert "Proyecto" in page.note.text() or "otro databank" in page.note.text()
    page.deleteLater()


def test_population(app: QApplication) -> None:
    """Scope many on the same databank: the newest gate run, two runs compared, the batch
    studies said honestly. (The population page left the sidebar with F13; the scope stays.)"""
    SELECTION.choose(project=PROJECT, databank=DATABANK)
    page = StudyPage(strategy_page=False)
    page.resize(1600, 1050)
    page.open_study("gate")
    assert page.view.results and page.bar.one.isHidden()
    days = [page.history.runs.item(i).data(Qt.UserRole) for i in range(page.history.runs.count())]
    assert len(days) >= 2, days
    shot(page, "population")
    page.history.compare_runs.emit(days[1], days[0])
    assert len(page.view.results) == 2
    shot(page, "population-compare")
    page.history.picked.emit(days[1])
    assert page.meta["day"] == days[1] and "historial" in page.note.text()
    page.open_study("cloud")
    assert "lote de variantes" in page.note.text(), page.note.text()


if __name__ == "__main__":
    APP = QApplication.instance() or QApplication([])
    APP.setStyleSheet(QSS)
    HTTP = serve()
    for test, args in ((test_strategy, (APP, HTTP)), (test_population, (APP,))):
        started = time.time()
        test(*args)
        print(f"ok  {test.__name__}  {time.time() - started:.1f} s")
