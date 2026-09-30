"""The «?» beside every button: the registry's keys, one mark per button that follows it, and —
with `--port P` — every visible enabled button of every zone explained.

    QT_QPA_PLATFORM=offscreen python3 tests/test_ui_helpmark.py              # the mechanism
    QT_QPA_PLATFORM=offscreen python3 tests/test_ui_helpmark.py --port 8772  # + coverage
"""

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]

from PySide6.QtCore import QEvent, QPoint  # noqa: E402
from PySide6.QtGui import QHelpEvent  # noqa: E402
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QPushButton,  # noqa: E402
                               QTabBar, QVBoxLayout, QWidget)

from ui.desktop import helpmark  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402
from ui.text.buttonhelp import help_for, merge, normalise  # noqa: E402


def marks(w: QWidget) -> list:
    """Every mark under a widget."""
    return w.findChildren(helpmark.Mark)


def test_keys() -> None:
    """Signs, counts and quoted names never change the key; a bare sign keeps itself."""
    assert normalise("▶ correr marcados (3)") == "correr marcados"
    assert normalise("▶▶ Correr workflow (hasta la próxima decisión)") == \
        "correr workflow (hasta la próxima decisión)"
    assert normalise("▶ correr los marcados de «Filtros»") == "correr los marcados de"
    assert normalise("cuantiles 0·25·50·75·100 %") == "cuantiles"
    assert normalise("ver los 12 avisos restantes") == "ver los avisos restantes"
    assert normalise("OOS2") == "oos2" and normalise("×") == "×"
    assert help_for("Guardar", ["QFrame", "PaletteBar"]) != help_for("Guardar", ["Detail"])
    assert help_for("Guardar") == "" and help_for("") == ""


def test_marks(app: QApplication) -> None:
    """One mark per button: in its row, or floating right of it in a grid or a column (never a
    grid cell, never a wider button); hidden with it, gone with it."""
    top = QWidget()
    top.resize(700, 300)
    row, grid, column = QHBoxLayout(), QGridLayout(), QVBoxLayout(top)
    known = QPushButton("▶ correr marcados (0)")
    tipped = QPushButton("xyz", toolTip="Hace xyz.")
    silent, nav, flat = QPushButton("sin ayuda"), QPushButton("Cobertura", objectName="nav"), \
        QPushButton("Sección", flat=True, toolTip="t")
    own = QPushButton("abc")
    own.setProperty("help", "Lo que dice su propiedad.")
    for b in (known, tipped, silent, nav, flat):
        row.addWidget(b)
    grid.addWidget(own, 0, 0)
    grid.setColumnStretch(1, 1)
    column.addLayout(row)
    column.addLayout(grid)
    fixed = QPushButton("seguir leyendo")
    fixed.setFixedWidth(160)
    column.addWidget(fixed)
    column.addWidget(QTabBar())
    top.show()
    app.processEvents()
    top.hide()
    top.show()                       # a second show never adds a second mark
    app.processEvents()
    by = {m.button.text(): m for m in marks(top)}
    assert sorted(by) == sorted(["▶ correr marcados (0)", "xyz", "abc", "seguir leyendo"]), by
    assert row.indexOf(by["▶ correr marcados (0)"]) == row.indexOf(known) + 1
    assert grid.count() == 1 and fixed.width() == 160
    for b in (own, fixed):
        assert by[b.text()].isVisible() and by[b.text()].x() > b.geometry().right(), b.text()
    assert by["xyz"].toolTip() == "Hace xyz."
    assert by["abc"].toolTip() == "Lo que dice su propiedad."
    known.hide()
    assert by["▶ correr marcados (0)"].isHidden()
    known.show()
    assert not by["▶ correr marcados (0)"].isHidden()
    tipped.deleteLater()
    for _ in range(2):               # the button, then the mark its `destroyed` scheduled
        app.sendPostedEvents(None, QEvent.DeferredDelete)
    assert len(marks(top)) == 3
    top.deleteLater()


