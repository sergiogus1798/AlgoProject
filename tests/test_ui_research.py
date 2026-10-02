#!/usr/bin/env python3
"""«Investigar»: its routes on a local app, the queue with fake steps, the preflight's refusals and
the four views offscreen. No worker, no Claude, no SQX: every step that would reach one is a fake,
and the proposals folder is a temp dir holding the hand-made fixture."""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox

from core.paths import ROOT
from studies.research.board import inputs, many, proposal, store
from ui.daemon.research import api, preflight, proposals, queue, steps
from ui.desktop.research.zone import ResearchZone
from ui.desktop.theme import QSS

SHOTS = Path(os.environ.get("RESEARCH_SHOTS", ROOT / "scratch" / "research-director" / "shots"))
DRAFT = json.loads((Path(__file__).parent / "fixtures" / "research_proposal_draft.json")
                   .read_text(encoding="utf-8"))
TMP = tempfile.TemporaryDirectory()
mock.patch.object(store, "proposals_dir", lambda: Path(TMP.name)).start()
STARTED: list[tuple] = []


def fixture() -> dict:
    """The hand-made proposal, stamped against a one-cell board and saved in the temp dir."""
    for old in Path(TMP.name).glob("*.json"):
        old.unlink()
    cell = {**DRAFT["cell"], "score": 48.0, "lead": "bar3atr", "p": 0.04, "multiple": 26.0,
            "stability": 0.8, "trades_per_year": 60.0, "passes": True, "significant": True,
            "stable": True, "p_raw": 0.001, "needs_clock": False}        # a cell the real map lacks
    board = many.run(pd.DataFrame([cell]), inputs.memory(), inputs.CONFIG)
    p = proposal.stamp(DRAFT, board, datetime(2026, 10, 1, 12))
    proposal.save(p)
    return p


def http() -> TestClient:
    """A local app holding only the research router; never the real daemon."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    return TestClient(app)


def free() -> mock._patch:
    """A machine where the custodian is free, Claude exists and no project is registered."""
    return mock.patch.multiple(
        preflight, advance=mock.Mock(busy=lambda role, project: []),
        launch=mock.Mock(queued=lambda: []), registry=mock.Mock(rows=lambda: []),
        CLAUDE_BIN=Path(sys.executable))


def fakes(log: list, ask: str = "", fail: tuple = ()) -> dict:
    """Five fake steps that only write down what they were asked to run."""
    def step(name: str) -> object:
        """The fake of one step."""
        def run(ctx: dict) -> None:
            """Write the call down; fail or ask where the test said so."""
            log.append((ctx["idea"]["name"], name, ctx["project"]))
            if (ctx["idea"]["name"], name) == fail:
                raise steps.Failed("salió con 1")
            if name == "plantilla":
                if ctx["idea"]["name"] == ask:
                    raise steps.Question("PREGUNTA: ¿banda superior o media?")
                ctx["template"] = ctx["idea"]["name"] + "T"
        return run
    return {name: step(name) for name in queue.ORDER}


def test_routes_read_the_real_profile() -> None:
    """Map, cell, memory and board answer from today's files; the map colours what is on the board."""
    c = http()
    got = c.get("/api/research/map").json()
    assert len(got["symbols"]) == 19 and got["timeframes"] == ["M15", "M30", "H1", "H4"]
    board = c.get("/api/research/board").json()["cells"]
    on = {(x["symbol"], x["timeframe"]) for x in board}
    coloured = {tuple(k.split("|")) for k, v in got["cells"].items() if v["passing"]}
    assert coloured == on                                  # a cell is coloured iff it is on the board
    shown = [p for v in got["cells"].values() for p in v["passing"]]
    assert len(shown) == len(board) and all(p["entered_by"] and p["state"] for p in shown)
    assert all((p["trades_per_year"] is None) == (p["entered_by"] == ["prior"]) for p in shown)
    assert all(v["best"]["family"] for v in got["cells"].values())      # grey cells keep their best
    cell = c.get("/api/research/cell", params={"symbol": "XAUUSD", "timeframe": "H4"}).json()
    assert all(m["explanation"] for m in cell["measures"]) and cell["context"]["cost_over_atr"]
    memory = c.get("/api/research/memory").json()
    assert memory["coverage"]["cells"] == 19 * 4 * 2 * 7 and memory["attempts"]
    assert c.get("/api/research/cell", params={"symbol": "NOPE", "timeframe": "H4"}).json()["measures"] == []


