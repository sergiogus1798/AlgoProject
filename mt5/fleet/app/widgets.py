"""The Qt pieces every tab of MetaTracker is made of: cells, tables, cards, legends, scrolling pages."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QLabel, QScrollArea,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from mt5.fleet.app import fmt, theme


def cell(text: str, colour: str | None = None, right: bool = True) -> QTableWidgetItem:
    """A read-only table cell, right-aligned unless told otherwise."""
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignVCenter | (Qt.AlignRight if right else Qt.AlignLeft))
    if colour:
        item.setForeground(QColor(colour))
    return item


def signed(x: float | None) -> QTableWidgetItem:
    """A profit or loss, green or red; a dash for None."""
    if x is None:
        return cell(fmt.DASH)
    return cell(fmt.money(x), theme.GAIN if x > 0 else theme.LOSS if x < 0 else None)


def table(columns: list[str], stretch: str) -> QTableWidget:
    """An empty read-only table with these headers; the `stretch` column takes the width left over."""
    t = QTableWidget(0, len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.verticalHeader().hide()
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionMode(QAbstractItemView.NoSelection)
    t.setFocusPolicy(Qt.NoFocus)
    t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    t.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.horizontalHeader().setSectionResizeMode(columns.index(stretch), QHeaderView.Stretch)
    return t


def fill(t: QTableWidget, lines: list[list[QTableWidgetItem]]) -> None:
    """Replace a table's rows and size the table to them."""
    t.setRowCount(len(lines))
    for i, line in enumerate(lines):
        for j, item in enumerate(line):
            t.setItem(i, j, item)
    t.setFixedHeight(t.horizontalHeader().height() + sum(t.rowHeight(i) for i in range(len(lines))) + 6)


def label(text: str, name: str, wrap: bool = False) -> QLabel:
    """A label with a stylesheet name (`section`, `notes`, `empty`, `legend`…)."""
    w = QLabel(text)
    w.setObjectName(name)
    w.setWordWrap(wrap)
    w.setTextFormat(Qt.RichText)
    return w


def card(name: str) -> tuple[QFrame, QLabel]:
    """A bordered card with a small name over a big value; returns the card and the value label to set."""
    frame, value = QFrame(), QLabel(fmt.DASH)
    frame.setObjectName("card")
    value.setObjectName("cardvalue")
    title = QLabel(name)
    title.setObjectName("cardname")
    box = QVBoxLayout(frame)
    box.setContentsMargins(16, 10, 16, 10)
    box.addWidget(title)
    box.addWidget(value)
    return frame, value


def strip(cards: list[QFrame]) -> QWidget:
    """A row of cards."""
    row, box = QWidget(), QHBoxLayout()
    box.setContentsMargins(0, 0, 0, 0)
    for c in cards:
        box.addWidget(c)
    row.setLayout(box)
    return row


def page(parts: list[QWidget], legend: str) -> tuple[QScrollArea, QVBoxLayout]:
    """A scrolling tab page: the parts, a stretch, then the legend at the bottom.

    Returns:
        The scroll area to add to the tabs, and the layout its parts live in.
    """
    inner, box = QWidget(), QVBoxLayout()
    box.setContentsMargins(14, 10, 14, 14)
    for p in parts:
        box.addWidget(p)
    box.addStretch(1)
    box.addWidget(label(legend, "legend", wrap=True))
    inner.setLayout(box)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(inner)
    return scroll, box