def test_dead_button(app: QApplication) -> None:
    """A tooltip asked of a mark whose button just died must not touch the button (it was a
    segfault: one DeferredDelete pass kills the button, the mark's own deletion still waits)."""
    top = QWidget()
    lay = QHBoxLayout(top)
    button = QPushButton("Leer ahora")
    lay.addWidget(button)
    top.show()
    app.processEvents()
    mark = marks(top)[0]
    button.deleteLater()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    QApplication.sendEvent(mark, QHelpEvent(QEvent.ToolTip, QPoint(2, 2), QPoint(2, 2)))
    assert mark.button is None
    top.deleteLater()


def test_reparent(app: QApplication) -> None:
    """A marked button moved to another parent keeps one «?», next to it in the new place."""
    first, second = QWidget(), QWidget()
    one, two = QHBoxLayout(first), QHBoxLayout(second)
    button = QPushButton("Leer ahora")
    one.addWidget(button)
    first.show()
    second.show()
    app.processEvents()
    two.addWidget(button)            # reparents it to `second`
    button.show()
    for _ in range(2):
        app.processEvents()
        app.sendPostedEvents(None, QEvent.DeferredDelete)
    assert not marks(first) and len(marks(second)) == 1, (marks(first), marks(second))
    orphan = QPushButton("Leer ahora")
    orphan.setParent(None)
    orphan.show()                    # a top-level button: no parent, no mark, no exception
    app.processEvents()
    for w in (first, second, orphan):
        w.deleteLater()


def test_merge() -> None:
    """A tooltip that nearly copies the sentence is said once; one that adds something, twice."""
    said = help_for("Retirar")
    assert merge(said, "Mueve el fichero a assets/symbols/_retired/. Deja de contar para "
                       "`core.assets`, pero no se pierde.") == said
    assert merge("Hace a.", "Apagado: falta el proyecto.") == "Hace a.\n\nApagado: falta el proyecto."


def test_coverage(app: QApplication, port: int) -> None:
    """Walk every zone as uiwalk does; every visible enabled button must say what it does."""
    import uiwalk
    uiwalk.aim(port)
    uiwalk.trap()
    from ui.desktop.nav import ZONES
    from ui.desktop.shell import Shell
    shell = Shell()
    shell.resize(1920, 1050)
    shell.show()
    bare: dict[str, str] = {}
    settle = uiwalk.settle

    def look(a: QApplication, seconds: float) -> None:
        """Settle as uiwalk does, then note every button on screen with nothing to say."""
        settle(a, seconds)
        for b in shell.findChildren(QPushButton):
            if b.isVisible() and b.isEnabled() and not helpmark.skipped(b) and \
                    not helpmark.text_of(b):
                bare.setdefault(f"«{b.text()}» en {' › '.join(helpmark.scopes(b)[:3])}",
                                uiwalk.HERE["zone"])

    uiwalk.settle = look
    for zone in ZONES:
        uiwalk.walk(shell, app, zone, "Test_USDJPY_donchianUpperCrossUp_M30")
    sys.excepthook = sys.__excepthook__     # uiwalk's hook would swallow the assertion below
    counted = [b for b in shell.findChildren(QPushButton) if not helpmark.skipped(b)]
    print(f"    {len(counted)} botones vivos al final, {len(marks(shell))} con «?», "
          f"{len(uiwalk.ERRORS)} excepciones")
    assert not bare, "sin ayuda:\n" + "\n".join(f"  {k} (zona {z})" for k, z in bare.items())


def main() -> None:
    """Run the checks; the coverage walk only with a scratch daemon's port."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, help="un demonio de pruebas, nunca el 8765 del dueño")
    args = ap.parse_args()
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    helpmark.install(app)
    test_keys()
    print("ok  test_keys")
    for test in (test_marks, test_dead_button, test_reparent):
        test(app)
        print(f"ok  {test.__name__}")
    test_merge()
    print("ok  test_merge")
    if args.port:
        test_coverage(app, args.port)
        print("ok  test_coverage")
    else:
        print("--  test_coverage: sin --port, no se recorre la ventana")
    sys.stdout.flush()
    os._exit(0)          # the walk's reader threads may still be waiting on the daemon


if __name__ == "__main__":
    main()
