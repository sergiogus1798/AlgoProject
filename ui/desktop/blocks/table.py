"""The table block: sortable, numbers printed the window's way, every cell's full text on hover."""

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QDoubleSpinBox, QHBoxLayout, QHeaderView,
                               QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from core.symbols import alias
from ui.desktop.blocks import chart
from ui.desktop.blocks.card import card, text
from ui.desktop.blocks.states import STATE_LABEL, colour
from ui.text import numbers
from ui.text.glossary import label
from ui.desktop.theme import T

VISIBLE = 16        # rows shown before the table scrolls inside itself
WIDEST = 560        # a column of sentences is cut here; the whole sentence is on hover
# Columns holding a full SQX symbol: shown by its short name (core.symbols.alias), the whole
# string stays on hover so nothing is lost, only shortened on screen.
MARKET_COLS = {"market", "mercado", "symbol", "activo", "asset"}
# A cell holding one of these words — the whole cell, any case — is coloured green/red bold,
# automatically: the contract never colours data, so this is the renderer reading the study's
# own word (CONTRACT §2). Only words that say passed or failed outright (§1, 2026-10-01): not
# «veto», «avisa», «fails» or «survives», which a study writes as a reason or a code.
PASS_WORDS = {"pass", "pasa", "aprobado", "mantener"}
FAIL_WORDS = {"fail", "falla", "no pasa", "muere", "suspenso", "descartar"}
WATCH_WORDS = {"limbo"}     # the WFC's state for «indeciso» (encargo 48)
# A column in percent prints one decimal (§1 «7,7 %, no 8 %»): a «%» that is a unit, not one
# right after a number — «A CI 95 %» or «intervalo 95 % desde» name a confidence level — or a
# `_pct` key («dd_pct_95»).
PERCENT = re.compile(r"(?<![\d\s])\s*%|^%|\(%\)|_pct(_|$)")


class Cell(QTableWidgetItem):
    """A cell that sorts by its value, not by its printed text: «1 200» after «950»."""

    def __init__(self, value: object, market: bool = False, state: str | None = None,
                 percent: bool = False, compact: bool = False) -> None:
        """Print the value and keep it for sorting.

        Args:
            value: What the study wrote in the cell.
            market: True in a column of full SQX symbols: printed by its short name
                (`core.symbols.alias`), the full string kept for sorting and the tooltip.
            state: `pass`/`fail` when the contract's `states` grid names one for this cell,
                else guessed from the text itself (`PASS_WORDS`/`FAIL_WORDS`); bold and green
                or red either way (§1 «Pass/Fail…verde bold…rojo bold»).
            percent: True in a column in percent: one decimal, the «%» left to the header.
            compact: A coloured cell is filled with its state colour, dark text on it.
        """
        shown = alias(value) if market and isinstance(value, str) else value
        figure = isinstance(shown, (int, float, type(None))) and not isinstance(shown, bool)
        if figure and percent:
            printed = numbers.num(shown, "%").removesuffix(" %")
        else:
            # A raw contract state in a cell («watch») reads as its label («Vigilar»).
            printed = chart.num(shown) if figure else STATE_LABEL.get(str(shown), str(shown))
        super().__init__(printed)
        self.value = value
        word = " ".join(value.lower().split()) if isinstance(value, str) else ""
        state = state or ("pass" if word in PASS_WORDS else "fail" if word in FAIL_WORDS
                          else "watch" if word in WATCH_WORDS else None)
        if state:
            font = self.font()
            font.setBold(True)
            self.setFont(font)
            if compact:
                self.setBackground(QColor(colour(state)))
                self.setForeground(QColor(T["bg"]))
            else:
                self.setForeground(QColor(colour(state)))

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


