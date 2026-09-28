"""One value of the SQX settings as an editor: a dropdown where the values are fixed, a box otherwise."""

import httpx
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from ui.desktop import client
from ui.text.numbers import num
from ui.desktop.theme import C


def shown(value: object) -> str:
    """A current value as the window prints it: numbers through `num`, lists joined."""
    if isinstance(value, list):
        return " · ".join(shown(v) for v in value) or "(vacío)"
    return num(value)


def combo(options: list[dict], current: object) -> QComboBox:
    """A dropdown over the fixed options, on the current value.

    Args:
        options: {value, text} as the daemon sends them.
        current: The value the file holds.

    Returns:
        The combo. A current value outside the list is added and says so, rather than the
        box silently showing the first option as if it were the one in the file.
    """
    box = QComboBox()
    for o in options:
        box.addItem(o["text"], o["value"])
    if current not in [o["value"] for o in options]:
        box.addItem(f"{current} (el del fichero, fuera de la lista)", current)
    box.setCurrentIndex(box.findData(current))
    return box


def bounds_of(spec: dict) -> str:
    """The range a number box accepts, as the window says it, or "" when it is open."""
    lo, hi = spec.get("min"), spec.get("max")
    if lo is None and hi is None:
        return ""
    if hi is None:
        return f"≥ {num(lo)}"
    return f"≤ {num(hi)}" if lo is None else f"entre {num(lo)} y {num(hi)}"


class Field(QWidget):
    """The editor of one value. `written(str)` carries the line for the zone's status bar,
    `refused(str)` the daemon's reason when it said no."""

    written = Signal(str)
    refused = Signal(str)

    def __init__(self, file: str, spec: dict) -> None:
        """Build the editor the spec asks for.

        Args:
            file: The shared file the value lives in ("build", "classes", "policy", …).
            spec: The field as `/api/sqxconfig` sends it.
        """
        super().__init__()
        self.file, self.spec, self.value = file, spec, spec["value"]
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(6)
        self.build()

    def build(self) -> None:
        """(Re)build the editor on `self.value`."""
        while self.row.count():
            item = self.row.takeAt(0)
            if item.widget():          # the trailing stretch is an item with no widget
                item.widget().hide()   # deleteLater alone leaves it painted until the loop runs
                item.widget().deleteLater()
        kind = self.spec["type"]
        if self.spec.get("locked"):
            text = QLabel(f"{shown(self.value)}   · bloqueado")
            text.setObjectName("dim")
            text.setToolTip(self.spec["locked"])
            self.row.addWidget(text)
        elif kind in ("choice", "bool"):
            box = combo(self.spec["options"], self.value)
            box.activated.connect(lambda _i, b=box: self.send(b.currentData()))
            self.row.addWidget(box)
        elif kind == "choices":
            self.items()
        else:
            edit = QLineEdit(", ".join(map(str, self.value)) if kind == "list"
                             else "" if self.value is None else str(self.value))
            edit.setMinimumWidth(220)
            if kind == "list":
                edit.setPlaceholderText("separados por comas")
            edit.editingFinished.connect(lambda e=edit: self.typed(e.text()))
            self.row.addWidget(edit)
            bounds = bounds_of(self.spec)
            if bounds:
                edit.setToolTip(bounds)
                hint = QLabel(bounds)
                hint.setObjectName("dim")
                self.row.addWidget(hint)
        if self.spec.get("warn"):
            warn = QLabel("aviso: un run ya hecho se relee con este valor")
            warn.setStyleSheet(f"color: {C['weak']}; font-weight: 700;")
            warn.setToolTip(self.spec["warn"])
            self.row.addWidget(warn)
        self.row.addStretch(1)

    def items(self) -> None:
        """An ordered list of fixed values: one dropdown per item, then add and remove.

        The order is kept because in CrossTF it is a contract — block 1, block 2 — with the
        study that reads the cells.
        """
        boxes = []
        for v in self.value:
            box = combo(self.spec["options"], v)
            box.activated.connect(lambda _i: self.send([b.currentData() for b in boxes]))
            boxes.append(box)
            self.row.addWidget(box)
        add, drop = QPushButton("+"), QPushButton("−")
        add.setToolTip("Añadir al final la primera opción que la lista aún no lleva")
        drop.setToolTip("Quitar el último elemento de la lista")
        unused = [o["value"] for o in self.spec["options"] if o["value"] not in self.value]
        add.clicked.connect(lambda: self.send([*self.value, unused[0]]))
        add.setEnabled(bool(unused))
        drop.clicked.connect(lambda: self.send(self.value[:-1]))
        drop.setEnabled(bool(self.value))
        self.row.addWidget(add)
        self.row.addWidget(drop)

    def typed(self, text: str) -> None:
        """A box lost focus: send it only when it says something new."""
        now = (", ".join(map(str, self.value)) if self.spec["type"] == "list"
               else "" if self.value is None else str(self.value))
        if text != now:
            self.send([t.strip() for t in text.split(",") if t.strip()]
                      if self.spec["type"] == "list" else text)

    def send(self, value: object) -> None:
        """Ask the daemon to write the value; on a refusal put the editor back.

        Args:
            value: An option value, a list of them, or the typed text.
        """
        where = " › ".join(str(p) for p in self.spec["path"])
        try:
            done = client.post("sqxconfig/value", {"file": self.file, "path": self.spec["path"],
                                                   "value": value})
        except httpx.HTTPStatusError as err:
            self.refused.emit(f"{where}: {err.response.json().get('detail', err)}")
            self.build()
            return
        self.value = done["value"]
        self.written.emit(f"escrito en assets · {where} = {shown(self.value)}")
        self.build()
