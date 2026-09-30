"""The rail's run buttons offscreen, the daemon faked: every card can run, and says why when not."""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton  # noqa: E402

from tests.test_chain import rail  # noqa: E402
from ui.daemon.workflow.tests import SPENDS  # noqa: E402
from ui.daemon.launch import chainplan  # noqa: E402
from ui.desktop import client  # noqa: E402

SENT: list[tuple[str, dict]] = []
ASKED: list[str] = []
ANSWER = {"yes": QMessageBox.Yes}
SQX = {"6": {"ok": True, "reasons": [], "titles": ["CONSTRUCCION"]},
       "7": {"ok": False, "reasons": ["«Results» no tiene ninguna estrategia"], "titles": []}}


def fake_daemon(data: dict) -> None:
    """GETs answered from `data`; POSTs recorded and answered with a queued job."""
    def get(path: str, **params: str) -> dict:
        """The routes the rail reads."""
        SENT.append((f"GET {path}", params))
        if path == "workflow":
            return data
        if path == "launch/steps":
            return {"steps": SQX}
        if path == "jobs":
            return {"jobs": []}
        return {"ok": True, "reasons": [], "titles": ["CONSTRUCCION"], "text": "Se va a lanzar"}

    def post(path: str, body: dict) -> dict:
        """Every write the rail sends, answered as the daemon would when it queues."""
        SENT.append((f"POST {path}", body))
        return {"jobs": [{"id": "1"}], "refused": []} if path == "workflow/run" else {
            "job": "1", "titles": ["CONSTRUCCION"]}

    client.get, client.post = get, post
    client.aim = lambda port: None
    QMessageBox.question = staticmethod(lambda *a, **k: ASKED.append(a[1]) or ANSWER["yes"])


def cards(r: object) -> dict[str, object]:
    """The step cards on the rail, by number."""
    return {w.step["n"]: w for w in (r.grid.itemAt(i).widget() for i in range(r.grid.count()))}


def test_buttons() -> None:
    """Python ▶ with nothing ticked runs the step's tests (the bug of 2026-09-28: it posted
    nothing and said «Nada marcado»), leaving out what writes the ledger; ▶ SQX asks, then posts the step; a disabled one shows
    its reason on the card; «Correr workflow» is on with its plan written beside it."""
    from ui.desktop.theme import QSS
    from ui.desktop.workspace.rail import Rail
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(QSS)
    data = rail({"6": "pending", "7": "pending"}, "done")
    for s in data["steps"]:
        s |= {"tab": "", "sub": "", "why": "", "panel": False, "in": None, "out": None}
        for t in s["tests"]:
            t |= {"title": t["key"], "why": "", "config": "", "spends": SPENDS.get(t["key"], ""),
                  "databank": None}
    data |= {"backfill": {"offer": False, "why": ""}, "oos2": {"text": ""},
             "blind": {"sealed": False, "text": ""}, "chain": chainplan.plan(data)}
    fake_daemon(data)
    r = Rail()
    r.load("Test_Fake")
    r.show()
    # The rail reads off the GUI thread (`background.run`): one processEvents raced it and
    # failed about one run in three.
    end = time.monotonic() + 10
    while not r.plan.text() and time.monotonic() < end:
        app.processEvents()
        time.sleep(0.02)
    assert r.chain.isEnabled() and "6 (SQX) → 7 (SQX) → 8" in r.plan.text(), r.plan.text()
    got = cards(r)
    SENT.clear()
    got["8"].findChildren(QPushButton)[0].click()
    assert ASKED == ["Correr el paso 8"], "nothing ticked: it asks before running them all"
    body = next(b for p, b in SENT if p == "POST workflow/run")
    assert [t["key"] for t in body["tests"]] == ["gate", "edgeCost", "feedQuality",
                                                 "spread"], "snoopingScreen writes the ledger"
    six, seven = got["6"].findChildren(QPushButton)[0], got["7"].findChildren(QPushButton)[0]
    assert six.text() == "▶ SQX" and six.isEnabled() and not seven.isEnabled()
    assert "Results" in got["7"].why, got["7"].why
    SENT.clear()
    six.click()
    assert [p for p, _ in SENT][:2] == ["GET launch/preflight", "POST launch/run"], SENT
    assert SENT[1][1] == {"project": "Test_Fake", "step": "6"}, SENT
    SENT.clear()
    ANSWER["yes"] = QMessageBox.No
    r.chain.click()
    assert [p for p, _ in SENT] == ["GET launch/chain"], "«No» must post nothing"


if __name__ == "__main__":
    test_buttons()
    print("ok")
