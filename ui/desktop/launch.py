#!/usr/bin/env python3
"""Start the app: bring the daemon up if it is not, then open the window."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.paths import ROOT, UI_PORT
from ui.desktop import client
from ui.desktop.shell import Shell
from ui.desktop.theme import QSS


def ensure_daemon(port: int) -> subprocess.Popen | None:
    """Make sure exactly one daemon is answering on this port.

    Args:
        port: Loopback port the window will talk to.

    Returns:
        The process started, or None when one was already up — a daemon someone else
        started is left alone and never killed on exit, because two windows sharing one
        daemon is the normal case and stopping it would take the library from both.
    """
    if client.awake(port):
        return None
    proc = subprocess.Popen([sys.executable, "-m", "ui.daemon.serve", "--port", str(port)],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if client.awake(port):
            return proc
        time.sleep(0.25)
    raise SystemExit(f"el demonio no respondió en el puerto {port}. Arráncalo a mano con "
                     f"python3 -m ui.daemon.serve para ver el error")


def main() -> None:
    """Open the window and run until it is closed."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zone", default="Cobertura",
                    help="la zona que se abre al arrancar, por su nombre en la barra lateral")
    args = ap.parse_args()

    owned = ensure_daemon(UI_PORT)
    app = QApplication(sys.argv)
    app.setApplicationName("AlgoProject")
    # The same icon the menu entry uses, so the taskbar and alt-tab show it too.
    app.setWindowIcon(QIcon(str(Path(__file__).with_name("icon-256.png"))))
    app.setStyleSheet(QSS)
    window = Shell()
    window.open_zone(args.zone)
    window.show()
    code = app.exec()
    if owned:
        owned.terminate()
    sys.exit(code)


if __name__ == "__main__":
    main()
