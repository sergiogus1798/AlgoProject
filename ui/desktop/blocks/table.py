"""The table block: sortable, numbers printed the window's way, every cell's full text on hover."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from ui.desktop.blocks import chart
from ui.desktop.blocks.card import card, text
from ui.desktop.theme import T

VISIBLE = 16        # rows shown before the table scrolls inside itself
WIDEST = 460        # a column of sentences is cut here; the whole sentence is on hover


class Cell(QTableWidgetItem):
    """A cell that sorts by its value, not by its printed text: «1 200» after «950»."""

    def __init__(self, value: object) -> None:
        """Print the value and keep it for sorting.

        Args:
            value: What the study wrote in the cell.
        """
        super().__init__(chart.num(value) if isinstance(value, (int, float, type(None)))
                         and not isinstance(value, bool) else str(value))
        self.value = value

    def __lt__(self, other: "Cell") -> bool:
        """Numbers before text, missing values last, each group in its own order.

        Args:
            other: The cell compared against.

        Returns:
            Whether this cell sorts first.
        """
        def rank(v: object) -> tuple:
            """A key every cell value can be compared by."""
            if v is None:
                return (2, 0, "")
            if isinstance(v, (int, float)):
                return (0, v, "")
            return (1, 0, str(v))

        return rank(self.value) < rank(other.value)


def widget(block: dict) -> QWidget:
    """One table, sortable by any column.

    Args:
        block: A contract `table` block.

    Returns:
        The framed table; an empty one says so instead of drawing a bare header.
    """
    b = block
    if not b["rows"]:
        return card(b, text("(vacía: el estudio no dejó ninguna fila aquí)", T["faint"]))
    table = QTableWidget(len(b["rows"]), len(b["columns"]))
    table.setHorizontalHeaderLabels([str(c) for c in b["columns"]])
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setWordWrap(False)
    align = b.get("align") or ["left"] * len(b["columns"])
    for i, row in enumerate(b["rows"]):
        for j, v in enumerate(row):
            cell = Cell(v)
            cell.setTextAlignment((Qt.AlignRight if align[j] == "right" else Qt.AlignLeft)
                                  | Qt.AlignVCenter)
            cell.setToolTip(f"{b['columns'][j]}: {v if v is not None else '—'}")
            table.setItem(i, j, cell)
    # Enabling sorting sorts at once by column 0; the study's own order is the reading order.
    table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
    table.setSortingEnabled(True)
    table.resizeColumnsToContents()
    for j in range(len(b["columns"])):
        table.setColumnWidth(j, min(WIDEST, table.columnWidth(j) + 16))
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    # A last column of sentences (the «why», «what it says») takes the spare width, so less
    # of it is cut; a last column of numbers does not, or its figures drift to the far edge.
    table.horizontalHeader().setStretchLastSection(align[-1] == "left")
    table.verticalHeader().setDefaultSectionSize(26)
    shown = min(len(b["rows"]), VISIBLE)
    table.setFixedHeight(table.horizontalHeader().sizeHint().height() + 26 * shown + 6)
    if len(b["rows"]) > VISIBLE:
        table.setToolTip(f"{len(b['rows'])} filas: la tabla se desplaza por dentro; pulsa una "
                         "cabecera para ordenar.")
    return card(b, table)
