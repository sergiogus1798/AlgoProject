"""Any assets/ file as a table of its values, each one beside what the file says about it."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem)

from ui.desktop.assetforms import TextBox
from ui.desktop.theme import C

# Past this, a value stops being a cell and becomes a paragraph: a `why` or a note is
# edited in a box, not squeezed into a column.
LONG = 60


class YamlTree(QTableWidget):
    """One file's editable values, in file order, with its own comments as the explanation."""

    edited = Signal(str, list, str, str)   # file name, path, what was typed, kind

    def __init__(self) -> None:
        """Build the three columns and wire the two ways of editing a value."""
        super().__init__(0, 3)
        self.name, self.leaves, self.filling = "", [], False
        self.setHorizontalHeaderLabels(["campo", "valor", "qué dice el fichero"])
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setWordWrap(True)
        head = self.horizontalHeader()
        head.setSectionResizeMode(0, QHeaderView.Interactive)
        head.setSectionResizeMode(1, QHeaderView.Interactive)
        head.setSectionResizeMode(2, QHeaderView.Stretch)
        # Fixed and not sized to content: a path like `money_management / params / ATRMult`
        # would take half the width and squeeze out the explanation, which is the column
        # that makes this table worth reading.
        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 240)
        self.itemChanged.connect(self.on_typed)
        self.cellDoubleClicked.connect(self.on_open)

    def fill(self, name: str, leaves: list[dict]) -> None:
        """Draw one file.

        Args:
            name: The file's short name, sent back with every edit.
            leaves: What `assetyaml.leaves` found, in file order.
        """
        self.filling = True
        self.name, self.leaves = name, leaves
        self.setRowCount(len(leaves))
        for i, leaf in enumerate(leaves):
            where = QTableWidgetItem(" / ".join(leaf["path"]))
            where.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            where.setForeground(Qt.GlobalColor.gray if len(leaf["path"]) > 1 else
                                where.foreground())
            self.setItem(i, 0, where)

            value = QTableWidgetItem(shown(leaf))
            if not editable(leaf):
                value.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                value.setToolTip("Doble clic para editarlo en una caja: es una lista o un texto "
                                 "largo, y una celda lo escondería.")
            if leaf["value"] is None:
                value.setForeground(Qt.GlobalColor.gray)
            self.setItem(i, 1, value)

            hint = QTableWidgetItem(leaf["hint"])
            hint.setFlags(Qt.ItemIsEnabled)
            hint.setForeground(Qt.GlobalColor.gray)
            hint.setToolTip(leaf["hint"])
            self.setItem(i, 2, hint)
        self.resizeRowsToContents()
        self.filling = False

    def on_typed(self, item: QTableWidgetItem) -> None:
        """Send a value edited straight in the cell.

        Args:
            item: The cell that changed.
        """
        if self.filling or item.column() != 1:
            return
        leaf = self.leaves[item.row()]
        self.edited.emit(self.name, leaf["path"], item.text(), leaf["kind"])

    def on_open(self, row: int, column: int) -> None:
        """Open the box for a list or a paragraph.

        Args:
            row: Row double-clicked.
            column: Column double-clicked; only the value column opens anything.
        """
        leaf = self.leaves[row]
        if column != 1 or editable(leaf):
            return
        box = TextBox(" / ".join(leaf["path"]), leaf["hint"], shown(leaf),
                      leaf["kind"] == "list")
        if box.exec():
            self.edited.emit(self.name, leaf["path"], box.text(), leaf["kind"])


def shown(leaf: dict) -> str:
    """One value as the table and the box both print it.

    Args:
        leaf: One entry of `assetyaml.leaves`.

    Returns:
        A list as one item per line, `null` for an undecided value — the word the file
        itself uses, so what is on screen is what is on disk — and the text otherwise.
    """
    if leaf["kind"] == "list":
        return "\n".join(str(v) for v in leaf["value"])
    if isinstance(leaf["value"], bool):
        return str(leaf["value"]).lower()   # the file says true/false, not Python's True
    return "null" if leaf["value"] is None else str(leaf["value"])


def editable(leaf: dict) -> bool:
    """Whether this value fits in a cell.

    Args:
        leaf: One entry of `assetyaml.leaves`.

    Returns:
        False for a list and for anything longer than a line, which open the box instead.
    """
    return leaf["kind"] == "scalar" and len(shown(leaf)) <= LONG
