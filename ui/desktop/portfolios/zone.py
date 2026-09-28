"""PORTFOLIOS: every archived strategy, its versions, and «Importar» — only from the archive for now."""

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QScrollArea, QSplitter,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.portfolios import detail
from ui.desktop.studypage.net import fetch as daemon_fetch
from ui.desktop.theme import T

# (header, tooltip) of the list's columns, in order.
COLUMNS = (("Estrategia", "Su nombre en el databank del que se archivó."),
           ("Activo", "El símbolo del proyecto de origen."),
           ("Timeframe", "El del proyecto de origen."),
           ("Paso", "El paso del WORKFLOW en que estaba al archivar su versión más nueva."),
           ("Versiones", "Cuántas veces se archivó. Una versión nunca se sobrescribe."),
           ("Última versión", "Cuándo se archivó la versión más nueva."),
           ("N del Ledger", "Candidatas puntuadas en TODAS las búsquedas del estudio del Ledger "
                            "(la plantilla en ese activo y timeframe) el día que se archivó: con "
                            "ella se deflacta su Sharpe. «—» cuando hay búsquedas pero ninguna "
                            "apuntó candidatas."),
           ("Búsquedas", "Todas las filas del Ledger de ese estudio ese día: cada build, retest o "
                         "filtro que miró sus datos, apunte candidatas o no."),
           ("Proyecto", "El proyecto de SQX del que viene."))
INTRO = ("Las estrategias archivadas con «Archivar» en la ficha de Estrategia. «Importar» las abre "
         "tal como se guardaron: todos los paneles leen el archivo, no se recalcula nada ni se "
         "encola ningún trabajo. Por ahora solo se importa desde el archivo; desde un databank "
         "vivo, cuando el dueño lo pida.")


class PortfoliosZone(QFrame):
    """The zone: the archive's strategies on the left; on the right the chosen one's versions,
    what the chosen version holds and «Importar». `import_requested(identity, version)` is
    what the shell wires to the Estrategia page."""

    import_requested = Signal(str, str)

    def __init__(self, fetch: Callable[..., dict] = daemon_fetch) -> None:
        """Build the frame; the daemon is asked nothing until the zone is first shown.

        Args:
            fetch: GET a daemon route, never raising; injectable for a test.
        """
        super().__init__()
        self.setObjectName("term")
        self.fetch, self.rows, self.loaded = fetch, [], False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)
        lay.addWidget(QLabel("PORTFOLIOS", objectName="kicker"))
        lay.addWidget(QLabel("Estrategias archivadas", objectName="h1"))
        lay.addWidget(text(INTRO, T["muted"], 13))
        self.said = text("", T["muted"], 13)
        lay.addWidget(self.said)
        lay.addWidget(QFrame(objectName="rule"))
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        for i, (head, tip) in enumerate(COLUMNS):
            item = QTableWidgetItem(label(head))
            item.setToolTip(tip)
            self.table.setHorizontalHeaderItem(i, item)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._picked)
        self.versions = QListWidget()
        self.versions.setMaximumHeight(150)
        self.versions.currentItemChanged.connect(lambda *_: self._version())
        self.body = text("", T["text"], 13)
        self.body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.body)
        self.go = QPushButton("Importar esta versión")
        self.go.setToolTip("Abre la página de Estrategia con todo lo que esta versión congeló. "
                           "No calcula nada: lo que no se archivó sale como no calculado.")
        self.go.setEnabled(False)
        self.go.clicked.connect(self._import)
        right = QWidget()
        side = QVBoxLayout(right)
        side.setContentsMargins(12, 0, 0, 0)
        side.addWidget(QLabel(label("versiones"), objectName="mono"))
        side.addWidget(self.versions)
        side.addWidget(scroll, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.go)
        side.addLayout(row)
        split = QSplitter()
        split.addWidget(self.table)
        split.addWidget(right)
        split.setSizes([900, 640])
        lay.addWidget(split, 1)

    def showEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Read the archive the first time the zone is shown.

        Args:
            event: Qt's show event.
        """
        super().showEvent(event)
        if not self.loaded:
            self.reload()

    def reload(self) -> None:
        """Read the archive again («Recargar», or after a new «Archivar»)."""
        self.loaded = True
        got = self.fetch("archive/list")
        if "error" in got:
            return self.said.setText(f'<span style="color:{colour("fail")}">{got["error"]}</span>')
        self.rows = got["strategies"]
        count = sum(len(r["versions"]) for r in self.rows)
        self.said.setText(f"{num(len(self.rows))} estrategia{'s' * (len(self.rows) != 1)} "
                          f"archivada{'s' * (len(self.rows) != 1)}, {num(count)} "
                          f"versi{'ones' if count != 1 else 'ón'}."
                          if self.rows else "El archivo está vacío: archiva una estrategia desde "
                                            "su ficha, en Estrategia.")
        self.table.setRowCount(len(self.rows))
        for i, r in enumerate(self.rows):
            cells = (r["strategy"] or "—", r["symbol"], r["timeframe"] or "—", r["step"],
                     num(len(r["versions"])), detail.when(r["archived_at"]),
                     detail.trials(r["ledger"]), num(r["ledger"]["searches"]), r["project"])
            for j, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setToolTip(f"Identidad: {r['identity']}" if j == 0 else COLUMNS[j][1])
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()
        if self.rows:
            self.table.selectRow(0)

    def _picked(self) -> None:
        """A strategy was chosen: list its versions, newest first, and open the newest."""
        picked = self.table.selectionModel().selectedRows()
        if not picked:
            return
        held = self.rows[picked[0].row()]
        self.versions.blockSignals(True)
        self.versions.clear()
        for v in reversed(held["versions"]):
            item = QListWidgetItem(f"{detail.when(v['archived_at'])} · paso {v['step']}"
                                   + (f" · {v['note']}" if v["note"] else ""))
            item.setData(Qt.UserRole, v["version"])
            item.setToolTip(f"Versión {v['version']} · desde {v['databank']} · "
                            + detail.ledger(v["ledger"]))
            self.versions.addItem(item)
        self.versions.blockSignals(False)
        self.versions.setCurrentRow(0)

    def chosen(self) -> tuple[str, str]:
        """The (identity, version) on screen; ("", "") when none."""
        picked = self.table.selectionModel().selectedRows()
        item = self.versions.currentItem()
        if not (picked and item):
            return "", ""
        return self.rows[picked[0].row()]["identity"], item.data(Qt.UserRole)

    def _version(self) -> None:
        """A version was chosen: say what it holds, and arm «Importar»."""
        identity, version = self.chosen()
        if not identity:
            return
        got = self.fetch("archive/show", identity=identity, version=version)
        self.go.setEnabled("error" not in got)
        self.body.setText(f'<span style="color:{colour("fail")}">{got["error"]}</span>'
                          if "error" in got else detail.page(got))

    def pick(self, identity: str, version: str = "") -> None:
        """Select one strategy and one of its versions ("" for the newest) — for a launcher.

        Args:
            identity: The strategy's identity.
            version: A version folder name.
        """
        i = next(k for k, r in enumerate(self.rows) if r["identity"] == identity)
        self.table.selectRow(i)
        for k in range(self.versions.count()):
            if self.versions.item(k).data(Qt.UserRole) == version:
                self.versions.setCurrentRow(k)

    def _import(self) -> None:
        """Ask the shell to open the version on screen as the Estrategia page."""
        identity, version = self.chosen()
        if identity:
            self.import_requested.emit(identity, version)
