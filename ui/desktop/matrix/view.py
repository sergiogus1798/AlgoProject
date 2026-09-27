"""The population matrix zone: one databank's strategies against every study, and what to do from there."""

import httpx
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QFrame,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView,
                               QVBoxLayout)

from ui.desktop import client
from ui.desktop.matrix import menus
from ui.desktop.matrix.actions import CurateStrip, RunBar
from ui.desktop.matrix.model import FIXED, MatrixModel
from ui.desktop.matrix.paint import CellDelegate, StudyHeader
from ui.desktop.selection import SELECTION
from ui.desktop.theme import MONO, C, T

HELP = ("Una fila por estrategia de este databank, una columna por estudio; el color es lo que "
        "dijo el estudio, rayado ◷ si la configuración de hoy ya firmaría otro hash, «·» si "
        "nunca se corrió. Los estudios se emparejan por identidad y sólo dentro de un databank. "
        "Clic en una celda: abre ese estudio de esa estrategia. Clic en la cabecera: el de la "
        "población. Clic derecho en la cabecera: ordenar y filtrar por estado.")


def skipped_line(skipped: list[dict]) -> str:
    """What the daemon could not read, one clause per folder and reason.

    Args:
        skipped: `/api/matrix` `skipped` rows.

    Returns:
        Spanish text, empty when everything was read.
    """
    return "No leído: " + " · ".join(
        f"{s['path']} — {s['reason']}" + (f" ({s['n']:,})" if s["n"] else "")
        for s in skipped) if skipped else ""


