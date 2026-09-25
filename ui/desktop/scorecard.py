"""The scorecard: one row per strategy, one column per screen, its value coloured by its pass."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from ui.desktop.theme import C

FIXED = ["estrategia", "murió en", "sobrevive"]


def figure(value: object) -> str:
    """A screen's value as the cell prints it.

    Args:
        value: The scorecard's `<screen>_value`, or None when the strategy never reached it.

    Returns:
        Four significant digits, an empty string for never-reached.
    """
    return "" if value is None else f"{value:.4g}"


class Scorecard(QTableWidget):
    """The population after the cascade, sortable by any screen."""

    picked = Signal(str)   # identity

    def __init__(self) -> None:
        """Build an empty table that announces the selected strategy's identity."""
        super().__init__()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.itemSelectionChanged.connect(self.announce)

    def fill(self, rows: list[dict], screens: list[dict]) -> None:
        """Replace the whole table.

        Args:
            rows: The scorecard's rows.
            screens: The screens, in cascade order, which are the columns after the fixed four.
        """
        names = [s["name"] for s in screens]
        self.setSortingEnabled(False)
        self.clear()
        self.setColumnCount(len(FIXED) + len(names))
        self.setRowCount(len(rows))
        self.setHorizontalHeaderLabels(FIXED + names)
        for j, s in enumerate(screens):
            self.horizontalHeaderItem(len(FIXED) + j).setToolTip(f"{s['kind']} · {s['why']}")
        for i, r in enumerate(rows):
            survives = bool(r["survives"])
            # One name: the retest's, which is the one that goes forward. A strategy SQX
            # dropped from the retest has no name there, so its build name is shown, marked.
            name = r["strategy"] or f"{r['strategy_build']} (SQX la tiró)"
            cells = [name, r["died_at"] or "", "sí" if survives else "no"]
            for j, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, r["identity"])
                item.setToolTip(f"identidad {r['identity']}\nen el build: {r['strategy_build']}")
                if j == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if j == 2:
                    item.setForeground(QColor(C["promising"] if survives else C["dead"]))
                self.setItem(i, j, item)
            for j, name in enumerate(names):
                item = QTableWidgetItem(figure(r[f"{name}_value"]))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item.setToolTip(r[f"{name}_note"] or "")
                passed = r[f"{name}_passed"]
                if passed is not None and r[f"{name}_value"] is not None:
                    item.setForeground(QColor(C["promising"] if passed else C["dead"]))
                self.setItem(i, len(FIXED) + j, item)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        self.setColumnWidth(0, 200)
        self.setSortingEnabled(True)

    def announce(self) -> None:
        """Say which strategy is now selected, by identity."""
        rows = self.selectionModel().selectedRows()
        if rows:
            self.picked.emit(self.item(rows[0].row(), 0).data(Qt.UserRole))

    def only(self, survivors: bool) -> None:
        """Hide the dead, or show everybody.

        Args:
            survivors: True hides every row whose `sobrevive` is «no».
        """
        for i in range(self.rowCount()):
            self.setRowHidden(i, survivors and self.item(i, 2).text() == "no")
