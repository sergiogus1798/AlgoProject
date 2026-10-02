"""The ficha's basic statistics: IS / OOS1 / IS+OOS1 / OOS2 (behind its door), the figures and the trade distribution."""

from PySide6.QtWidgets import (QButtonGroup, QComboBox, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)

from ui.desktop.blocks.kinds import draw
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C, T
from ui.desktop.workspace.fichajobs import Compute, uncomputed

SEGMENTS = ("IS", "OOS1", "IS+OOS1", "OOS2")
LOCKED = SEGMENTS.index("OOS2")
# The four figures the owner reads first, one step larger (2026-09-28); their names keep the grey.
BIG = ("Operaciones", "Net Profit (SQX, suma de operaciones)",
       "Net Profit con spread y slippage reales (suma de operaciones)", "Profit Factor")
PICKED = (f"QPushButton:checked {{ border-color: {C['accent']}; background: {T['select']}; }}"
          f"QPushButton:disabled {{ color: {T['faint']}; border: 1px dashed {T['faint']}; }}")


def clear(grid: QGridLayout | QVBoxLayout) -> None:
    """Empty a layout, nested layouts included."""
    while grid.count():
        entry = grid.takeAt(0)
        if entry.widget():
            entry.widget().deleteLater()
        elif entry.layout():
            clear(entry.layout())


def figure(row: dict) -> QLabel:
    """One figure in the window's number format; red only for money below zero — a negative
    skew or a PF is not a loss."""
    value, unit = row["value"], row.get("unit", "")
    shown = QLabel(num(value, unit), objectName="mono")
    money = "USD" in unit or "$" in unit
    ink = C["dead"] if money and isinstance(value, (int, float)) and value < 0 else T["text"]
    shown.setStyleSheet(f"color: {ink}; font-size: {15 if row['label'] in BIG else 13}px;")
    return shown


class Stats(QWidget):
    """The selector, the figures of the chosen sample and, beside them, its distribution."""

    def __init__(self, compute: Compute) -> None:
        """Build it empty.

        Args:
            compute: The ficha's queue, for a figure a study has not computed.
        """
        super().__init__()
        self.compute = compute
        self.data: dict = {}
        self.segment = QButtonGroup(self)
        picker = QHBoxLayout()
        for i, seg in enumerate(SEGMENTS):
            button = QPushButton(seg)
            button.setCheckable(True)
            button.setStyleSheet(PICKED)
            self.segment.addButton(button, i)
            picker.addWidget(button)
        self.segment.idClicked.connect(self.show_sample)
        self.unit = QComboBox()
        self.unit.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.unit.setToolTip("En qué se cuenta el retorno de cada operación. Por lote quita el "
                             "tamaño de la posición: un money management que crece con la "
                             "cuenta no engorda las colas.")
        self.unit.currentTextChanged.connect(lambda _: self.show_sample(self.segment.checkedId()))
        picker.addWidget(self.unit)
        picker.addStretch(1)
        self.reserved = QLabel("", objectName="dim")
        self.reserved.setWordWrap(True)
        self.reserved.setStyleSheet(f"color: {C['weak']};")
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(18)
        self.grid.setColumnStretch(1, 1)
        left = QVBoxLayout()
        left.addWidget(QLabel("ESTADÍSTICAS BÁSICAS", objectName="kicker"))
        left.addLayout(picker)
        left.addWidget(self.reserved)
        left.addLayout(self.grid)
        left.addStretch(1)
        self.chart = QVBoxLayout()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(left, 2)
        lay.addLayout(self.chart, 3)

    def fill(self, data: dict) -> None:
        """Take `/api/strategy/stats`'s answer and show IS.

        Args:
            data: `samples` {IS, OOS1, OOS2}, each `{rows, returns}` or `{blocked, why?}`;
                `units`, `default_unit` — or `error`.
        """
        self.data = data
        self.unit.blockSignals(True)
        self.unit.clear()
        self.unit.addItems(data.get("units", []))
        self.unit.setCurrentText(data.get("default_unit", ""))
        self.unit.setVisible(bool(data.get("units")))
        self.unit.blockSignals(False)
        oos2 = data.get("samples", {}).get("OOS2", {})
        locked = "rows" not in oos2
        self.segment.button(LOCKED).setEnabled(not locked)
        # A disabled button never shows its tooltip, so the reason is written beside it.
        self.reserved.setText(f"OOS2 {oos2['blocked']}" if "blocked" in oos2 else "")
        self.reserved.setToolTip(oos2.get("why", ""))
        self.segment.button(0).setChecked(True)
        self.show_sample(0)

    def show_sample(self, index: int) -> None:
        """Show one sample's figures, its return shape and its histogram."""
        clear(self.grid)
        clear(self.chart)
        if "error" in self.data:
            error = QLabel(self.data["error"], objectName="dim")
            error.setWordWrap(True)
            error.setStyleSheet(f"color: {C['muted' if self.data.get('absent') else 'dead']};")
            self.grid.addWidget(error, 0, 0, 1, 2)
            return
        got = self.data["samples"][SEGMENTS[index]]
        shape = got.get("returns", {}).get(self.unit.currentText(), {})
        rows = got["rows"] + ([{"label": "Retorno por operación", "value": None, "head": True}]
                              if shape else [])
        rows += shape.get("rows", [])
        for i, row in enumerate(rows):
            name = QLabel(label(row["label"]), objectName="kicker" if row.get("head") else "dim")
            name.setWordWrap(True)
            if row["label"] in BIG:
                name.setStyleSheet("font-size: 15px;")
            self.grid.addWidget(name, i, 0)
            if row.get("head"):
                continue
            if row["value"] is None and row.get("study"):
                self.grid.addLayout(uncomputed(row["study"], self.compute), i, 1)
            else:
                self.grid.addWidget(figure(row), i, 1)
        if shape.get("histogram"):
            self.chart.addWidget(draw(shape["histogram"]))
        self.chart.addStretch(1)
