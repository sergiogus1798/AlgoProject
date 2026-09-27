"""The whole window offscreen over the whole daemon in-process: every zone, the context bar, the signals."""

import os
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtWidgets import QApplication, QTabWidget  # noqa: E402

from core.paths import ROOT  # noqa: E402
from ui.daemon.loader import state as loadstate  # noqa: E402
from ui.daemon import jobs, tasklog  # noqa: E402
from ui.daemon.app import APP  # noqa: E402
from ui.desktop import client  # noqa: E402
from ui.desktop.matrix.model import FIXED  # noqa: E402
from ui.desktop.nav import ZONES  # noqa: E402
from ui.desktop.selection import SELECTION  # noqa: E402
from ui.desktop.shell import Shell  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

PROJECT, DATABANK = "USDJPY_workflow_profiling_v1", "Results"
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"
SCRATCH = tempfile.TemporaryDirectory(prefix="ui-shell-")
LOADS: list = []     # what the load bar asked the daemon to start


def serve() -> None:
    """Point the window's client at the real daemon app in-process.

    Never port 8765 and never bin/algoui: the owner may have the app open. The one call that
    could reach an install (`tasklog.status`, the generation zone's live line) is stubbed out.
    """
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


def settle(app: QApplication) -> None:
    """Let queued paints and deleteLater run."""
    for _ in range(5):
        app.processEvents()


def shot(shell: Shell, name: str) -> None:
    """Save a grab of the whole window for a person to look at."""
    SHOTS.mkdir(parents=True, exist_ok=True)
    shell.grab().save(str(SHOTS / f"G-{name}.png"))


def slug(zone: str) -> str:
    """A zone name as a file name."""
    return zone.lower().replace(" ", "-").replace("/", "").replace("ó", "o").replace("í", "i")


def test_every_zone(app: QApplication, shell: Shell) -> None:
    """Each sidebar entry opens its own page and marks only its own button."""
    for zone in ZONES:
        shell.open_zone(zone)
        settle(app)
        assert shell.stack.currentWidget() is shell.zones[zone], zone
        assert [n for n, b in shell.nav.items() if b.isChecked()] == [zone]


def test_matrix_to_strategy(app: QApplication, shell: Shell) -> None:
    """Pickers → SELECTION → context bar; a cell opens the strategy page on that study."""
    shell.open_zone("Población")
    settle(app)
    m = shell.population
    m.project.setCurrentIndex(m.project.findData(PROJECT))
    m.project.activated.emit(m.project.currentIndex())
    m.databank.setCurrentIndex(m.databank.findData(DATABANK))
    m.databank.activated.emit(m.databank.currentIndex())
    settle(app)
    assert SELECTION.now["project"] == PROJECT and SELECTION.now["databank"] == DATABANK
    assert m.model.rowCount() > 0, "la matriz de Results salió vacía"
    # Choosing the databank asked for its data: every piece it lacks was queued, the ones
    # that need SQX on the conductor lane, and the chips say where each stands.
    queued = {a[2]["loader"]: k["lane"] for a, k in LOADS}
    assert queued, "elegir el databank no pidió cargar nada"
    assert all(queued[p] == "conductor" for p in ("trades", "harvest") if p in queued), queued
    chips = shell.context.load.chips
    assert all(chips[p].text() for p in chips), {p: c.text() for p, c in chips.items()}
    shot(shell, "poblacion")
    shell.open_zone("Workflow")
    settle(app)
    shot(shell, "workflow")

    col = len(FIXED)                                  # the first study column
    key = m.model.field(col)
    # The databank's files add rows no study has judged yet; the two compared here have one.
    judged = [r for r in range(m.model.rowCount()) if m.model.state(r, key) != "missing"]
    assert len(judged) > 1, judged
    m.cell_clicked(m.model.index(judged[0], col))
    settle(app)
    chosen = m.model.strategy(judged[0])
    assert SELECTION.now["identity"] == chosen["identity"]
    assert shell.stack.currentWidget() is shell.strategy and shell.strategy.key == key
    assert shell.context.crumbs["strategy"].text().startswith(chosen["strategy"])
    shot(shell, "estrategia")
    side = shell.strategy.history
    while not isinstance(side, QTabWidget):
        side = side.parentWidget()
    side.setCurrentIndex(1)                           # «historial y comparar»
    rival = m.model.strategy(judged[1])
    shell.strategy.versus(rival["strategy"], rival["identity"])
    settle(app)
    assert len(shell.strategy.view.results) == 2, shell.strategy.note.text()
    shot(shell, "estrategia-comparar")
    side.setCurrentIndex(0)
    shell.strategy.load()

    m.header_clicked(col)
    settle(app)
    assert shell.stack.currentWidget() is shell.popstudy and shell.popstudy.key == key
    shot(shell, "estudio-de-poblacion")

    shell.open_zone("Estrategia")
    shell.strategy.population_wanted.emit("crossmarket")
    assert shell.stack.currentWidget() is shell.popstudy and shell.popstudy.key == "crossmarket"


def test_rail_and_crumbs(shell: Shell) -> None:
    """A step with studies opens its first on the population page; one without, the matrix.
    Each crumb opens its zone."""
    shell.rail.open_step.emit({"n": "8", "studies": ["gate", "isOos"]})
    assert shell.stack.currentWidget() is shell.popstudy and shell.popstudy.key == "gate"
    shell.rail.open_step.emit({"n": "7", "studies": []})
    assert shell.stack.currentWidget() is shell.population
    for crumb, zone in (("project", "Workflow"), ("databank", "Población"),
                        ("strategy", "Estrategia")):
        shell.context.crumbs[crumb].click()
        assert shell.stack.currentWidget() is shell.zones[zone], crumb


def test_grabs(app: QApplication, shell: Shell) -> None:
    """One grab per zone the selection does not change, for a person to look at."""
    for zone in ZONES:
        if zone in ("Población", "Workflow", "Estrategia", "Estudio de población"):
            continue
        shell.open_zone(zone)
        settle(app)
        shot(shell, slug(zone))


def main() -> None:
    """Run every check and print its time."""
    serve()
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    t = time.time()
    shell = Shell()
    shell.resize(1440, 900)
    shell.show()
    print(f"ok  Shell()  {time.time() - t:.1f} s")
    for test in (test_every_zone, test_matrix_to_strategy, test_rail_and_crumbs, test_grabs):
        t = time.time()
        test(*(app, shell)[2 - test.__code__.co_argcount:])
        print(f"ok  {test.__name__}  {time.time() - t:.1f} s")


if __name__ == "__main__":
    main()
