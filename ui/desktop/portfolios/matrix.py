"""The correlation matrix: one cell per pair, coloured in discrete steps against the threshold in force."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QScrollArea,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui.desktop import background
from ui.desktop.blocks.card import text
from ui.desktop.blocks.kinds import draw
from ui.desktop.blocks.states import colour
from ui.desktop.theme import T

CELL, ROW = 78, 44       # big enough to read two decimals from the owner's chair


def chip(state: str, words: str) -> QLabel:
    """One step of the legend: its colour and what it means."""
    label = QLabel(f"  {words}  ")
    label.setStyleSheet(f"background: {colour(state)}; color: {T['bg']}; font-weight: 700; padding: 3px 6px;")
    return label


class Matrix(QWidget):
    """The square table of one pair measure, the diagonal blank, with its legend and meaning.
    A click on a cell calls `on_pair(i, j)` with the two identities."""

    def __init__(self, m: dict, on_pair: Callable[[str, str], None]) -> None:
        """Paint the matrix the daemon sent (`portfolios/module` › `matrix`)."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 10, 4, 4)
        limit = "sin umbral leído" if m["threshold"] is None else (
            f"umbral en vigor {m['threshold']:g}" + (" en valor absoluto" if m["two_sided"] else " (solo por arriba)"))
        lay.addWidget(text(f"{m['measure']} — {limit}", T["text"], 16, True))
        lay.addWidget(text(m["meaning"], T["muted"], 14))
        legend = QHBoxLayout()
        for step in m["steps"]:
            legend.addWidget(chip(step["state"], step["text"]))
        legend.addWidget(text("Haz clic en una celda para ver esa pareja.", T["faint"], 13))
        legend.addStretch(1)
        lay.addLayout(legend)
        n = len(m["ids"])
        short = [label.split(" · ")[0].replace("Strategy ", "") for label in m["labels"]]
        table = QTableWidget(n, n)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setHorizontalHeaderLabels(short)
        table.setVerticalHeaderLabels(short)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)      # the matrix takes the module's width
        table.horizontalHeader().setMinimumSectionSize(CELL)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.verticalHeader().setDefaultSectionSize(ROW)
        bold = QFont()
        bold.setBold(True)
        bold.setPointSize(13)
        for a in range(n):
            table.horizontalHeaderItem(a).setToolTip(m["labels"][a])
            table.verticalHeaderItem(a).setToolTip(m["labels"][a])
            for b in range(n):
                value, state = m["values"][a][b], m["states"][a][b]
                item = QTableWidgetItem("" if value is None else f"{value:+.2f}")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(bold)
                if a != b:
                    item.setToolTip(f"{m['labels'][a]}\n{m['labels'][b]}\n{m['measure']}: "
                                    + ("sin medir (solape insuficiente)" if value is None else f"{value:+.3f}"))
                    item.setBackground(QBrush(QColor(colour(state) if state else T["line"])))
                    item.setForeground(QBrush(QColor(T["bg"] if state else T["text"])))     # no threshold read: plain, readable
                table.setItem(a, b, item)
        table.setMinimumHeight(min(ROW * n + 60, 620))
        table.cellClicked.connect(lambda a, b: a != b and on_pair(m["ids"][a], m["ids"][b]))
        lay.addWidget(table, 1)


class PairDialog(QDialog):
    """One pair of the matrix: both P&L series in build and every measure against its threshold."""

    def __init__(self, parent: QWidget, params: dict) -> None:
        """Open empty and ask `portfolios/pair` off the GUI thread."""
        super().__init__(parent)
        self.setWindowTitle("Pareja")
        self.resize(1200, 820)
        frame = QFrame(objectName="term")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)
        self.lay = QVBoxLayout(frame)
        self.wait = text("leyendo la pareja…", T["muted"], 14)
        self.lay.addWidget(self.wait)
        background.get("portfolios/pair", self.paint, owner=self, **params)

    def paint(self, got: dict) -> None:
        """Draw what the daemon answered."""
        self.wait.hide()
        if "error" in got:
            return self.lay.addWidget(text(got["error"], colour("fail"), 14))
        self.setWindowTitle(got["title"])
        inner = QWidget()
        col = QVBoxLayout(inner)
        col.addWidget(text(got["title"], T["text"], 17, True))
        if got.get("relaxed"):
            col.addWidget(text(got["relaxed"], colour("watch"), 14, True))
        for block in got["blocks"]:
            col.addWidget(draw(block))
        col.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        self.lay.addWidget(scroll, 1)