def test_veto_and_answer() -> None:
    """A veto and an answer are written into the proposal and change what may be launched."""
    p, c = fixture(), http()
    shown = c.get("/api/research/proposal").json()
    assert [i["launchable"] for i in shown["ideas"]] == [True, False, True]
    assert "pregunta" in shown["ideas"][1]["why_not"]
    names = [i["name"] for i in p["ideas"]]
    c.post("/api/research/veto", json={"id": p["id"], "idea": names[0], "vetoed": True})
    got = c.post("/api/research/answer", json={"id": p["id"], "idea": names[1], "question": 0,
                                                "text": "Por el rango High-Low"}).json()
    assert [i["launchable"] for i in got["ideas"]] == [False, True, True]
    assert "Respuesta: Por el rango" in (Path(TMP.name) / f"{p['id']}.md").read_text("utf-8")


def test_queue_one_after_another() -> None:
    """Launchable ideas go in order, each through the five steps before the next starts; the
    one with an open question never starts; the project takes the template's real name."""
    p, log, states = fixture(), [], []
    q = queue.run(p, fakes(log), lambda s: states.append(json.loads(json.dumps(s))))
    a, _, c = (i["name"] for i in p["ideas"])
    assert [(n, s) for n, s, _ in log] == [(a, s) for s in queue.ORDER] + [(c, s) for s in queue.ORDER]
    assert log[0][2] == f"Research_XAUUSD_{a}_H4" and log[2][2] == log[4][2] == f"Research_XAUUSD_{a}T_H4"
    assert [i["state"] for i in q["ideas"]] == ["hecha", "pregunta", "hecha"] and q["state"] == "terminada"
    assert max(sum(i["state"] == "en marcha" for i in s["ideas"]) for s in states) == 1
    assert states[0]["ideas"][2]["state"] == "esperando"


def test_queue_question_and_failure() -> None:
    """A question from the template step sets that idea aside and the next goes on; a failure
    halts the queue with the ideas behind it still waiting; a vetoed idea never starts."""
    p, log = fixture(), []
    p["ideas"][1]["questions"][0]["answer"] = "rango"
    a, b, c = (i["name"] for i in p["ideas"])
    q = queue.run(p, fakes(log, ask=a), lambda s: None)
    assert [i["state"] for i in q["ideas"]] == ["pregunta", "hecha", "hecha"]
    assert "banda superior" in q["ideas"][0]["note"] and (a, "proyecto", mock.ANY) not in log
    log.clear()
    q = queue.run(p, fakes(log, fail=(a, "proyecto")), lambda s: None)
    assert [i["state"] for i in q["ideas"]] == ["falló", "esperando", "esperando"]
    assert q["state"] == "parada" and {n for n, _, _ in log} == {a} and q["ideas"][0]["error"]
    p["ideas"][0]["vetoed"] = True
    q = queue.run(p, fakes(log), lambda s: None)
    assert [i["state"] for i in q["ideas"]] == ["vetada", "hecha", "hecha"]


def test_preflight_refusals() -> None:
    """A busy custodian, another launcher, an existing project: each refuses."""
    p = fixture()
    a = p["ideas"][0]["name"]
    with free():
        ok = preflight.check(p["id"])
        assert ok["ok"] and ok["ideas"] == [a, p["ideas"][2]["name"]] and ok["hours"] == 6
        assert "UNA DETRÁS DE OTRA" in ok["text"] and "hasta 30 $" in ok["text"]
        assert "no va: " + p["ideas"][1]["name"] in ok["text"]
        with mock.patch.object(preflight, "registry", mock.Mock(rows=lambda: [
                {"name": f"Research_XAUUSD_{a}_H4", "retired": ""}])):
            assert "ya existe" in " ".join(preflight.check(p["id"])["reasons"])
        with mock.patch.object(preflight, "advance",
                               mock.Mock(busy=lambda r, pr: ["install ocupado: puerto 5070"])):
            assert not preflight.check(p["id"])["ok"]
        with mock.patch.object(preflight, "launch", mock.Mock(queued=lambda: ["ya hay un lanzamiento"])):
            assert not preflight.check(p["id"])["ok"]
        for i in p["ideas"]:
            proposals.veto(p["id"], i["name"], True)
        assert "ninguna idea" in " ".join(preflight.check(p["id"])["reasons"])