class Matrix(QFrame):
    """The strategies of the databank in `SELECTION` × the studies. Clicking a cell emits
    `open_study(key)` after choosing that strategy; clicking a study header emits
    `open_population(key)`."""

    open_study = Signal(str)
    open_population = Signal(str)

    def __init__(self) -> None:
        """Build the empty zone and follow the global selection."""
        super().__init__()
        self.setObjectName("term")
        self.where: tuple[str | None, str | None] = (None, None)
        self.projects: list[dict] = []
        self.catalogue: list[dict] = []
        self.data: dict = {}
        box = QVBoxLayout(self)
        box.setContentsMargins(12, 10, 12, 10)
        head = QHBoxLayout()
        kicker = QLabel("POBLACIÓN")
        kicker.setObjectName("kicker")
        self.project, self.databank = QComboBox(), QComboBox()
        self.project.setMinimumWidth(260)
        self.project.activated.connect(lambda _: SELECTION.choose(
            project=self.project.currentData(), asset=self.asset()))
        self.databank.activated.connect(lambda _: SELECTION.choose(
            databank=self.databank.currentData()))
        again = QPushButton("↻")
        again.setToolTip("Volver a leer proyectos, catálogo y matriz del disco")
        again.clicked.connect(self.reread)
        self.text = QLineEdit()
        self.text.setPlaceholderText("filtrar por nombre…")
        self.text.textChanged.connect(lambda t: self.model.refilter(t))
        self.every = QCheckBox("todos los estudios")
        self.every.setToolTip("Por defecto sólo salen los estudios con algún resultado en este "
                              "databank; marcado, todo el catálogo, con sus huecos «no corrido».")
        self.every.toggled.connect(lambda _: self.draw())
        self.curate = QPushButton("⊘ curar ▾")
        self.curate.setToolTip("Sólo los estudios que eliminan: muestra el comando /curate que "
                               "aplica su veredicto. La ventana no lo ejecuta.")
        self.curate.clicked.connect(lambda: menus.curate_menu(self))
        self.unfilter = QPushButton("quitar filtros")
        self.unfilter.clicked.connect(lambda: menus.clear_filters(self))
        for w in (kicker, self.project, self.databank, again, self.text, self.every,
                  self.curate, self.unfilter):
            head.addWidget(w, 1 if w is self.text else 0)
        box.addLayout(head)
        self.note = QLabel("Elige un proyecto y un databank.")
        self.note.setObjectName("dim")
        self.note.setWordWrap(True)
        self.note.setToolTip(HELP)
        self.lost = QLabel("")
        self.lost.setWordWrap(True)
        self.lost.setStyleSheet(f"color: {C['weak']}; font-size: 12px;")
        box.addWidget(self.note)
        box.addWidget(self.lost)
        self.model = MatrixModel()
        self.table = QTableView()
        self.header = StudyHeader()
        self.table.setHorizontalHeader(self.header)
        self.table.setModel(self.model)
        self.table.setItemDelegate(CellDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(
            f"QTableView {{ font-family: {MONO}; font-size: 13px; border: none; }} "
            f"QTableView::item:selected {{ background: {T['rule']}; color: {T['text']}; }}")
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.clicked.connect(self.cell_clicked)
        self.header.sectionClicked.connect(self.header_clicked)
        self.header.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header.customContextMenuRequested.connect(self.header_menu)
        box.addWidget(self.table, 1)
        self.runbar = RunBar()
        self.runbar.go.clicked.connect(self.run_selected)
        self.strip = CurateStrip()
        box.addWidget(self.runbar)
        box.addWidget(self.strip)
        SELECTION.changed.connect(self.follow)

    def showEvent(self, event: object) -> None:
        """Read projects and catalogue the first time the zone is shown, not at construction."""
        if not self.catalogue:
            self.reread()
        super().showEvent(event)

    def asset(self) -> str | None:
        """The asset the daemon read off the chosen project's name."""
        return next((p["asset"] for p in self.projects
                     if p["project"] == self.project.currentData()), None)

    def reread(self) -> None:
        """Read projects and catalogue again, then the chosen databank."""
        try:
            self.projects = client.get("projects")["projects"]
            self.catalogue = client.get("catalogue")["studies"]
        except httpx.HTTPError as e:
            self.note.setText(f"El demonio no respondió: {e}")
            return
        self.runbar.offer(self.catalogue)
        self.project.clear()
        for p in self.projects:
            self.project.addItem(p["project"], p["project"])
        self.where = (None, None)
        self.follow(dict(SELECTION.now))

    def follow(self, chosen: dict) -> None:
        """Mirror the selection in the pickers and load the databank when it changed.

        Args:
            chosen: What `SELECTION.changed` carries.
        """
        if not self.catalogue:
            self.reread()
            return
        self.project.setCurrentIndex(self.project.findData(chosen["project"]))
        self.databank.clear()
        banks = next((p["databanks"] for p in self.projects if p["project"] == chosen["project"]), [])
        for d in banks:
            self.databank.addItem(d, d)
        bank = (chosen["databank"] or "").replace(" ", "_") or None
        self.databank.setCurrentIndex(self.databank.findData(bank))
        if (chosen["project"], bank) != self.where:
            self.load(chosen["project"], bank)

    def load(self, project: str | None, databank: str | None) -> None:
        """Ask the daemon for one databank's matrix and draw it; say why when it cannot.

        Args:
            project, databank: Where; either None empties the zone.
        """
        self.where = (project, databank)
        self.strip.hide()
        self.data = {"strategies": [], "cells": {}, "present": [], "skipped": []}
        if project and databank:
            try:
                self.data = client.get("matrix", project=project, databank=databank)
            except httpx.HTTPError as e:
                self.note.setText(f"El demonio no respondió: {e}")
        self.draw()

    def draw(self) -> None:
        """Lay the columns out (only the studies present, or the whole catalogue) and the counts."""
        shown = set(self.catalogue_keys() if self.every.isChecked() else self.data["present"])
        columns = [e for e in self.catalogue if e["key"] in shown]
        self.model.load(self.data, columns)
        self.header.filtered = set(self.model.wanted)
        self.table.setColumnWidth(0, 230)
        self.table.setColumnWidth(1, 110)
        for j in range(len(FIXED), self.model.columnCount()):
            self.table.setColumnWidth(j, 150)
        n, done = len(self.data["strategies"]), len(self.data["present"])
        self.note.setText(f"{n:,} estrategias · {done} estudios con resultado de "
                          f"{len(self.catalogue)} en el catálogo · clic en celda: su estudio · "
                          "clic en cabecera: la población · clic derecho: ordenar y filtrar · "
                          "◷ rayado = caducado · «·» = no corrido" if n else
                          "Nada juzgado todavía en este databank." if self.where[1] else
                          "Elige un proyecto y un databank.")
        self.lost.setText(skipped_line(self.data["skipped"]))
        self.lost.setVisible(bool(self.data["skipped"]))
        gates = [e for e in columns if e["role"] == "gate"]
        self.curate.setEnabled(bool(gates))

    def catalogue_keys(self) -> list[str]:
        """Every study key of the catalogue."""
        return [e["key"] for e in self.catalogue]

    def entry(self, key: str) -> dict:
        """One study's catalogue row."""
        return next(e for e in self.catalogue if e["key"] == key)

    def cell_clicked(self, index: object) -> None:
        """Choose the strategy; on a study cell clicked without Ctrl/Mayús, open that study."""
        s = self.model.strategy(index.row())
        if QApplication.keyboardModifiers() & (Qt.ControlModifier | Qt.ShiftModifier):
            return
        SELECTION.choose(strategy=s["strategy"], identity=s["identity"])
        if index.column() >= len(FIXED):
            self.open_study.emit(self.model.field(index.column()))

    def header_clicked(self, section: int) -> None:
        """A study header opens its population result; a fixed one sorts."""
        if section >= len(FIXED):
            self.open_population.emit(self.model.field(section))
            return
        order = self.model.order
        again = order and order[0] == self.model.field(section) and order[1] == Qt.AscendingOrder
        self.model.sort(section, Qt.DescendingOrder if again else Qt.AscendingOrder)

    def header_menu(self, pos: object) -> None:
        """Sort, filter by state and, on a gate column, the /curate command."""
        menus.column_menu(self, self.header.logicalIndexAt(pos)).exec(self.header.mapToGlobal(pos))

    def run_selected(self) -> None:
        """Queue the run bar's study on every selected row."""
        rows = sorted(i.row() for i in self.table.selectionModel().selectedRows())
        names = [self.model.strategy(r)["strategy"] for r in rows]
        self.runbar.run(*self.where, self.asset() or SELECTION.now["asset"] or "", names)
