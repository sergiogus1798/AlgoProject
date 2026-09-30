"""The palette view's top bar: which palette is open, what it is, and the library actions."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QVBoxLayout)

POLICY_ES = {"neutral": "Sin etiquetar → entra a peso 1",
             "off": "Sin etiquetar → fuera (la paleta ES su lista)"}


class PaletteBar(QFrame):
    """The picker, the policy, the search box and the four library buttons."""

    opened = Signal(str)
    searched = Signal()
    restated = Signal()
    saved = Signal()
    cloned = Signal(str, str, str)
    removed = Signal()

    def __init__(self) -> None:
        """Build the two rows of the bar."""
        super().__init__(objectName="panel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.picker = QComboBox()
        self.picker.setMinimumWidth(300)
        self.picker.currentIndexChanged.connect(
            lambda: self.opened.emit(self.picker.currentData() or ""))
        row.addWidget(self.picker)
        self.clone = QPushButton("Clonar")
        self.clone.clicked.connect(self.ask_clone)
        row.addWidget(self.clone)
        self.delete = QPushButton("Borrar")
        self.delete.clicked.connect(self.ask_delete)
        row.addWidget(self.delete)
        self.policy = QComboBox()
        self.policy.setMinimumWidth(250)
        for key, text in POLICY_ES.items():
            self.policy.addItem(text, key)
        self.policy.currentIndexChanged.connect(lambda _: self.restated.emit())
        row.addWidget(self.policy)
        self.search = QLineEdit(placeholderText="Buscar bloque o forma en las 83 categorías")
        self.search.setMinimumWidth(240)
        self.search.textChanged.connect(lambda _: self.searched.emit())
        row.addWidget(self.search, 1)
        self.save = QPushButton("Guardar", objectName="primary")
        self.save.clicked.connect(lambda: self.saved.emit())
        row.addWidget(self.save)
        outer.addLayout(row)

        # The counts get a line of their own: squeezed onto the row above they elided to
        # three characters, and they are the only thing that shows a palette has stopped
        # narrowing anything.
        self.counts = QLabel(objectName="muted")
        outer.addWidget(self.counts)

    def fill(self, palettes: dict, labels: dict[str, str], keep: str | None) -> str:
        """Rebuild the picker from the library.

        Args:
            palettes: The library as the daemon sends it, slug to entry.
            labels: Family key to its Spanish name.
            keep: Slug to reselect, when it is still there.

        Returns:
            The slug now selected. Entries are grouped by family in their text rather than
            with separators: a QComboBox separator is selectable by keyboard and would open
            a palette that does not exist.
        """
        self.picker.blockSignals(True)
        self.picker.clear()
        for slug, entry in sorted(palettes.items(),
                                  key=lambda kv: (kv[1]["palette"]["family"],
                                                  kv[1]["palette"]["label"])):
            p = entry["palette"]
            mark = "★ " if p["origin"] == "default" else ""
            self.picker.addItem(f"{labels[p['family']]}  ·  {mark}{p['label']}", slug)
        if keep:
            self.picker.setCurrentIndex(max(self.picker.findData(keep), 0))
        self.picker.blockSignals(False)
        return self.picker.currentData() or ""

    def ask_clone(self) -> None:
        """Ask for the new palette's name and emit the request.

        The slug is derived from what is typed rather than asked for separately: two
        fields for one idea is how a library ends up with `ruptura2` labelled "Tendencia".
        """
        label, ok = QInputDialog.getText(self, "Clonar paleta",
                                         "Nombre de la copia:", text="")
        if not ok or not label.strip():
            return
        slug = "".join(c if c.isalnum() else "_" for c in label.strip().lower())
        self.cloned.emit(slug.strip("_"), label.strip(), self.picker.currentData())

    def ask_delete(self) -> None:
        """Say `removed` once the owner confirms: it deleted on the click (📓 2026-09-29), and
        a palette is an edited list of weights whose only undo was git."""
        name = self.picker.currentText()
        if QMessageBox.question(self, "Borrar paleta", f"¿Borrar la paleta «{name}»? Su fichero "
                                "se elimina de sqx/blocks/palettes/.") == QMessageBox.Yes:
            self.removed.emit()
