"""The Ctrl+K palette offscreen over the whole daemon in-process: matching, the four ways out, recents."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtCore import QSettings, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QLineEdit  # noqa: E402

from core.paths import ROOT  # noqa: E402
from ui.daemon.loader import state as loadstate  # noqa: E402
from ui.daemon import jobs, tasklog  # noqa: E402
from ui.daemon.app import APP  # noqa: E402
from ui.desktop import client, cmdrank  # noqa: E402
from ui.desktop.selection import SELECTION  # noqa: E402
from ui.desktop.shell import Shell  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

PROJECT, DATABANK, STRATEGY = "Test_USDJPY_donchianUpperCrossUp_M30", "Results", "Strategy 1.15.54"
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"
SCRATCH = tempfile.TemporaryDirectory(prefix="ui-cmdpalette-")
LOADS: list = []     # what the load bar asked the daemon to start


def serve() -> None:
    """Client over the in-process daemon (never port 8765); recents in a throwaway store."""
    http = TestClient(APP)

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
    tasklog.status = lambda role, project: None
    # Choosing a databank queues its loading; here the jobs are written down, never started —
    # two of them would run orderstocsv on the conductor.
    loadstate.jobs = SimpleNamespace(listing=jobs.listing,
                                     start=lambda *a, **k: LOADS.append((a, k)))
    QSettings.setPath(QSettings.NativeFormat, QSettings.UserScope, SCRATCH.name)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, SCRATCH.name)
    cmdrank.STORE = ("AlgoProjectTest", "cmdpalette")


def settle(app: QApplication) -> None:
    """Let queued paints and deleteLater run."""
    for _ in range(5):
        app.processEvents()


def pick(app: QApplication, shell: Shell, query: str) -> None:
    """Open the palette with Ctrl+K, type a query and press Enter."""
    QTest.keyClick(shell, Qt.Key_K, Qt.ControlModifier)
    settle(app)
    assert shell.cmdpalette.isVisible(), "Ctrl+K no abrió la paleta"
    QTest.keyClicks(shell.cmdpalette.field, query)
    QTest.keyClick(shell.cmdpalette.field, Qt.Key_Return)
    settle(app)
    assert not shell.cmdpalette.isVisible()


def test_match() -> None:
    """Subsequence, accent-blind; a tight match outranks a scattered one; non-matches drop;
    «ledger» finds the search log by its alias."""
    m = cmdrank.match
    assert m("busq", "Registro de búsquedas") is not None
    assert m("busquedas", "Búsquedas") == 0
    assert m("xyz", "Proyecto") is None and m("1.15.54", STRATEGY) is not None
    assert m("est", "Estrategia") < m("est", "Registro de búsquedas")
    items = [{"kind": "zone", "label": z, "also": cmdrank.ALIASES.get(z, ())}
             for z in ("En marcha", "Registro de búsquedas", "Proyecto")]
    assert [i["label"] for i in cmdrank.rank("ledger", items, [])] == ["Registro de búsquedas"]


def test_lazy(shell: Shell) -> None:
    """Nothing is read at window start: the daemon is asked only when the palette opens."""
    assert shell.cmdpalette.items == [] and shell.cmdpalette.catalogue == []


def test_zone(app: QApplication, shell: Shell) -> None:
    """A zone by an alias, through open_zone: the stack and the sidebar agree."""
    pick(app, shell, "ledger")
    assert shell.stack.currentWidget() is shell.ledger
    assert [n for n, b in shell.nav.items() if b.isChecked()] == ["Registro de búsquedas"]


def test_strategy(app: QApplication, shell: Shell) -> None:
    """A strategy of the chosen databank: SELECTION gets name and identity, Estrategia opens."""
    SELECTION.choose(project=PROJECT, databank=DATABANK)
    pick(app, shell, "1.15.54")
    assert SELECTION.now["strategy"] == STRATEGY and len(SELECTION.now["identity"]) == 64
    assert SELECTION.now["project"] == PROJECT and SELECTION.now["databank"] == DATABANK
    assert shell.stack.currentWidget() is shell.estrategia
    assert shell.estrategia.currentWidget() is shell.ficha
    assert shell.context.crumbs["strategy"].text().startswith(STRATEGY)


def test_study(app: QApplication, shell: Shell) -> None:
    """With a strategy chosen, a one-strategy study opens on its ficha; a population-only one
    is not listed (its result lives in Proyecto's panel)."""
    pick(app, shell, "profitShape")
    assert shell.stack.currentWidget() is shell.estrategia
    assert shell.ficha.page is not None and shell.ficha.page.key == "profitShape"
    QTest.keyClick(shell, Qt.Key_K, Qt.ControlModifier)
    settle(app)
    assert not [i for i in shell.cmdpalette.items
                if i["kind"] == "study" and i["study"] == "gate"]
    QTest.keyClick(shell.cmdpalette.field, Qt.Key_Escape)
    settle(app)


def test_recent_and_escape(app: QApplication, shell: Shell) -> None:
    """The last choices come first, newest on top; Esc closes without going anywhere."""
    QTest.keyClick(shell, Qt.Key_K, Qt.ControlModifier)
    settle(app)
    top = [i["label"] for i in shell.cmdpalette.shown[:3]]
    assert top == ["Forma del beneficio (profitShape)", STRATEGY, "Registro de búsquedas"], top
    assert all(i.get("recent") for i in shell.cmdpalette.shown[:3])
    SHOTS.mkdir(parents=True, exist_ok=True)
    QTest.keyClicks(shell.cmdpalette.field, "1.1")
    settle(app)
    shell.cmdpalette.grab().save(str(SHOTS / "I-palette.png"))
    QTest.keyClick(shell.cmdpalette.field, Qt.Key_Escape)
    settle(app)
    assert not shell.cmdpalette.isVisible() and shell.stack.currentWidget() is shell.estrategia


def test_store_limits() -> None:
    """At most ten recents; a broken store reads as none and never raises."""
    for n in range(14):
        cmdrank.save_recent({"kind": "zone", "label": f"z{n}", "hint": ""})
    got = cmdrank.load_recent()
    assert len(got) == 10 and got[0]["label"] == "z13"
    QSettings(*cmdrank.STORE).setValue(cmdrank.RECENT_KEY, "{roto")
    assert cmdrank.load_recent() == []
    QSettings(*cmdrank.STORE).setValue(cmdrank.RECENT_KEY, json.dumps([]))


def test_text_field_keeps_ctrl_k(app: QApplication, shell: Shell) -> None:
    """A focused text field keeps Ctrl+K (X11 deletes to end of line; offscreen, nothing): no palette."""
    shell.open_zone("Plantillas")
    field = next(f for f in shell.catalogue.findChildren(QLineEdit) if f.isVisible())
    field.setText("abc")
    field.setFocus()
    field.setCursorPosition(1)
    settle(app)
    QTest.keyClick(field, Qt.Key_K, Qt.ControlModifier)
    settle(app)
    assert not shell.cmdpalette.isVisible() and field.text() in ("a", "abc")
    field.clear()


def main() -> None:
    """Run every check and print its time."""
    serve()
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    shell = Shell()
    shell.resize(1440, 900)
    shell.show()
    shell.activateWindow()
    settle(app)
    for test in (test_match, test_lazy, test_zone, test_strategy, test_study,
                 test_recent_and_escape, test_store_limits, test_text_field_keeps_ctrl_k):
        t = time.time()
        test(*(app, shell)[2 - test.__code__.co_argcount:])
        print(f"ok  {test.__name__}  {time.time() - t:.1f} s")


if __name__ == "__main__":
    main()