class Fitted(QTableWidget):
    """A table that measures its columns again when first shown. Only inside its frame does the
    stylesheet's font apply (the terminal's monospace, wider than the default): measured before,
    a long cell was cut with room to spare."""

    compact = False     # a small matrix: as wide as its columns, no wider

    def fit(self) -> None:
        """Each column as wide as its content, up to `WIDEST`; a compact table's own width with it."""
        self.resizeColumnsToContents()
        for j in range(self.columnCount()):
            self.setColumnWidth(j, min(WIDEST, self.columnWidth(j) + 16))
        if self.compact:        # a table that scrolls inside itself keeps its last column clear of the bar
            bar = self.verticalScrollBar().sizeHint().width() if self.rowCount() > VISIBLE else 0
            self.setMaximumWidth(sum(self.columnWidth(j) for j in range(self.columnCount())) + 6 + bar)

    def showEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Fit once, with the font the table is really drawn in."""
        super().showEvent(event)
        if not self.property("fitted"):
            self.setProperty("fitted", True)
            self.fit()


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
    table = Fitted(len(b["rows"]), len(b["columns"]))
    table.compact = bool(b.get("compact"))
    table.setHorizontalHeaderLabels([label(c) for c in b["columns"]])
    help_ = b.get("help") or [None] * len(b["columns"])
    for j, h in enumerate(help_):
        if h:
            table.horizontalHeaderItem(j).setToolTip(h)   # the uniform "?" of CONTRACT §5
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setWordWrap(False)
    align = b.get("align") or ["left"] * len(b["columns"])
    market = [c.lower() in MARKET_COLS for c in b["columns"]]
    percent = [bool(PERCENT.search(str(c)) or PERCENT.search(label(c))) for c in b["columns"]]
    states, tips = b.get("states"), b.get("tips")
    # Per column, not per cell: a population table is 10,000 rows × 35 columns, and the
    # header's words and the alignment flag were a third of the seconds it took to draw.
    heads = [label(c) for c in b["columns"]]
    flags = [(Qt.AlignRight if a == "right" else Qt.AlignLeft) | Qt.AlignVCenter for a in align]
    compact = bool(b.get("compact"))
    for i, row in enumerate(b["rows"]):
        for j, v in enumerate(row):
            cell = Cell(v, market[j], states[i][j] if states else None, percent[j], compact)
            cell.setTextAlignment(flags[j])
            # never 1e-05, even on hover; a plain figure is already printed that way
            full = v if isinstance(v, str) else chart.num(v) if percent[j] or market[j] else cell.text()
            own = tips[i][j] if tips else None       # a study's own hover, e.g. WFM's conditions
            cell.setToolTip(own or f"{heads[j]}: {full}")
            table.setItem(i, j, cell)
    # Enabling sorting sorts at once by column 0; the study's own order is the reading order.
    table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
    table.setSortingEnabled(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    # A last column of sentences (the «why», «what it says») takes the spare width, so less
    # of it is cut; a last column of numbers does not, or its figures drift to the far edge.
    table.horizontalHeader().setStretchLastSection(align[-1] == "left" and not b.get("compact"))
    table.fit()
    table.verticalHeader().setDefaultSectionSize(26)
    shown = min(len(b["rows"]), VISIBLE)
    table.setFixedHeight(table.horizontalHeader().sizeHint().height() + 26 * shown + 6)
    if len(b["rows"]) > VISIBLE:
        table.setToolTip(f"{len(b['rows'])} filas: la tabla se desplaza por dentro; pulsa una "
                         "cabecera para ordenar.")
    threshold = b.get("threshold")
    if not threshold:
        return card(b, table)
    names = threshold["column"] if isinstance(threshold["column"], list) else [threshold["column"]]
    cols = [b["columns"].index(n) for n in names]
    return card(b, _thresholded(table, cols, threshold))


def _thresholded(table: QTableWidget, cols: list[int], cfg: dict) -> QWidget:
    """A table with one editable threshold over one or several columns, recolouring all of
    them on every change — no call back to the study: the p-values are already in the table
    (CONTRACT §5.9), e.g. crossmarket's «P por modelo» market × model table, one threshold for
    every model column at once.

    Args:
        table: The built table.
        cols: The p-value columns' indices, one threshold for all.
        cfg: `{"column", "default"}`; `column` is a str or a list of str; `default` is 0.05
            when absent.
    """
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    row = QHBoxLayout()
    row.addWidget(QLabel("Umbral"))
    spin = QDoubleSpinBox()
    spin.setDecimals(3)
    spin.setSingleStep(0.005)
    spin.setRange(0.0, 1.0)
    spin.setValue(cfg.get("default", 0.05))
    spin.setToolTip("Verde por debajo, rojo por encima; se recalcula al instante para todas las "
                    "columnas, sin volver a correr el estudio.")

    def paint(value: float) -> None:
        """Colour every column of `cols` green below `value`, red at or above it."""
        for col in cols:
            for i in range(table.rowCount()):
                item = table.item(i, col)
                if isinstance(item.value, (int, float)):
                    item.setForeground(QColor(colour("pass" if item.value < value else "fail")))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

    spin.valueChanged.connect(paint)
    paint(spin.value())
    row.addWidget(spin)
    row.addStretch(1)
    lay.addLayout(row)
    lay.addWidget(table)
    return box
