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
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.paths import ROOT  # noqa: E402
from ui.daemon.loader import state as loadstate  # noqa: E402
from ui.daemon import jobs, tasklog  # noqa: E402
from ui.daemon.app import APP  # noqa: E402
from ui.desktop import client  # noqa: E402
from ui.desktop.nav import ZONES  # noqa: E402
from ui.desktop.selection import SELECTION  # noqa: E402
from ui.desktop.shell import Shell  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

# The fixture since F13 (2026-09-28): the USDJPY Donchian project, whose Results databank the
# custodian no longer holds — its panel rows come from the cosecha and the reports.
PROJECT, DATABANK = "Test_USDJPY_donchianUpperCrossUp_M30", "Results"
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"
SCRATCH = tempfile.TemporaryDirectory(prefix="ui-shell-")
LOADS: list = []     # what the load bar asked the daemon to start


def serve() -> None:
    """Point the window's client at the real daemon app in-process.

    Never port 8765 and never bin/algoui: the owner may have the app open. The one call that
    could reach an install (`tasklog.status`, En marcha's live line) is stubbed out.
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


# `app`/`shell` used to be plain parameters, only ever filled by `main()` below — a bare
# `python3 -m pytest` collected these as fixtures pytest never defined and every test here
# errored at setup (📓 2026-09-30, T1 UI feedback pass; same fix as `test_ui_studypage.py`).
# Built once at import instead; the tests below still run in file order because that order IS
# the dependency (`test_panel_to_strategy` sets the SELECTION the later ones read).
serve()
QAPP = QApplication.instance() or QApplication(sys.argv)
QAPP.setStyleSheet(QSS)
SHELL = Shell()
SHELL.resize(1440, 900)
SHELL.show()


def test_every_zone() -> None:
    """Each sidebar entry opens its own page and marks only its own button."""
    for zone in ZONES:
        SHELL.open_zone(zone)
        settle(QAPP)
        assert SHELL.stack.currentWidget() is SHELL.zones[zone], zone
        assert [n for n, b in SHELL.nav.items() if b.isChecked()] == [zone]


def wait(app: QApplication, done: object, seconds: float = 60) -> None:
    """Pump events until `done()` is true — the zones read the daemon off the GUI thread."""
    end = time.time() + seconds
    while not done() and time.time() < end:
        app.processEvents()
        time.sleep(0.05)
    settle(app)


def test_panel_to_strategy() -> None:
    """SELECTION → Proyecto fills Databanks too; the drawer's «→ ver en Databanks» opens it on
    the step's tab; a double click there opens Estrategia on that strategy, whose crumb names
    it; the ficha reads the daemon for its three panels."""
    SELECTION.choose(project=PROJECT)
    SHELL.open_zone("Proyecto")
    table = SHELL.workspace.panel.table
    wait(QAPP, lambda: table.rowCount() > 0)
    assert table.rowCount() > 0, "el panel de Databanks salió vacío"
    assert SHELL.workspace.panel.window() is SHELL and SHELL.workspace.databanks.isAncestorOf(
        SHELL.workspace.panel), "el panel de databanks no vive en la zona Databanks"
    shot(SHELL, "proyecto")
    tab = SHELL.workspace.panel.tab()
    SHELL.workspace.see(tab, "")
    assert SHELL.stack.currentWidget() is SHELL.zones["Databanks"]
    assert SHELL.workspace.panel.tab() == tab
    shot(SHELL, "databanks")
    row = next(r for r in range(table.rowCount())
               if table.rows[table.item(r, 0).data(256)]["identity"])
    chosen = table.rows[table.item(row, 0).data(256)]
    table.double(row, 0)
    settle(QAPP)
    assert SHELL.stack.currentWidget() is SHELL.estrategia, SHELL.status.text()
    assert SHELL.estrategia.currentWidget() is SHELL.ficha
    assert SELECTION.now["identity"] == chosen["identity"]
    assert SELECTION.now["databank"] == DATABANK, (SELECTION.now, SHELL.workspace.panel.sub_spec())
    assert SHELL.context.crumbs["strategy"].text() == chosen["name"]
    assert SHELL.ficha.title.text() == chosen["name"]
    wait(QAPP, lambda: not SHELL.ficha.said.text())
    assert SHELL.ficha.page is not None, "la ficha no montó las pestañas de estudios"
    shot(SHELL, "estrategia")


def test_crumbs() -> None:
    """Each crumb opens its zone of PROYECTO."""
    for crumb, zone in (("projects", "Proyectos"), ("project", "Proyecto"),
                        ("strategy", "Estrategia")):
        SHELL.context.crumbs[crumb].click()
        assert SHELL.stack.currentWidget() is SHELL.zones[zone], crumb


def test_portfolios_import() -> None:
    """PORTFOLIOS' «Importar» opens the archived version on Estrategia, SELECTION untouched;
    a live strategy chosen afterwards brings the live ficha back."""
    zone = SHELL.zones["Portfolios"]
    SHELL.open_zone("Portfolios")
    wait(QAPP, lambda: bool(getattr(zone, "rows", None)), 20)
    if not getattr(zone, "rows", None):
        print("    (sin estrategias archivadas en AlgoData/archive: no hay nada que importar)")
        return
    before = dict(SELECTION.now)
    zone.pick(zone.rows[0]["identity"])
    zone.import_requested.emit(zone.rows[0]["identity"], "")
    settle(QAPP)
    assert SHELL.stack.currentWidget() is SHELL.estrategia, SHELL.status.text()
    assert SHELL.estrategia.currentWidget() is SHELL.estrategia.imported
    assert SELECTION.now == before
    wait(QAPP, lambda: not SHELL.estrategia.imported.said.text())
    shot(SHELL, "portfolios-importada")
    SHELL.estrategia.show_live()
    assert SHELL.estrategia.currentWidget() is SHELL.ficha


def test_grabs() -> None:
    """One grab per zone the selection does not change, for a person to look at."""
    for zone in ZONES:
        if zone in ("Proyecto", "Databanks", "Estrategia"):
            continue
        SHELL.open_zone(zone)
        settle(QAPP)
        shot(SHELL, slug(zone))


def main() -> None:
    """Run every check and print its time."""
    for test in (test_every_zone, test_panel_to_strategy, test_crumbs, test_portfolios_import,
                 test_grabs):
        t = time.time()
        test()
        print(f"ok  {test.__name__}  {time.time() - t:.1f} s")


if __name__ == "__main__":
    main()
