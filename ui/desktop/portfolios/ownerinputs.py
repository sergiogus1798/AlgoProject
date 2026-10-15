"""«Entradas del dueño»: the inputs the funding modules refuse without, typed and saved one by one."""

from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.desktop import background
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.theme import T


class OwnerInputs(QDialog):
    """One row per input: its sentence, what it blocks, a box and «Guardar». Nothing is written
    that was not typed here; a blank box removes the line and the file's value comes back."""

    def __init__(self, parent: QWidget, changed: Any) -> None:
        """Open empty and ask `portfolios/owner` off the GUI thread; `changed()` fires after a save."""
        super().__init__(parent)
        self.setWindowTitle("Entradas del dueño")
        self.resize(1000, 900)
        self.changed = changed
        frame = QFrame(objectName="term")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)
        col = QVBoxLayout(frame)
        col.addWidget(text("Entradas del dueño", T["text"], 17, True))
        col.addWidget(
            text(
                "Lo que el fondeo no inventa. Se guarda en config/owner.yaml (local, fuera de git); el resto viene "
                "de portfolio/funded/sim/config.yaml y portfolio/common/construct/config.yaml; "
                "una caja vacía devuelve el valor del fichero del repositorio.",
                T["muted"],
                13,
            )
        )
        self.state = text("", T["muted"], 13)
        col.addWidget(self.state)
        self.rows = QVBoxLayout()
        inner = QWidget()
        inner.setLayout(self.rows)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setWidget(inner)
        col.addWidget(area, 1)
        background.get("portfolios/owner", self.paint, owner=self)

    def paint(self, got: dict) -> None:
        """Draw one row per field the daemon listed."""
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        for f in got.get("fields", []):
            self.rows.addWidget(self.row(f))
        self.rows.addStretch(1)

    def row(self, f: dict) -> QWidget:
        """One input: label and help above, the box, «Guardar», and where its value comes from."""
        box = QWidget()
        col = QVBoxLayout(box)
        col.setContentsMargins(0, 6, 0, 6)
        col.addWidget(text(f"{f['label']}", T["text"], 17, True))
        unit = " — fracción: 5 % se escribe 0,05" if f["kind"] == "fraction" else ""
        col.addWidget(text(f"{f['help']}{unit}. Bloquea {f['blocks']}.", T["text"], 14))
        line = QHBoxLayout()
        edit: QLineEdit | QComboBox
        if f["options"]:
            edit = QComboBox()
            edit.addItems(["", *f["options"]])
            edit.setCurrentText("" if f["value"] is None else str(f["value"]))
        else:
            edit = QLineEdit("" if f["value"] is None else str(f["value"]))
            edit.setPlaceholderText("decisión tuya")
        edit.setFixedWidth(220)
        save = QPushButton("Guardar")
        origin = QLabel(
            "sin contestar"
            if f["value"] is None
            else ("tu capa local" if f["from_layer"] else "valor del repositorio")
        )
        origin.setStyleSheet(
            f"color:{colour('watch') if f['value'] is None else T['muted']};"
        )
        save.setEnabled(False)  # nothing to save until the box changes
        changed = (
            edit.currentTextChanged if isinstance(edit, QComboBox) else edit.textChanged
        )
        changed.connect(lambda _: save.setEnabled(True))
        save.clicked.connect(lambda: self.save(f["id"], edit))
        for w in (edit, save, origin):
            line.addWidget(w)
        line.addStretch(1)
        col.addLayout(line)
        return box

    def save(self, field: str, edit: QLineEdit | QComboBox) -> None:
        """Send what the box holds; the answer is the sentence under the title."""
        value = edit.currentText() if isinstance(edit, QComboBox) else edit.text()
        background.post(
            "portfolios/owner",
            {"field": field, "value": value},
            self.saved,
            owner=self,
        )

    def saved(self, got: dict) -> None:
        """Say what happened and read the list again so every row shows what is in force."""
        ok = got.get("ok")
        self.state.setText(
            f"Guardado en {got['where']}." if ok else " ".join(got.get("reasons", []))
        )
        self.state.setStyleSheet(
            f"color:{colour('pass') if ok else colour('fail')}; font-size:13px;"
        )
        if ok:
            self.changed()
            background.get("portfolios/owner", self.paint, owner=self)
