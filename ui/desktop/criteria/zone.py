"""Criterios: what a strategy has to meet at each workflow step to go on, seen and edited."""

import httpx
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.criteria.dialog import RuleDialog
from ui.desktop.criteria.parts import (COLUMNS, CUT, FREEZE, INTRO, OUTCOMES, TIPS, cells, mark,
                                       table)
from ui.desktop.theme import C, T

class CriteriaZone(QFrame):
    """The zone: the freeze on top, then one section per step in WORKFLOW's
    order, then the history of changes. Reads the daemon on first show."""

    def __init__(self) -> None:
        """Build the frame; `load` fills it."""
        super().__init__()
        self.setObjectName("term")
        self.state: dict | None = None
        kicker = QLabel("Proyecto · Criterios", objectName="kicker")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        title = QLabel("Criterios de paso", objectName="h1")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.freeze = QPushButton("Congelar")
        self.freeze.setToolTip(FREEZE)
        self.freeze.clicked.connect(self.ask_freeze)
        reload_ = QPushButton("Recargar criterios")
        reload_.setToolTip("Vuelve a leer criteria.yaml y el historial, por si otro los cambió.")
        reload_.clicked.connect(self.load)
        top = QHBoxLayout()
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(self.freeze)
        top.addWidget(reload_)
        intro = QLabel(INTRO)
        intro.setWordWrap(True)
        head = QHBoxLayout()
        head.addWidget(intro, 1)
        head.addWidget(mark(OUTCOMES))
        self.frozen, self.status = QLabel(""), QLabel("", objectName="dim")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        for banner in (self.frozen,):
            banner.setWordWrap(True)
            banner.hide()
        self.column = QVBoxLayout()
        self.column.setSpacing(4)
        inner = QWidget()
        inner.setLayout(self.column)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(6)
        lay.addWidget(kicker)
        lay.addLayout(top)
        lay.addLayout(head)
        lay.addWidget(self.frozen)
        lay.addWidget(self.status)
        lay.addWidget(scroll, 1)

    def showEvent(self, event: QShowEvent) -> None:
        """Read the daemon the first time the zone is shown, not when the window starts."""
        super().showEvent(event)
        if self.state is None:
            self.load()

    def load(self) -> None:
        """Read `/api/criteria` and rebuild the banners and every section."""
        try:
            self.state = client.get("criteria")
        except httpx.HTTPError as err:
            self.say(f"El demonio no contesta: {err}", C["dead"])
            return
        while self.column.count():
            item = self.column.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.banners()
        build = self.state["build"]
        self.heading("6", "Build", "Filtros de aceptación: los escribe el builder en la tarea "
                     f"Build y los aplica SQX. Aquí solo se leen ({build['where']}).")
        self.column.addWidget(table(COLUMNS, [cells(r) for r in build["rows"]], TIPS))
        for step in self.state["steps"]:
            self.section(step)
        self.heading("", "Historial de cambios", "Cada cambio hecho desde esta pestaña, el "
                     "más reciente arriba (ledger/criteria-history.jsonl).")
        rows = [[(h["at"].replace("T", " "), ""), (h["step"] or "—", ""), (h["what"], ""),
                 (h["was"], h["was"]), (h["now"], h["now"])] for h in self.state["history"]]
        self.column.addWidget(table(("Cuándo", "Paso", "Qué", "Antes", "Después"), rows, {})
                              if rows else QLabel("Sin cambios todavía.", objectName="dim"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.column.addStretch(1)
        self.say(f"{sum(len(s['rows']) for s in self.state['steps'])} criterios en "
                 f"{len(self.state['steps'])} pasos", T["muted"])

    def banners(self) -> None:
        """Say that the criteria are frozen, when they are."""
        assert self.state is not None   # `banners` runs after `reload` has read it
        frozen = self.state["frozen"]
        self.frozen.setVisible(bool(frozen))
        self.freeze.setEnabled(not frozen)
        self.freeze.setText("Congelados" if frozen else "Congelar")
        if frozen:
            hand = " OJO: criteria.yaml se ha editado a mano después de congelar." \
                if frozen["changed"] else ""
            self.frozen.setText(f"Criterios congelados desde el {frozen['on']} "
                                f"({frozen['by']}): solo lectura.{hand}")
            self.frozen.setStyleSheet(f"color: {C['dead'] if hand else C['promising']}; "
                                      "font-weight: 700;")

    def heading(self, n: str, title: str, said: str) -> QHBoxLayout:
        """A section's kicker and the sentence under it; returns the kicker's row.

        Args:
            n: Step number, "" for a section that is not a step.
            title: The step's short name.
            said: One dim sentence about the section, "" for none.
        """
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 16, 0, 0)
        name = QLabel(f"Paso {n} · {title}" if n else title, objectName="kicker")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        name.setStyleSheet("font-size: 15px; letter-spacing: 0.5px;")
        row.addWidget(name)
        row.addStretch(1)
        self.column.addWidget(holder)
        if said:
            label = QLabel(said, objectName="dim")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
            label.setWordWrap(True)
            self.column.addWidget(label)
        return row

    def section(self, step: dict) -> None:
        """One step: its cut, its rules or «Sin criterios», and «Añadir criterio»."""
        row = self.heading(step["n"], step["title"], "")
        row.insertWidget(1, QLabel(f"Corta: {step['cut']}" if step["cut"] else  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                                   "Sin databank de corte", objectName="dim"))
        row.insertWidget(2, mark(CUT))
        assert self.state is not None
        add = QPushButton("Añadir criterio")
        add.setEnabled(bool(step["cut"]) and not self.state["frozen"])
        add.setToolTip("Añade un criterio a este paso: una métrica de SQX, un número de un "
                       "test de la app, un veredicto o una regla compuesta."
                       if step["cut"] else "criteria.yaml no dice qué databank corta este "
                       "paso (`cut`): hasta que lo diga no se le pueden poner criterios, "
                       "porque el autopilot se pararía al juzgarlo.")
        add.clicked.connect(lambda _, s=step: self.edit(s, None))
        row.addWidget(add)
        if step["rows"]:
            t = table(COLUMNS, [cells(r) for r in step["rows"]], TIPS)
            t.cellDoubleClicked.connect(lambda r, _, s=step: self.edit(s, r))
            self.column.addWidget(t)
        else:
            self.column.addWidget(QLabel("Sin criterios: pasan todas."))
        if step["offered"]:
            self.column.addWidget(QLabel(  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                "Disponibles, sin umbral todavía — calculados y visibles, no juzgan:",
                objectName="dim"))
            self.column.addWidget(table(COLUMNS, [cells(r) for r in step["offered"]], TIPS))

    def edit(self, step: dict, at: int | None) -> None:
        """Open the dialog for one rule of a step and send what it built to the daemon.

        Args:
            step: The step, as the state holds it.
            at: The rule's position; None adds one.
        """
        assert self.state is not None
        if self.state["frozen"]:
            self.say("Los criterios están congelados: no se cambian.", C["weak"])
            return
        was = step["rows"][at]["rule"] if at is not None else None
        dialog = RuleDialog(self, f"Paso {step['n']} · {step['title']}", step["facts"], was,
                              why=step["rows"][at].get("why", "") if at is not None else "")
        if not dialog.exec():
            return
        self.send("criteria/rule", {"n": step["n"], "at": at, "was": was,
                                    "rule": None if dialog.deleted else dialog.rule})

    def ask_freeze(self) -> None:
        """Confirm, then freeze: it cannot be undone from the window."""
        if QMessageBox.question(self, "Congelar criterios", FREEZE + "\n\n¿Congelar ahora?"  # pyright: ignore[reportCallIssue]  # PySide6 stub lists the deprecated overload that wants buttons
                                ) == QMessageBox.StandardButton.Yes:
            self.send("criteria/freeze", {})

    def send(self, path: str, body: dict) -> None:
        """One write through the daemon; the zone is re-read and says what happened."""
        try:
            done = client.post(path, body)
        except httpx.HTTPStatusError as err:
            self.say(f"No escrito — {err.response.json().get('detail', err)}", C["dead"])
            return
        self.load()
        self.say(f"Escrito en criteria.yaml · {done['note']}", C["promising"])

    def say(self, text: str, colour: str) -> None:
        """Put one line on the status line of the zone, in the colour of what happened."""
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {colour};")
