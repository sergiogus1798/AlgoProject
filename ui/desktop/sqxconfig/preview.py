#!/usr/bin/env python3
"""The Configuración SQX zone alone in a window, over the running daemon — until the sidebar carries it."""

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.paths import UI_PORT
from ui.desktop import client, helpmark
from ui.desktop.sqxconfig.zone import SqxConfigZone
from ui.desktop.theme import QSS

SIZE = (1680, 1050)
# What the shots open, by section key: the overview folded, then the owner's own example.
SHOTS = {"1-configuracion-sqx.png": None, "2-crosstf.png": "crosstf", "3-mc-retest.png": "mc_retest",
         "4-wfm.png": "wfm", "5-wfc.png": "wfc", "6-cscv.png": "cscv"}


def shoot(zone: SqxConfigZone, app: QApplication, folder: Path) -> None:
    """Save one PNG per entry of SHOTS, unfolding that section alone.

    Args:
        zone: The zone, shown and loaded.
        app: The application, to let each layout settle before the grab.
        folder: Where the PNGs go.
    """
    folder.mkdir(parents=True, exist_ok=True)
    keys = [s.section["key"] for s in zone.sections]
    for name, key in SHOTS.items():
        for s in zone.sections:
            s.head.setChecked(False)
        app.processEvents()
        if key:
            zone.open(keys.index(key))
            app.processEvents()
            zone.open(keys.index(key))
        app.processEvents()
        zone.grab().save(str(folder / name))
        print(folder / name)


def main() -> None:
    """Open the zone, or save its shots with `--shot DIR` and exit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shot", type=Path, help="carpeta donde dejar las PNG y salir")
    parser.add_argument("--port", type=int, default=UI_PORT,
                        help="puerto de un demonio de pruebas; por defecto, el de la ventana")
    args = parser.parse_args()
    client.aim(args.port)
    if not client.health(args.port):
        sys.exit(f"No hay demonio en el puerto {args.port}: arráncalo con "
                 "`python3 -m ui.daemon.serve` o abre la ventana con bin/algoui.")
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    helpmark.install(app)     # the «?» beside every button
    zone = SqxConfigZone()
    zone.setWindowTitle("AlgoProject — Configuración SQX")
    zone.resize(*SIZE)
    zone.show()
    app.processEvents()
    if args.shot:
        shoot(zone, app, args.shot)
        return
    app.exec()


if __name__ == "__main__":
    main()
