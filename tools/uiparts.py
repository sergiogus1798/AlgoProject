"""What a person can do to the widgets under one root: the inventory `uiinventory` drives.

Dev-only. Pure introspection: every visible button (checkboxes and «?» marks included), every
item of every combo, every tab, every text or spin input and every item view — rows, header
sections, cells, checkbox cells — as `Item`s with a key that survives the widget being rebuilt
(the tab titles it lives under, its kind, its label), so a repaint does not make it new.
"""

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QModelIndex, QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QAbstractSpinBox, QComboBox, QLineEdit,
                               QStackedWidget, QTabBar, QTabWidget, QWidget)
from shiboken6 import isValid

from ui.desktop.helpmark import Mark

ROWS, CELLS = 40, 120       # rows and cells driven per view
INNER = (QTabBar, QAbstractItemView, QAbstractSpinBox, QComboBox)   # their own buttons and edits are not controls


@dataclass
class Item:
    """One thing a person can do to one widget."""

    key: tuple
    what: str
    act: Callable[[], None]
    widget: QWidget
    nav: bool = False       # a tab: driven after everything else in its scope
    skip: str = ""
    undo: Callable[[], None] | None = None      # run once the view has reacted (a typed probe is taken back)


def columns(model: object) -> int:
    """A model's column count; a list model keeps its own private and has one."""
    try:
        return model.columnCount(QModelIndex())
    except TypeError:
        return 1


def plain(text: str) -> str:
    """A label's text without its HTML or its counter («Carteras (16)» → «Carteras»)."""
    return re.sub(r"\s*\(\d+\)$", "", re.sub(r"<[^>]+>", " ", text or "")).strip()


def scope(w: QWidget) -> tuple:
    """The tab titles a widget lives under, outermost first: the same widget rebuilt keeps its key."""
    out, a = [], w
    while a is not None:
        p = a.parentWidget()
        if isinstance(p, QStackedWidget) and isinstance(p.parentWidget(), QTabWidget):
            out.append(plain(p.parentWidget().tabText(p.parentWidget().indexOf(a))))
        a = p
    return tuple(reversed(out))


def typed(w: QLineEdit, value: str) -> None:
    """Type a probe value as a person would: edited, then Enter."""
    w.setText(value)
    w.textEdited.emit(value)
    w.editingFinished.emit()
    w.returnPressed.emit()


def view_parts(w: QAbstractItemView) -> list[tuple]:
    """Rows, header sections, cells and checkbox cells of one item view."""
    m, parts = w.model(), []
    if m is None:
        return parts
    rows, cols = m.rowCount(QModelIndex()), columns(m)
    name = lambda r: " · ".join(str(m.index(r, c).data() or "") for c in range(min(cols, 2)))[:60]  # noqa: E731
    if w.selectionMode() != QAbstractItemView.NoSelection:
        parts += [(f"fila «{name(r)}»", lambda r=r: w.setCurrentIndex(m.index(r, 0)), "") for r in range(min(rows, ROWS))]
    head = getattr(w, "horizontalHeader", lambda: None)()
    if head is not None and head.isVisible():
        parts += [(f"cabecera «{m.headerData(c, Qt.Horizontal)}»", lambda c=c: QTest.mouseClick(
            head.viewport(), Qt.LeftButton, pos=QPoint(head.sectionViewportPosition(c) + 6, 6)), "") for c in range(cols)]

    def click(r: int, c: int) -> None:
        """Scroll to one cell and click it."""
        w.scrollTo(m.index(r, c))
        QTest.mouseClick(w.viewport(), Qt.LeftButton, pos=w.visualRect(m.index(r, c)).center())

    every = rows * cols <= CELLS
    parts += [(f"celda ({r},{c})", lambda r=r, c=c: click(r, c), "")
              for r in range(rows if every else min(rows, 1)) for c in range(cols)]
    for r in range(min(rows, 3)):
        for c in range(cols):
            if m.index(r, c).data(Qt.CheckStateRole) is not None:     # the flag alone is every QTableWidgetItem's default
                parts.append((f"casilla fila {r}", lambda r=r, c=c: [m.setData(m.index(r, c), s, Qt.CheckStateRole)
                                                                      for s in (Qt.Checked, Qt.Unchecked)], ""))
    if rows > ROWS or not every:
        parts.append(("resto de filas y celdas", lambda: None,
                      f"tope: {rows} filas × {cols} columnas; las no tocadas pasan por el mismo código"))
    return parts


