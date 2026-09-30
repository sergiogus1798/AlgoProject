#!/usr/bin/env python3
"""PORTFOLIOS alone in a window, «Importar» opening the archived ficha beside it — until the sidebar wires it."""

import argparse
import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.paths import UI_PORT
from ui.desktop import client, helpmark
from ui.desktop.portfolios.imported import ImportedFicha
from ui.desktop.portfolios.zone import PortfoliosZone
from ui.desktop.studypage.net import fetch
from ui.desktop.theme import QSS

SIZE = (1680, 1050)
WAIT_S = 60          # the ficha's three reads run off the GUI thread; a shot waits for them


def opener(fichas: list) -> callable:
    """The slot `import_requested` is wired to here: a standalone Estrategia window.

    Args:
        fichas: Keeps each window alive, and lets `--shot` find the last one.

    Returns:
        slot(identity, version).
    """
    def open_one(identity: str, version: str) -> None:
        """Read the version's header and open its ImportedFicha in a window of its own."""
        shown = fetch("archive/show", identity=identity, version=version)
        if "error" in shown:
            print(shown["error"], file=sys.stderr)
            return
        ficha = ImportedFicha()
        ficha.setWindowTitle(f"AlgoProject — Estrategia (archivo) — {shown['strategy']}")
        ficha.resize(*SIZE)
        ficha.show()
        ficha.open(shown)
        fichas.append(ficha)
    return open_one


def settle(app: QApplication, ficha: ImportedFicha) -> None:
    """Pump events until the ficha has painted what the daemon answered."""
    end = time.monotonic() + WAIT_S
    while ficha.said.text() and time.monotonic() < end:
        app.processEvents()
        time.sleep(0.05)
    app.processEvents()


def main() -> None:
    """Open the zone, or save the list and the imported ficha with `--shot DIR` and exit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shot", type=Path, help="carpeta donde dejar las PNG y salir")
    parser.add_argument("--identity", default="", help="la estrategia a importar en la captura")
    parser.add_argument("--version", default="", help="su versión; vacío = la más nueva")
    parser.add_argument("--port", type=int, default=UI_PORT, help=f"el del demonio; {UI_PORT} por defecto")
    args = parser.parse_args()
    if not client.health(args.port):
        sys.exit(f"No hay demonio en el puerto {args.port}: arráncalo con "
                 "`python3 -m ui.daemon.serve` o abre la ventana con bin/algoui.")
    client._HTTP.base_url = f"http://127.0.0.1:{args.port}"   # every view reaches it through client
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    helpmark.install(app)     # the «?» beside every button
    zone, fichas = PortfoliosZone(), []
    zone.import_requested.connect(opener(fichas))
    zone.setWindowTitle("AlgoProject — Portfolios")
    zone.resize(*SIZE)
    zone.show()
    app.processEvents()
    if not args.shot:
        return app.exec()
    if not zone.rows:
        sys.exit("El archivo está vacío: no hay nada que importar.")
    zone.pick(args.identity or zone.rows[0]["identity"], args.version)
    app.processEvents()
    args.shot.mkdir(parents=True, exist_ok=True)
    zone.grab().save(str(args.shot / "1-portfolios.png"))
    print(args.shot / "1-portfolios.png")
    zone.go.click()
    settle(app, fichas[-1])
    fichas[-1].grab().save(str(args.shot / "2-importada.png"))
    print(args.shot / "2-importada.png")


if __name__ == "__main__":
    main()
