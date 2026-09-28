#!/usr/bin/env python3
"""Start the app: bring the daemon up if it is not, then open the window."""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from core.paths import ROOT, UI_PORT
from ui.daemon import version
from ui.desktop import client
from ui.desktop.shell import Shell
from ui.desktop.theme import QSS

SHOT_MS = 2500      # the zones read the daemon when built; this lets the last paint land


def replace_stale(port: int, info: dict) -> None:
    """Stop a daemon that runs older code than the checkout, unless it is working.

    Args:
        port: Its port.
        info: Its /api/health body.

    A daemon outlives its window by design, so after an update the shortcut used to
    reach one from before it and the window died on the first route it lacked (📓
    2026-09-26: a daemon from the day before, 404 on /api/catalogue).
    """
    if info.get("busy"):
        refuse(f"El demonio del puerto {port} corre código anterior a esta versión y tiene "
               f"{info['busy']} trabajo(s) en marcha. Vuelve a abrir la ventana cuando "
               f"terminen: entonces se reinicia solo.")
    if "pid" not in info:
        refuse(f"El demonio del puerto {port} es de una versión que no dice su pid. "
               f"Páralo a mano (ps -ef | grep ui.daemon.serve, kill <pid>) y vuelve a abrir.")
    os.kill(info["pid"], signal.SIGTERM)
    for _ in range(40):
        if not client.awake(port):
            return
        time.sleep(0.25)
    refuse(f"El demonio viejo (pid {info['pid']}) no se paró. Páralo a mano y vuelve a abrir.")


def refuse(text: str) -> None:
    """Say why the window cannot open, in a dialog — a desktop shortcut has no terminal.

    Args:
        text: The sentence for the owner.
    """
    QMessageBox.critical(None, "AlgoProject", text)
    raise SystemExit(text)


def ensure_daemon(port: int) -> subprocess.Popen | None:
    """Make sure exactly one daemon is answering on this port.

    Args:
        port: Loopback port the window will talk to.

    Returns:
        The process started, or None when one running the same code was already up — a
        daemon someone else started is left alone and never killed on exit, because two
        windows sharing one daemon is the normal case. Only a daemon on older code, and
        idle, is replaced (`replace_stale`).
    """
    info = client.health(port)
    if info and info.get("code") == version.fingerprint():
        return None
    if info:
        replace_stale(port, info)
    proc = subprocess.Popen([sys.executable, "-m", "ui.daemon.serve", "--port", str(port)],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if client.awake(port):
            return proc
        time.sleep(0.25)
    raise SystemExit(f"el demonio no respondió en el puerto {port}. Arráncalo a mano con "
                     f"python3 -m ui.daemon.serve para ver el error")


def shoot(window: Shell, folder: Path, zone: str) -> None:
    """Save the window as it looks now and close the app — every front's evidence.

    Args:
        window: The open window.
        folder: Where the PNG goes; created if absent.
        zone: The zone on screen, which names the file.
    """
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{zone.replace(' ', '_').replace('/', '-')}.png"
    window.grab().save(str(path))
    print(path)
    QApplication.quit()


def main() -> None:
    """Open the window and run until it is closed."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zone", default="Cobertura",
                    help="la zona que se abre al arrancar, por su nombre en la barra lateral")
    ap.add_argument("--port", type=int, default=UI_PORT,
                    help=f"el puerto del demonio (por defecto {UI_PORT}); otro para no tocar el "
                         "de la ventana del dueño")
    ap.add_argument("--shot", type=Path, metavar="DIR",
                    help="guarda una captura PNG de la ventana en esa carpeta y sale")
    args = ap.parse_args()

    app = QApplication(sys.argv)
    owned = ensure_daemon(args.port)
    client.aim(args.port)
    app.setApplicationName("AlgoProject")
    # The same icon the menu entry uses, so the taskbar and alt-tab show it too.
    app.setWindowIcon(QIcon(str(Path(__file__).with_name("icon-256.png"))))
    app.setStyleSheet(QSS)
    window = Shell()
    window.open_zone(args.zone)
    window.show()
    if args.shot:
        QTimer.singleShot(SHOT_MS, lambda: shoot(window, args.shot, args.zone))
    code = app.exec()
    if owned:
        owned.terminate()
    sys.exit(code)


if __name__ == "__main__":
    main()