def parts_of(w: QWidget) -> tuple[str, str, list[tuple]]:
    """(kind, label, [(part, act, skip)]) of one widget; no parts when it is not a control."""
    inner = isinstance(w.parentWidget(), INNER) or "QComboBoxPrivate" in type(w.window()).__name__
    tip = plain(w.toolTip())[:40]
    if isinstance(w, Mark):
        def shown() -> None:
            """Click the mark; it must carry a sentence."""
            QTest.mouseClick(w, Qt.LeftButton)
            assert w.toolTip().strip(), "un «?» sin frase de ayuda"
        return "ayuda «?»", plain(w.toolTip())[:40], [("", shown, "")]
    if isinstance(w, QAbstractButton) and not inner:
        return "botón", plain(w.text()) or tip or w.objectName(), [("", w.click, "")]
    if isinstance(w, QComboBox):
        def pick(text: str) -> None:
            """Choose one entry as a person would."""
            w.setCurrentIndex(w.findText(text))
            w.activated.emit(w.currentIndex())
        return "combo", tip, [(f"→ «{t}»", lambda t=t: pick(t), "") for t in [w.itemText(i) for i in range(w.count())]]
    if isinstance(w, QTabBar):
        titles = [plain(w.tabText(i)) for i in range(w.count())]
        go = lambda t: w.setCurrentIndex(next(i for i in range(w.count()) if plain(w.tabText(i)) == t))  # noqa: E731
        return "pestaña", "", [(f"«{t}»", lambda t=t: go(t), "" if w.isTabEnabled(i) else "desactivada")
                               for i, t in enumerate(titles)]
    if isinstance(w, QLineEdit) and not inner:
        old = w.text()
        return "texto", plain(w.placeholderText())[:40] or tip, [
            (f"{name} «{v}»", lambda v=v: typed(w, v), "", lambda: isValid(w) and w.setText(old))
            for name, v in (("vacío", ""), ("basura", "zz 1="))]
    if isinstance(w, QAbstractSpinBox):
        return "número", tip, [("mínimo", lambda: w.setValue(w.minimum()), ""), ("máximo", lambda: w.setValue(w.maximum()), "")]
    if isinstance(w, QAbstractItemView) and not inner:
        m = w.model()
        heads = [str(m.headerData(c, Qt.Horizontal) or "") for c in range(min(columns(m), 3))] if m else []
        return "tabla", "|".join(heads), view_parts(w)
    return "", "", []


def inventory(root: QWidget, skip: tuple = ()) -> list[Item]:
    """Every action on every visible control under `root` (those under a `skip` widget left out)."""
    out, seen = [], Counter()
    for w in [root, *root.findChildren(QWidget)]:
        if not isValid(w) or not w.isVisible() or any(s is w or s.isAncestorOf(w) for s in skip):
            continue
        kind, label, parts = parts_of(w)
        if not parts:
            continue
        base = (scope(w), kind, label)
        n, seen[base] = seen[base], seen[base] + (kind != "pestaña")     # a tab is its title, whichever bar holds it
        for part, act, why, *undo in parts:
            where = " › ".join(scope(w))
            out.append(Item((*base, n, part), f"{where + ' › ' if where else ''}{kind} «{label}» {part}".strip(), act, w,
                            kind == "pestaña", why or ("" if w.isEnabled() else "desactivado"), *undo))
    return out
