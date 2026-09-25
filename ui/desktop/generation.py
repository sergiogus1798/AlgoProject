"""The generation zone: where a running SQX project is, task by task, read from its install."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QHideEvent, QShowEvent
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QHBoxLayout, QHeaderView,
                               QLabel, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout)

from ui.desktop import client
from ui.desktop.durations import clock, per, ratio
from ui.desktop.resultspanel import kicker, rule
from ui.desktop.theme import C, chip

COLUMNS = ["#", "tarea", "tipo", "en este start", "estado", "hechas / total", "tiempo",
           "por estrategia", "databank de salida", "en disco"]
STATUS = {"done": ("hecha", "promising"), "running": ("en curso", "weak"),
          "skipped": ("saltada", "faint"), "earlier": ("hecha antes", "promising"),
          "queued": ("en cola", "pending"),
          "inactive": ("inactiva", "faint")}
ROLE = {"custodian": "custodio · SQX_w2", "conductor": "conductor · SQX_w1", "master": "maestro"}
EVERY_MS = 3000


class Generation(QFrame):
    """One install, one project, and what its log and its databanks say right now."""

    def __init__(self) -> None:
        """Build the pickers, the state line, the task table and the log tail."""
        super().__init__(objectName="term")
        self.data: dict = {}
        self.timer = QTimer(self)
        self.timer.setInterval(EVERY_MS)
        self.timer.timeout.connect(self.refresh)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        head = QHBoxLayout()
        head.addWidget(QLabel("Generación", objectName="h1"))
        head.addSpacing(12)
        head.addWidget(kicker("install"))
        self.install = QComboBox()
        self.install.setToolTip("La ventana lee dos ficheros y una carpeta del install: no le "
                                "envía ningún comando. Vale con el maestro abierto y con el "
                                "custodio ocupado.")
        self.install.currentTextChanged.connect(self.fill_projects)
        head.addWidget(self.install)
        head.addWidget(kicker("proyecto"))
        self.project = QComboBox()
        self.project.setMinimumWidth(260)
        self.project.currentTextChanged.connect(lambda *_: self.refresh())
        head.addWidget(self.project)
        head.addStretch()
        lay.addLayout(head)
        self.state = QLabel("", objectName="mono")
        self.state.setWordWrap(True)
        lay.addWidget(self.state)
        lay.addWidget(rule())

        split = QSplitter(Qt.Vertical)
        top = QFrame()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(kicker("las tareas del proyecto, en el orden en que SQX las corre"))
        self.table = QTableWidget()
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.setShowGrid(False)
        tl.addWidget(self.table, 1)
        split.addWidget(top)
        bottom = QFrame()
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(kicker("el log del install, últimas líneas de progreso"))
        self.log = QLabel("", objectName="dim")
        self.log.setAlignment(Qt.AlignTop)
        self.log.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bl.addWidget(self.log, 1)
        split.addWidget(bottom)
        split.setSizes([560, 260])
        lay.addWidget(split, 1)

    def reload(self) -> None:
        """Ask the daemon which installs and projects exist."""
        self.data = client.get("progress/installs")
        keep = self.install.currentText()
        self.install.blockSignals(True)
        self.install.clear()
        for role in self.data:
            self.install.addItem(role)
            self.install.setItemData(self.install.count() - 1, ROLE.get(role, role), Qt.ToolTipRole)
        self.install.setCurrentText(keep if keep in self.data else "custodian")
        self.install.blockSignals(False)
        self.fill_projects(self.install.currentText())

    def fill_projects(self, role: str) -> None:
        """List the picked install's projects and refresh.

        Args:
            role: The install picked.
        """
        keep = self.project.currentText()
        names = self.data.get(role, [])
        self.project.blockSignals(True)
        self.project.clear()
        self.project.addItems(names)
        self.project.setCurrentText(keep if keep in names else (names[0] if names else ""))
        self.project.blockSignals(False)
        self.refresh()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 — Qt's name
        """Start refreshing while the zone is on screen.

        Args:
            event: Qt's show event.
        """
        super().showEvent(event)
        self.timer.start()

    def hideEvent(self, event: QHideEvent) -> None:  # noqa: N802 — Qt's name
        """Stop asking when nobody is looking.

        Args:
            event: Qt's hide event.
        """
        super().hideEvent(event)
        self.timer.stop()

    def refresh(self) -> None:
        """Redraw the project from what the daemon reads right now."""
        role, project = self.install.currentText(), self.project.currentText()
        if not project:
            return
        got = client.get("progress", install=role, project=project)
        run = got["run"]
        age = got["log_age_s"]
        if run["project"] == project and not run["finished"]:
            pct = f" · {run['percent']} %" if run["percent"] is not None else ""
            line = chip("CORRIENDO", C["weak"]) + f" &nbsp;tarea <b>{run['current'] or '…'}</b>{pct}"
            now = next((t for t in got["tasks"] if t["status"] == "running"), None)
            if now:
                line += f" · <b>{ratio(now)}</b> estrategias · {per(now)} por estrategia · " \
                        f"la tarea lleva {clock(now['elapsed_s'])}"
        elif run["project"] == project:
            line = chip("terminado", C["promising"]) + " &nbsp;el último start de este proyecto acabó"
        elif run["project"] and not run["finished"]:
            line = chip("otro proyecto corre", C["dead"]) + f" &nbsp;el install está con <b>{run['project']}</b>"
        else:
            line = chip("parado", C["pending"]) + " &nbsp;el log de hoy no tiene un start de este proyecto"
        if got["workflow_s"] is not None:
            line += f" · workflow de hoy: <b>{clock(got['workflow_s'])}</b>"
        line += (f"<span style='color:{C['faint']}'>  · log hace {age} s</span>" if age is not None
                 else f"<span style='color:{C['faint']}'>  · sin log de hoy</span>")
        self.state.setText(line)
        self.fill_table(got["tasks"])
        self.log.setText("\n".join(run["tail"]) or "sin líneas de progreso hoy")

    def fill_table(self, tasks: list[dict]) -> None:
        """One row per task.

        Args:
            tasks: As `/api/progress` returns them.
        """
        self.table.setColumnCount(len(COLUMNS))
        self.table.setRowCount(len(tasks))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        for i, t in enumerate(tasks):
            label, colour = STATUS[t["status"]]
            n = t["strategies"]
            cells = [str(i + 1), t["title"], t["type"], "sí" if t["active"] else "·", label,
                     ratio(t) if t["started"] else "·",
                     clock(t["elapsed_s"]) if t["started"] else "·",
                     per(t) if t["started"] else "·",
                     t["output"], "·" if n is None else str(n)]
            for j, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemIsEnabled)
                if j in (0, 5, 6, 7, 9):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if j == 4:
                    item.setForeground(QColor(C[colour]))
                if j == 1 and t["status"] == "running":
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if t["status"] == "inactive":
                    item.setForeground(QColor(C["faint"]))
                self.table.setItem(i, j, item)
            self.table.item(i, 4).setToolTip(
                "hecha: el log vio «Task finished» en este start · hecha antes: inactiva en este "
                "start pero su databank tiene estrategias de uno anterior · en curso: la última "
                "tarea que escribe · saltada: inactiva en este start (stage) · en cola: activa "
                "y aún no empezada · inactiva: apagada")
            self.table.item(i, 5).setToolTip(
                "hechas: las que SQX dice haber procesado (el estado del worker mientras corre, "
                "el log de la tarea al acabar) · total: lo que había en su databank de entrada "
                "al empezar. Un build no tiene total")
            self.table.item(i, 6).setToolTip("desde «TASK STARTED» hasta «TASK FINISHED», o "
                                             "hasta ahora si corre")
            self.table.item(i, 7).setToolTip("tiempo medio por estrategia que SQX declara; si "
                                             "mientras corre dice 0, lo que lleva entre las hechas")
            self.table.item(i, 9).setToolTip("ficheros .sqx en disco: SQX los escribe al "
                                             "sincronizar, así que la salida de la tarea en "
                                             "curso va con retraso")
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
