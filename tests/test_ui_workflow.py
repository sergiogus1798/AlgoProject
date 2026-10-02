"""The workflow rail, both sides: the route on a real project, the blind door, Proyecto's rail."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtWidgets import QApplication, QPushButton  # noqa: E402

from core.paths import ROOT  # noqa: E402
from ledger import gate  # noqa: E402
from ui.daemon.workflow import derive  # noqa: E402
from ui.daemon.workflow.api import ROUTER  # noqa: E402
from ui.daemon.workflow.steps import STEPS  # noqa: E402

# Since F13 (2026-09-28): the USDJPY Donchian project — 8 done, 17-19 not all run. Retired
# from the custodian on 2026-09-29; its exports and reports stay under the data root.
PROJECT = "Test_USDJPY_donchianUpperCrossUp_M30"
STATES = {"done", "running", "pending", "blocked", "sealed", "missing"}
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"


def route(project: str) -> dict:
    """GET /api/workflow on a daemon holding only this router."""
    app = FastAPI()
    app.include_router(ROUTER)
    r = TestClient(app).get("/api/workflow", params={"project": project})
    assert r.status_code == 200, r.text
    return r.json()


def as_agent(autonomous: bool) -> str | None:
    """Set or clear ALGO_AUTONOMOUS for one test; returns the value to put back."""
    before = os.environ.pop(gate.AUTONOMOUS, None)
    if autonomous:
        os.environ[gate.AUTONOMOUS] = "1"      # the door holds only for an autonomous agent
    return before


def put_back(before: str | None) -> None:
    """Restore ALGO_AUTONOMOUS as it was before `as_agent`."""
    os.environ.pop(gate.AUTONOMOUS, None)
    if before is not None:
        os.environ[gate.AUTONOMOUS] = before


def _route_autonomous() -> dict:
    """`route(PROJECT)` as an autonomous agent — refetched by whichever test needs it (an
    in-process TestClient call is cheap) instead of passed between tests, which only ever
    worked from `__main__`'s own call order (📓 2026-09-30, T1/R UI feedback pass: a bare
    `python3 -m pytest` collected a plain parameter like `data` as a fixture pytest never
    defined, and every dependent test errored at setup)."""
    before = as_agent(True)
    try:
        return route(PROJECT)
    finally:
        put_back(before)


def test_route() -> None:
    """The real project, read as an autonomous agent: every step in WORKFLOW order, the
    contract's keys, the ledger's door. Step 8 is checked by invariants, not by today's
    counts: filters and curations of the live project move its output."""
    check_route(_route_autonomous())


def check_route(data: dict) -> dict:
    """`test_route`'s assertions on one answer."""
    assert [s["n"] for s in data["steps"]] == [s["n"] for s in STEPS]
    for s in data["steps"]:
        assert set(s) >= {"n", "title", "kind", "studies", "state", "why", "in", "out", "day"}
        assert s["state"] in STATES and s["why"], s
    by = {s["n"]: s for s in data["steps"]}
    # Invariants only: a cut, a filter or a curation moves step 8's counts on the live data.
    assert by["8"]["state"] == "done" and 0 < by["8"]["out"] <= by["8"]["in"]
    assert data["blind"]["sealed"] is True and by["20"]["state"] == "blocked"
    assert by["17"]["state"] == "sealed" and by["17"]["in"] is None
    assert data["oos2"]["looks"] > 0 and not data["oos2"]["virgin"]
    assert data["oos2"]["allowed"] is None
    return data


def test_human() -> None:
    """A human (no ALGO_AUTONOMOUS): the door is open, 17 shows its numbers, 20 is not held."""
    before = as_agent(False)
    try:
        data = route(PROJECT)
    finally:
        put_back(before)
    by = {s["n"]: s for s in data["steps"]}
    assert data["blind"]["sealed"] is False, data["blind"]
    assert all(by[n]["state"] != "sealed" for n in ("17", "18", "19"))
    assert by["20"]["why"] != data["blind"]["text"]


