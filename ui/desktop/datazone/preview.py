"""The Datos zone alone in a window, until the sidebar wires it; `--shot` saves each tab as a PNG and exits."""

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from ui.desktop.datazone.zone import TABS, DataZone
from ui.desktop.theme import QSS

SIZE = (1440, 960)


def shoot(zone: DataZone, folder: Path) -> None:
    """Open every tab in turn, save it as `datos-<n>-<tab>.png`, and quit.

    Args:
        zone: The zone on screen.
        folder: Where the PNGs go; created if absent.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(TABS):
        zone.tabs.setCurrentIndex(i)
        for _ in range(5):
            QApplication.processEvents()
        path = folder / f"datos-{i}-{name.lower().replace(' ', '-')}.png"
        zone.grab().save(str(path))
        print(path)
    QApplication.quit()


def main() -> None:
    """Open the zone; the daemon must already be up (`python3 -m ui.daemon.serve`)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asset", default="XAUUSD", help="el activo que se abre, p. ej. USDJPY")
    ap.add_argument("--tab", default="Catálogo", choices=TABS, help="la pestaña que se abre")
    ap.add_argument("--shot", type=Path, metavar="DIR",
                    help="guarda una captura PNG de cada pestaña en esa carpeta y sale")
    args = ap.parse_args()
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    zone = DataZone()
    zone.resize(*SIZE)
    zone.show()
    zone.open(args.asset, args.tab)
    if args.shot:
        QTimer.singleShot(800, lambda: shoot(zone, args.shot))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
