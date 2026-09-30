"""The column chooser of one databank table: a checkable list by segment, with a search box."""

import unicodedata

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from ui.desktop.theme import T
from ui.desktop.workspace.columns import SEGMENTS, merged

GROUPS = {"Estudio": "Columnas del estudio de esta pestaña",
          "IS": "IS",
          "OOS": "OOS (tramo de la tarea: la cosecha no dice cuál)",
          "OOS2": "OOS2",
          "IS+OOS1": "IS+OOS1 (calculada con las operaciones de la cosecha)"}


def folded(text: str) -> str:
    """Lower case without accents, so «ganadoras» finds «% Ganadoras» and «deposito» «depósito»."""
    return "".join(ch for ch in unicodedata.normalize("NFD", text.lower())
                   if unicodedata.category(ch) != "Mn")


class ColumnsMenu(QDialog):
    """Tick what the table shows. `answer` after «Aplicar» is the ids in order (what stayed
    keeps its place, what was added goes at the end); after «Restaurar vista por defecto» it
    is None. The strategy's name is not listed: it always stays."""

    def __init__(self, offered: dict[str, dict], ids: list[str], table: str,
                 segs: dict | None, parent: QWidget | None = None) -> None:
        """Build the list checked as the table shows it now.

        Args:
            offered: `columns.choices` of this table.
            ids: The ids the table shows now, in order.
            table: The databank, for the title: the metrics chosen hold in all its tabs.
            segs: GET /api/databank/segments: its `oos` names the span of the OOS group.
            parent: The panel.
        """
        super().__init__(parent)
        self.setObjectName("term")
        self.setWindowTitle(f"Métricas · databank {table}")
        self.resize(520, 640)
        self.offered, self.ids, self.answer, self.bank = offered, ids, ids, table
        self.search = QLineEdit()
        self.search.setPlaceholderText("buscar métrica…")
        self.search.textChanged.connect(self.narrow)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        # An unticked box drew nothing on the dark look: only the ✓ of the ticked ones showed.
        self.tree.setStyleSheet(f"QTreeView::indicator:unchecked {{ border: 1px solid "
                                f"{T['muted']}; width: 11px; height: 11px; }}")
        self.said = QLabel("")
        self.said.setObjectName("dim")
        self.said.setWordWrap(True)
        chosen, span = set(ids), (segs or {}).get("oos")
        titles = GROUPS | ({"OOS": f"{span} (en la tabla, «OOS»; lo dice la cosecha)"}
                           if span else {})
        for group in ("Estudio", *SEGMENTS):
            members = [c for c in offered.values() if c["group"] == group]
            if not members:
                continue
            top = QTreeWidgetItem(self.tree, [titles[group]])
            top.setFlags(Qt.ItemIsEnabled)
            for c in members:
                text = c["header"] + ("   · por defecto" if c["default"] else "") + (
                    "   — sin datos" if c["why"] else "")
                item = QTreeWidgetItem(top, [text])
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked if c["id"] in chosen else Qt.Unchecked)
                item.setData(0, Qt.UserRole, c["id"])
                item.setToolTip(0, f"La columna enseña «–»: {c['why']}" if c["why"] else
                                "Hay datos para esta columna en este databank.")
            top.setExpanded(group in ("Estudio", "IS", "OOS"))
        self.tree.itemChanged.connect(self.count)
        restore, cancel, apply_ = (QPushButton("Restaurar vista por defecto"),
                                   QPushButton("Cancelar"), QPushButton("Aplicar columnas"))
        restore.setProperty("help", "Vuelve a las métricas de siempre y olvida lo elegido "
                                    "para este databank, en todas sus pestañas.")
        cancel.setProperty("help", "Cierra sin cambiar las columnas.")
        apply_.setProperty("help", "Enseña las columnas marcadas: las que ya estaban conservan "
                                   "su sitio y las nuevas van al final. Las métricas se guardan "
                                   "para este databank (todas sus pestañas); las del estudio, "
                                   "para esta pestaña.")
        restore.clicked.connect(self.restore)
        cancel.clicked.connect(self.reject)
        apply_.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addWidget(restore)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(apply_)
        lay = QVBoxLayout(self)
        lay.addWidget(self.search)
        lay.addWidget(self.tree, 1)
        lay.addWidget(self.said)
        lay.addLayout(buttons)
        self.count()

    def checked(self) -> set[str]:
        """The ids ticked now, hidden by the search or not."""
        out = set()
        for g in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(g)
            out |= {top.child(i).data(0, Qt.UserRole) for i in range(top.childCount())
                    if top.child(i).checkState(0) == Qt.Checked}
        return out

    def count(self, *_changed: object) -> None:
        """Say how many columns the table will show."""
        self.said.setText(f"{len(self.checked())} columnas marcadas, más el nombre de la "
                          f"estrategia (siempre). Las métricas se guardan para el databank "
                          f"{self.bank}: valen en todas sus pestañas.")

    def narrow(self, text: str) -> None:
        """Keep only the rows whose header holds the typed text, and open their groups."""
        want = folded(text.strip())
        for g in range(self.tree.topLevelItemCount()):
            top, seen = self.tree.topLevelItem(g), 0
            for i in range(top.childCount()):
                hit = want in folded(top.child(i).text(0))
                top.child(i).setHidden(not hit)
                seen += hit
            top.setHidden(seen == 0)
            if want:
                top.setExpanded(True)

    def accept(self) -> None:
        """«Aplicar columnas»: the ticked ids in the table's order."""
        self.answer = merged(self.ids, self.checked(), self.offered)
        super().accept()

    def restore(self) -> None:
        """«Restaurar vista por defecto»: None, which the panel turns into forgetting."""
        self.answer = None
        super().accept()
