#!/usr/bin/env python3
"""Walk every zone of the window offscreen against a running daemon and report every exception.

Dev-only. Opens the real `Shell`, visits each zone of `nav.ZONES`, waits for its reads, then
drives what can be driven without writing anything: every combo box through its items, every
tab bar through its tabs, the first rows of every table. Proyecto (and so Databanks) is opened on
a project that has a databank, Estrategia on a strategy double-clicked in Databanks' panel, and
Portfolios' «Importar» on the first archived strategy. Nothing reaches SQX and nothing is written: every POST is
refused here except the pure reads (`POST /api/load` is turned into its GET), and every modal
dialog answers «No». Exits 1 when anything raised.

    QT_QPA_PLATFORM=offscreen python3 tools/uiwalk.py --port 8761
"""

import argparse
import os
import sys
import threading
import time
import traceback
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QInputDialog,  # noqa: E402
                               QMessageBox, QTabBar, QTableWidget)

from ui.desktop import client  # noqa: E402

# POSTs that only read: the aggregate curve of chosen rows, a config's hash, the chat's next
# question. Every other POST writes something (a YAML, a ledger row, a job, a load).
READS = ("databank/equity", "config/hash", "interview/step", "filters/preview")
ITEMS, TABS, WAIT_S = 6, 12, 25     # per combo, per tab bar; seconds a zone may take to read
ERRORS: list[tuple[str, str]] = []
HERE = {"zone": "arranque"}


def aim(port: int) -> None:
    """Point the window's client at the daemon on `port`, with writes refused."""
    client.aim(port)
    get = client.get

    def post(path: str, body: dict) -> dict:
        """Let the reads through; answer every write with an error the views already show."""
        if path == "load":
            return get("load", project=body["project"], databank=body["databank"])
        if path in READS:
            r = client._HTTP.post(f"/api/{path}", json=body)
            r.raise_for_status()
            return r.json()
        return {"error": f"uiwalk: POST /api/{path} no se envía (paseo de solo lectura)"}

    client.post = post


def trap() -> None:
    """Record exceptions from Qt slots and worker threads; make every modal answer «No»."""
    def hook(kind: type, value: BaseException, tb: object) -> None:
        """Keep one exception with the zone it happened in."""
        ERRORS.append((HERE["zone"], "".join(traceback.format_exception(kind, value, tb))))

    sys.excepthook = hook
    threading.excepthook = lambda a: hook(a.exc_type, a.exc_value, a.exc_traceback)
    for name in ("question", "warning", "information", "critical"):
        setattr(QMessageBox, name, staticmethod(lambda *a, **k: QMessageBox.No))
    QMessageBox.exec = lambda *a, **k: QMessageBox.No
    QDialog.exec = lambda *a, **k: 0
    QInputDialog.getText = staticmethod(lambda *a, **k: ("", False))


def settle(app: QApplication, seconds: float) -> None:
    """Pump events for a while, so the zone's threads land and paint.

    A callable queued with `QTimer.singleShot` that raises does not reach `sys.excepthook`:
    PySide raises it out of `processEvents`, so it is caught and recorded here.
    """
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            app.processEvents()
        except Exception as e:  # noqa: BLE001 — every exception is the report's content
            ERRORS.append((HERE["zone"], "".join(traceback.format_exception(e))))
        time.sleep(0.05)


def drive(app: QApplication, zone: object) -> int:
    """Move every visible combo, tab bar and table of one zone; return how many were moved."""
    moved = 0
    for box in [b for b in zone.findChildren(QComboBox) if b.isVisible()]:
        for i in range(min(box.count(), ITEMS)):
            box.setCurrentIndex(i)
            box.activated.emit(i)
            settle(app, 0.3)
        moved += 1
    for bar in [b for b in zone.findChildren(QTabBar) if b.isVisible()]:
        for i in range(min(bar.count(), TABS)):
            if bar.isTabEnabled(i):
                bar.setCurrentIndex(i)
                settle(app, 0.4)
        moved += 1
    for table in [t for t in zone.findChildren(QTableWidget) if t.isVisible()]:
        for r in range(min(table.rowCount(), 3)):
            table.selectRow(r)
            settle(app, 0.1)
        moved += 1
    return moved


def walk(shell: object, app: QApplication, name: str, project: str) -> str:
    """Open one zone, give it its data, drive it; return one line for the report."""
    HERE["zone"] = name
    before = len(ERRORS)
    if name == "Proyecto" and project:
        from ui.desktop.selection import SELECTION
        SELECTION.choose(project=project)
    shell.open_zone(name)
    settle(app, 2)
    moved = 0
    if name == "Estrategia":
        table = shell.workspace.panel.table
        row = next((r for r in range(table.rowCount())
                    if table.rows[table.item(r, 0).data(256)]["identity"]), None)
        if row is not None:
            table.double(row, 0)        # the panel's double click: Databanks → Estrategia
        else:
            ERRORS.append((name, "uiwalk: el panel de Databanks no tiene ninguna fila con "
                                 "identidad; Estrategia no se ha podido abrir"))
        settle(app, WAIT_S)
    elif name == "Portfolios":
        zone = shell.zones[name]
        settle(app, 6)
        moved = drive(app, zone)
        if getattr(zone, "rows", None):
            zone.pick(zone.rows[0]["identity"])
            shell.open_archived(zone.rows[0]["identity"], "")
            settle(app, WAIT_S)
            name += " + importada"
    else:
        settle(app, 6 if name != "Proyectos" else WAIT_S)
    moved += drive(app, shell.stack.currentWidget())
    title = getattr(shell.stack.currentWidget(), "title", None)
    if name.startswith("Estrategia") or name.startswith("Portfolios"):
        title = shell.estrategia.currentWidget().title
    shows = (f" · muestra «{title.text()}»" if title is not None and title.text() else
             f" · la ventana dice «{shell.status.text()}»"
             if name in ("Proyecto", "Estrategia") and shell.status.text() else "")
    return (f"{name:<24} {moved:>3} controles movidos · {len(ERRORS) - before} excepciones"
            + shows)


def main() -> None:
    """Build the window against the daemon, walk every zone, print the report."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, required=True, help="el puerto del demonio a usar")
    ap.add_argument("--project", default="Test_USDJPY_donchianUpperCrossUp_M30",
                    help="el proyecto con el que se abren Proyecto y Estrategia")
    args = ap.parse_args()
    if not client.health(args.port):
        sys.exit(f"No hay demonio en el puerto {args.port}: python3 -m ui.daemon.serve "
                 f"--port {args.port}")
    aim(args.port)
    trap()
    from ui.desktop.nav import ZONES
    from ui.desktop.shell import Shell
    from ui.desktop import helpmark
    from ui.desktop.theme import QSS
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    helpmark.install(app)     # the «?» beside every button
    shell = Shell()
    shell.resize(1600, 1000)
    shell.show()
    settle(app, 1)
    lines = [walk(shell, app, z, args.project) for z in ZONES]
    print("\n".join(lines))
    for zone, text in ERRORS:
        print(f"\n--- {zone}\n{text}", file=sys.stderr)
    print(f"\n{len(ZONES)} zonas, {len(ERRORS)} excepciones", flush=True)
    sys.stderr.flush()
    os._exit(1 if ERRORS else 0)       # worker threads may still be reading: do not wait


if __name__ == "__main__":
    main()