def test_launch_route_queues_one_job() -> None:
    """The POST re-checks, refuses a stale confirmation, and queues ONE conductor-lane job."""
    p, c = fixture(), http()
    start = lambda *a, **k: STARTED.append((a, k)) or {"id": "job-1"}  # noqa: E731
    with free(), mock.patch.object(api.jobs, "start", start):
        seen = c.get("/api/research/launch", params={"id": p["id"]}).json()
        stale = c.post("/api/research/launch", json={"id": p["id"],
                                                      "ideas": seen["ideas"][:1]}).json()
        assert not stale["ok"] and not STARTED
        sent = c.post("/api/research/launch", json={"id": p["id"],
                                                     "ideas": seen["ideas"]}).json()
    (label, argv, about), kwargs = STARTED[0]
    assert sent["job"] == "job-1" and len(STARTED) == 1 and label == "launch"
    assert argv == ["-m", "ui.daemon.research.queue", "--proposal", p["id"]]
    assert kwargs == {"lane": "conductor"} and about["role"] == "custodian"
    assert not c.post("/api/research/direct", json={"confirmed": False}).json()["ok"]


def test_views_offscreen() -> None:
    """The four views paint from the routes; a veto in the window reaches the file; the launch
    button asks before it sends, and there is no prefix to choose."""
    p, c = fixture(), http()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    store.write(queue.path(p["id"]), {**queue.initial(p), "ideas": [
        {"name": p["ideas"][0]["name"], "state": "en marcha", "step": "autopilot",
         "project": "Research_XAUUSD_ejemploImpulseBarDown_H4", "error": "", "note": ""},
        {"name": p["ideas"][1]["name"], "state": "pregunta", "step": "", "project": "",
         "error": "", "note": "1 pregunta(s) sin contestar"},
        {"name": p["ideas"][2]["name"], "state": "esperando", "step": "", "project": "",
         "error": "", "note": ""}]})
    sent = []
    with free(), mock.patch.object(api.jobs, "start", lambda *a, **k: sent.append(a) or {"id": "j"}):
        zone = ResearchZone(fetch=lambda path, **q: c.get(f"/api/{path}", params=q).json(),
                            send=lambda path, body: c.post(f"/api/{path}", json=body).json())
        zone.resize(1600, 950)
        zone.show()
        app.processEvents()
        assert zone.map.grid.count() == 4 + 19 * 5
        zone.map.open("XAUUSD", "H4")
        assert zone.map.measures.rowCount() > 30 and zone.map.families.rowCount() == 14
        assert zone.memory.attempts.rowCount() > 0 and zone.direct.board.rowCount() >= 1
        assert zone.proposal.columns.count() == 3 and zone.proposal.queue.rowCount() == 3
        assert zone.proposal.button.isEnabled() and not hasattr(zone.proposal, "prefix")
        SHOTS.mkdir(parents=True, exist_ok=True)
        for n, name in enumerate(("mapa", "memoria", "proponer", "propuesta")):
            zone.tabs.setCurrentIndex(n)
            app.processEvents()
            zone.grab().save(str(SHOTS / f"investigar-{name}.png"))
        zone.proposal.columns.itemAt(2).widget().findChild(QCheckBox).setChecked(True)
        assert proposal.load(p["id"])["ideas"][2]["vetoed"]
        assert zone.proposal.button.isEnabled()
        with mock.patch.object(QMessageBox, "question", lambda *a: QMessageBox.No):
            zone.proposal.launch()
            assert not sent
        with mock.patch.object(QMessageBox, "question", lambda *a: QMessageBox.Yes):
            zone.proposal.launch()
        assert len(sent) == 1 and "--prefix" not in sent[0][1]
        assert "En marcha" in zone.proposal.why.text()


def main() -> None:
    """Run every test in file order."""
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok", name)


if __name__ == "__main__":
    main()
