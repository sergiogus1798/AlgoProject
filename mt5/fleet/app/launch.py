"""Open MetaTracker, the window over the live MT5 fleet, or save a capture of it."""

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core import fleetpaths


def main() -> None:
    """`python3 -m mt5.fleet.app.launch [--root DIR] [--tab NAME] [--account LOGIN] [--shot PNG] [--at EPOCH]`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--shot", help="save the window to this PNG and exit, without notifications"
    )
    ap.add_argument(
        "--at", type=int, help="read the fleet as of this UTC epoch instead of now"
    )
    ap.add_argument(
        "--root",
        help="read the fleet tree from this folder instead of AlgoData/fleet (a fixture)",
    )
    ap.add_argument(
        "--tab",
        default="Flota",
        help="open on this tab: Flota, Estrategias, Despliegue, Salud, Conciliación",
    )
    ap.add_argument(
        "--account",
        type=int,
        help="the login to choose in the Flota tab (for a capture)",
    )
    args = ap.parse_args()
    if args.root:
        fleetpaths.FLEET = Path(args.root).resolve()
    from mt5.fleet.app.window import (
        Tracker,
    )  # after the root: nothing reads the tree before this line

    app = QApplication(sys.argv[:1])
    app.setApplicationName("MetaTracker")
    app.setDesktopFileName("metatracker")
    window = Tracker(
        at=args.at, notify=not args.shot, tab=args.tab, account=args.account
    )
    window.show()
    if args.shot:
        app.processEvents()
        window.fit()
        app.processEvents()
        window.grab().save(args.shot)
        return
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
