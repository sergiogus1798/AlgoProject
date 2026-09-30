"""One condition of the filters strip: metric, operator, value, and «×»."""

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QWidget

from ui.text.glossary import label
from ui.text.numbers import num

# The operators a metric's kind admits, as the daemon spells them → what the owner reads.
OPS = {"numeric": [(">", ">"), ("<", "<"), (">=", "≥"), ("<=", "≤"), ("=", "="),
                   ("entre", "entre")],
       "text": [("=", "=")],
       "dist": [("dentro", "mediana dentro del intervalo"),
                ("fuera", "mediana fuera del intervalo")]}


def shown_metric(m: dict) -> str:
    """A metric as the dropdown lists it: the words the daemon gave (`evaluate.named`), the
    glossary's for an older daemon that sent none."""
    return m.get("label") or label(m["key"])


def typed(value: object) -> str:
    """A saved value as the box shows it, so it reads back the same: exact, never scientific."""
    return np.format_float_positional(value, trim="-") if isinstance(value, float) else str(value)


def plain(rows: list[dict]) -> list[dict]:
    """Rows with every numeric text as a float, to compare what is typed with what is in force."""
    def one(v: object) -> object:
        """A value as a float when it reads as one."""
        try:
            return float(v)
        except (TypeError, ValueError):
            return v
    return [{**r, "value": [one(v) for v in r["value"]] if isinstance(r["value"], list)
             else one(r["value"])} for r in rows]


def guessed(got: dict) -> str:
    """The live count's line: what the rows on screen would leave, or why they cannot."""
    if "error" in got:
        return f"Con estas condiciones: {got['error']}"
    blank = f" ({num(got['blank'])} sin valor, se quedan)" if got["blank"] else ""
    return (f"Con estas condiciones, sin aplicar: {num(got['n_in'])} → {num(got['n_out'])} "
            f"pasan{blank} · se verían {num(got['visible'])} contando los descartes a mano · "
            "▶ Aplicar para que la tabla cambie")


class FilterRow(QWidget):
    """One condition: metric, operator, value (two for «entre», an interval % for a
    distribution) and «×». `gone` when removed, `changed` on every edit (the strip's live
    count)."""

    gone = Signal(object)
    changed = Signal()

    def __init__(self, metrics: list[dict]) -> None:
        """Build the row over the metrics the daemon offered."""
        super().__init__()
        self.metrics = {m["key"]: m for m in metrics}
        # `column`, never `metric`: that name hides QPaintDevice.metric() and the first paint
        # segfaults (knowhow/eng/qt-painting-traps.md)
        self.column, self.op = QComboBox(), QComboBox()
        self.column.setMinimumWidth(320)
        for m in metrics:
            self.column.addItem(shown_metric(m), m["key"])
            self.column.setItemData(self.column.count() - 1, m.get("reading") or
                                    f"{num(m['n'])} estrategias tienen valor", Qt.ToolTipRole)
        self.column.currentIndexChanged.connect(self.retype)
        self.value, self.upper = QLineEdit(), QLineEdit()
        for w in (self.value, self.upper):
            w.setFixedWidth(110)
        self.op.currentIndexChanged.connect(self.reshape)
        drop = QPushButton("×")
        drop.setFixedWidth(28)
        drop.clicked.connect(lambda: self.gone.emit(self))
        self.op.currentIndexChanged.connect(self.changed)
        for w in (self.value, self.upper):
            w.textChanged.connect(self.changed)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        for w in (self.column, self.op, self.value, self.upper, drop):
            lay.addWidget(w)
        lay.addStretch(1)
        self.retype()

    def kind(self) -> str:
        """numeric, text or dist: which operators the chosen metric admits."""
        m = self.metrics.get(self.column.currentData(), {"kind": "metric", "numeric": True})
        return "dist" if m["kind"] == "dist" else ("numeric" if m["numeric"] else "text")

    def retype(self) -> None:
        """Offer the chosen metric's operators."""
        self.op.clear()
        for code, words in OPS[self.kind()]:
            self.op.addItem(words, code)

    def reshape(self) -> None:
        """Two value boxes for «entre», an interval % for a distribution."""
        code = self.op.currentData()
        self.upper.setVisible(code == "entre")
        self.value.setPlaceholderText("intervalo %: 50, 80, 90, 98" if code in ("dentro", "fuera")
                                      else ("desde" if code == "entre" else "valor"))
        self.upper.setPlaceholderText("hasta")

    def filled(self) -> bool:
        """Whether a value was typed: an empty row is no condition."""
        return bool(self.value.text().strip() or self.upper.text().strip())

    def spec(self) -> dict:
        """The row as the daemon reads it."""
        code, text = self.op.currentData(), self.value.text().strip().replace(",", ".")
        value = [text, self.upper.text().strip().replace(",", ".")] if code == "entre" else text
        return {"metric": self.column.currentData(), "op": code, "value": value}

    def put(self, row: dict) -> None:
        """Show a saved row."""
        self.column.setCurrentIndex(max(self.column.findData(row["metric"]), 0))
        self.op.setCurrentIndex(max(self.op.findData(row["op"]), 0))
        low, high = row["value"] if isinstance(row["value"], list) else (row["value"], "")
        self.value.setText(typed(low))
        self.upper.setText(typed(high))
