"""The read-only tables the asset zone draws from — cells, formatting, the shared grid."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from ui.desktop import client
from ui.desktop.assetforms import word
from ui.text.numbers import num
from ui.desktop.theme import C


ROW = 24  # a row of figures, not of prose: the theme's default is half as tall again


def grid(headers: list[str]) -> QTableWidget:
    """An empty table in the house style, as small as what it holds.

    Args:
        headers: Column keys, shown through the glossary.

    Returns:
        A read-only table: every write in this zone goes through a box, never a cell, so a
        stray keystroke cannot change what an instrument costs. No column stretches (owner,
        2026-10-02): `fit` gives the table the width and height of its content.
    """
    t = QTableWidget(0, len(headers), objectName="compact")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
    t.setHorizontalHeaderLabels([word(h) for h in headers])
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setMinimumSectionSize(ROW)
    t.verticalHeader().setDefaultSectionSize(ROW)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    t.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    t.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return t


def cell(text: str, tip: str = "") -> QTableWidgetItem:
    """One cell of text, explaining itself on hover.

    Args:
        text: What it says.
        tip: What it means, defaulting to the text itself so a truncated cell is readable.

    Returns:
        The item.
    """
    item = QTableWidgetItem(text)
    item.setToolTip(tip or text)
    return item


def val(value: object) -> str:
    """One value as the tables print it.

    Args:
        value: Anything the daemon sent.

    Returns:
        «sin decidir» for an undecided value (`null` in the file), the figure through
        `numbers.num` otherwise. A per-segment commission (OPEN #27, 2026-09-29: `{build:
        {method, value}, oos1: …}`) reads as one figure when the three agree, else the three;
        it made the whole window fail to open, since Activos is built at start.
    """
    if isinstance(value, dict):
        legs = {
            seg: (v.get("value"), v.get("method"))
            for seg, v in value.items()
            if isinstance(v, dict)
        }
        if not legs:
            return str(value)
        shown = {
            f"{val(v)}{' %' if m == 'PercentageBased' else ''}"
            for v, m in legs.values()
        }
        return (
            shown.pop()
            if len(shown) == 1
            else " · ".join(
                f"{seg} {val(v)}{' %' if m == 'PercentageBased' else ''}"
                for seg, (v, m) in legs.items()
            )
        )
    return "sin decidir" if value is None else num(value)


def derived(value: float, source: str) -> QTableWidgetItem:
    """A bound the file leaves empty and `core.assets` fills: muted, with where it comes from."""
    item = cell(
        val(value),
        f"El fichero lo deja vacío; el MC Retest usa este: {source}. "
        "Doble clic para declarar otro.",
    )
    item.setForeground(QBrush(QColor(C["muted"])))
    return item


def fit(table: QTableWidget) -> None:
    """Give a table exactly the width its columns and the height its rows need.

    Args:
        table: The table, already filled.

    Returns:
        Nothing. These tables live inside one scroll, so a table with its own scrollbar
        would hide rows behind a second one — and the number of rows is small and known.
    """
    table.resizeColumnsToContents()
    # The header, the rows, and the frame's own two borders plus a hair: short by those and
    # the widget below is drawn over the last row.
    height = table.horizontalHeader().height() + 2 * table.frameWidth() + 4
    table.setFixedHeight(
        height + sum(table.rowHeight(i) for i in range(table.rowCount()))
    )
    table.setFixedWidth(
        2 * table.frameWidth()
        + 4
        + sum(table.columnWidth(j) for j in range(table.columnCount()))
    )


def send(name: str, path: list, text: str) -> None:
    """Write one value of one assets/ file through the daemon.

    Args:
        name: The file: an asset name, or one of the shared four.
        path: The keys leading to the value.
        text: What was typed. Empty means `null`, which is «sin decidir».
    """
    client.post(
        "assets/value",
        {"name": name, "path": [str(k) for k in path], "text": text, "kind": "scalar"},
    )