def test_unknown_project() -> None:
    """A project nothing knows: no crash, 1-3 missing, 20 blocked — no template in the registry,
    so no Q9 study whose ledger could open the door (`ledgerview.door`)."""
    before = as_agent(True)
    try:
        data = route("Test_no_such_project")
    finally:
        put_back(before)
    by = {s["n"]: s for s in data["steps"]}
    assert by["1"]["state"] == "missing" and by["5"]["state"] == "missing"
    assert by["20"]["state"] == "blocked" and "sin plantilla" in by["20"]["why"]
    assert data["blind"]["sealed"] and data["blind"]["study"] is None


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


def test_widget() -> None:
    """Proyecto's rail draws the real project and its cards, and one grab is saved."""
    data = _route_autonomous()
    from ui.desktop import client
    from ui.desktop.theme import QSS
    from ui.desktop.workspace.rail import Rail
    # Never the owner's daemon: showing the rail polls /api/jobs.
    client.get = lambda path, **params: {"jobs": []} if path == "jobs" else {"error": "sin demonio"}
    client.post = lambda path, body: {"error": "sin demonio"}
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(QSS)
    SHOTS.mkdir(parents=True, exist_ok=True)
    rail = Rail()
    rail.project = PROJECT
    rail.resize(1400, 420)
    rail.fill(data)
    rail.show()
    app.processEvents()
    assert rail.data is data
    rail.grab().save(str(SHOTS / "C-workflow.png"))
    rail.open_step("8")       # several Python tests: «Lanzar todos», and what runs first
    app.processEvents()
    drawer = rail.drawer
    assert drawer.all_button.isVisibleTo(rail) and "Lanzar todos" in drawer.all_button.text()
    assert {t["key"] for t in drawer.batch} <= {t["key"] for t in rail.step("8")["tests"]}
    assert "paso 7" in drawer.needs.text() or "✓ 7" in drawer.needs.text()
    rail.open_step("6")
    assert "Activar el builder" in " ".join(b.text() for b in drawer.findChildren(QPushButton))
    rail.open_step("4")
    assert drawer.note.isVisibleTo(rail) and "PREFLIGHT" in drawer.note.text()


def test_needs() -> None:
    """Every step but the first needs an earlier one, from the project's tasks where it can:
    the OOS retest the build, the cross-market retest the OOS and its judge (8)."""
    data = _route_autonomous()
    by = {s["n"]: s for s in data["steps"]}
    order = [s["n"] for s in data["steps"]]
    assert by["1"]["needs"] == []
    for s in data["steps"][1:]:
        assert s["needs"] and all(order.index(n) < order.index(s["n"]) for n in s["needs"]), s
    assert "6" in by["7"]["needs"] and "8" in by["9"]["needs"]
    assert {"17", "18", "19"} <= set(by["20"]["needs"])
    # From the tasks themselves — a retired project has none to read, so they are given here.
    from ui.daemon.workflow import needs
    tasks = [{"title": "OOS", "input": "Results", "output": "OOS"},
             {"title": "Retest Markets - Family", "input": "OOS",
              "output": "Retest Markets - Family"}]
    spec = next(s for s in STEPS if s["n"] == "9")
    assert {"7", "8"} <= set(needs.of(spec, {"sqx": {"tasks": tasks}}))


def test_project_knobs() -> None:
    """The drawer's knobs are the ones the runner runs: entryQuality's feed is the project's,
    and the cloud's symbol, which the runner now sets too (2026-09-28), is the project's."""
    from ui.daemon.results import forproject
    from ui.daemon.results.api import config
    from ui.daemon import runs
    from ui.daemon.runner import readings
    got = {k["key"]: k for s in config("entryQuality", PROJECT)["sections"] for k in s["knobs"]}
    mine = forproject.facts(PROJECT)
    assert got["run.feed"]["value"] == mine["feed"] and "note" in got["run.feed"]
    argv = readings.entry_quality(runs.context(PROJECT, "CrossTF", "S", mine["symbol"]), "S")
    assert f"run.feed={mine['feed']}" in argv, argv
    cloud = {k["key"]: k for s in config("cloud", PROJECT)["sections"] for k in s["knobs"]}
    assert cloud["run.symbol"]["value"] == mine["symbol"] and "warn" not in cloud["run.symbol"]


if __name__ == "__main__":
    test_human()
    test_route()
    test_unknown_project()
    test_seal()
    test_needs()
    test_project_knobs()
    test_widget()
    print("ok")
