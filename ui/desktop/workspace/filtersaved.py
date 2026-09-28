"""The filters strip's saved list: keep the rows on screen under a name, and bring one back."""

import httpx
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QInputDialog, QPushButton, QWidget

from ui.desktop import client


class SavedFilters(QWidget):
    """A dropdown of the filters saved by name, «Cargar» and «Guardar con nombre…».
    `chosen(rows)` carries a saved filter's rows; `said(text)` what to tell the owner."""

    chosen = Signal(list)
    said = Signal(str)

    def __init__(self) -> None:
        """Build the three controls and read the saved list."""
        super().__init__()
        self.kept: dict[str, dict] = {}
        self.names = QComboBox()
        self.names.setMinimumWidth(180)
        self.names.setToolTip("Filtros guardados con nombre (AlgoData/filters/saved.yaml)")
        load, self.store = QPushButton("Cargar"), QPushButton("Guardar con nombre…")
        load.setToolTip("Pone las condiciones del filtro guardado en las filas; no lo aplica.")
        load.clicked.connect(self.load)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        for w in (self.names, load, self.store):
            lay.addWidget(w)
        self.refresh()

    def refresh(self) -> None:
        """Read the saved filters again."""
        try:
            self.kept = client.get("filters/saved").get("saved", {})
        except httpx.HTTPError as failed:
            self.said.emit(f"El demonio no respondió: {failed}")
            return
        self.names.clear()
        self.names.addItems(sorted(self.kept))

    def load(self) -> None:
        """Hand the chosen saved filter's rows to the strip."""
        name = self.names.currentText()
        if name in self.kept:
            self.chosen.emit(self.kept[name]["rows"])

    def save(self, rows: list[dict]) -> None:
        """Ask a name and keep these rows under it.

        Args:
            rows: The strip's rows, [{metric, op, value}].
        """
        name, ok = QInputDialog.getText(self, "Guardar filtro", "Nombre del filtro:")
        if not ok or not name.strip():
            return
        try:
            got = client.post("filters/saved", {"name": name.strip(), "rows": rows})
        except httpx.HTTPError as failed:
            self.said.emit(f"El demonio no respondió: {failed}")
            return
        self.said.emit(got.get("error") or f"Guardado como «{name.strip()}»")
        self.refresh()
        self.names.setCurrentText(name.strip())
