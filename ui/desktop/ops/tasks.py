"""One SQX project task by task, read from its install: the lower half of «En marcha»."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHeaderView, QLabel, QSplitter,
                               QTableWidget, QTableWidgetItem, QVBoxLayout)

from ui.desktop import client
from ui.desktop.durations import clock, per, ratio, share
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.ops.progressbar import bar
from ui.desktop.theme import C, chip, kicker, rule

COLUMNS = ["#", "tarea", "tipo", "en este start", "estado", "hechas / total", "avance", "tiempo",
           "por estrategia", "databank de salida", "en disco"]
BAR = COLUMNS.index("avance")
STATUS = {"done": ("hecha", "promising"), "running": ("en curso", "weak"),
          "skipped": ("saltada", "faint"), "earlier": ("hecha antes", "promising"),
          "queued": ("en cola", "pending"), "inactive": ("inactiva", "faint")}
TIPS = {
    "estado": "hecha: el log vio «Task finished» en este start · hecha antes: inactiva en este "
              "start pero su databank tiene estrategias de uno anterior · en curso: la última "
              "tarea que escribe · saltada: inactiva en este start (stage) · en cola: activa y "
              "aún no empezada · inactiva: apagada",
    "hechas / total": "hechas: las que SQX dice haber procesado (el estado del worker mientras "
                      "corre, el log de la tarea al acabar) · total: lo que había en su databank "
                      "de entrada al empezar. Un build no tiene total",
    "avance": "El porcentaje de la tarea en curso: el que SQX escribe en su log cuando lo da (las "
              "tareas walk-forward), si no hechas ÷ total. Sin total (un build) la barra solo "
              "indica que se mueve",
    "tiempo": "desde «TASK STARTED» hasta «TASK FINISHED», o hasta ahora si corre",
    "por estrategia": "tiempo medio por estrategia que SQX declara; si mientras corre dice 0, "
                      "lo que lleva entre las hechas",
    "en disco": "ficheros .sqx en disco: SQX los escribe al sincronizar, así que la salida de la "
                "tarea en curso va con retraso",
}


def state_line(got: dict, project: str) -> str:
    """The rich-text line above the table: running, finished, busy with another, or stopped.

    Args:
        got: What `/api/progress` returned.
        project: The project shown.

    Returns:
        HTML for a QLabel.
    """
    run, age = got["run"], got["log_age_s"]
    if run["project"] == project and not run["finished"]:
        pct = f" · {num(run['percent'])} %" if run["percent"] is not None else ""
        line = chip("CORRIENDO", C["weak"]) + f" &nbsp;tarea <b>{run['current'] or '…'}</b>{pct}"
        now = next((t for t in got["tasks"] if t["status"] == "running"), None)
        if now:
            line += (f" · <b>{ratio(now)}</b> estrategias · {per(now)} por estrategia · "
                     f"la tarea lleva {clock(now['elapsed_s'])}")
    elif run["project"] == project:
        line = chip("terminado", C["promising"]) + " &nbsp;el último start de este proyecto acabó"
    elif run["project"] and not run["finished"]:
        line = (chip("otro proyecto corre", C["dead"])
                + f" &nbsp;el install está con <b>{run['project']}</b>")
    else:
        line = chip("parado", C["pending"]) + " &nbsp;el log de hoy no tiene un start de este proyecto"
    if got["workflow_s"] is not None:
        line += f" · workflow de hoy: <b>{clock(got['workflow_s'])}</b>"
    faint = f"<span style='color:{C['faint']}'>"
    return line + (f"{faint}  · log hace {num(age)} s</span>" if age is not None
                   else f"{faint}  · sin log de hoy</span>")


class Tasks(QFrame):
    """The state line, the task table with the running task's bar, and the log tail."""

    def __init__(self) -> None:
        """Build the empty line, table and log."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.state = QLabel("", objectName="mono", wordWrap=True)
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
        split.setSizes([420, 160])
        lay.addWidget(split, 1)

    def load(self, role: str, project: str) -> dict:
        """Redraw one project from what the daemon reads right now.

        Args:
            role: Its install.
            project: Its name.

        Returns:
            What `/api/progress` returned, for the caller's own line.
        """
        return self.show(project, client.get("progress", install=role, project=project))

    def show(self, project: str, got: dict) -> dict:
        """Paint one `/api/progress` answer (`load`, or `Running` off the GUI thread).

        Args:
            project: Its name.
            got: The daemon's answer.

        Returns:
            `got`, for the caller's own line.
        """
        self.state.setText(state_line(got, project))
        self.fill(got["tasks"], got["run"]["percent"])
        self.log.setText("\n".join(got["run"]["tail"]) or "sin líneas de progreso hoy")
        return got

    def fill(self, tasks: list[dict], percent: int | None) -> None:
        """One row per task; the running one gets its bar.

        Args:
            tasks: As `/api/progress` returns them.
            percent: SQX's own figure for the running task, or None.
        """
        self.table.clear()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setRowCount(len(tasks))
        self.table.setHorizontalHeaderLabels([label(c) for c in COLUMNS])
        for j, name in enumerate(COLUMNS):
            self.table.horizontalHeaderItem(j).setToolTip(TIPS.get(name, ""))
        for i, t in enumerate(tasks):
            text, colour = STATUS[t["status"]]
            n, go = t["strategies"], t["started"]
            cells = [num(i + 1), t["title"], t["type"], "sí" if t["active"] else "·", text,
                     ratio(t) if go else "·", "", clock(t["elapsed_s"]) if go else "·",
                     per(t) if go else "·", t["output"], "·" if n is None else num(n)]
            for j, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemIsEnabled)
                item.setToolTip(TIPS.get(COLUMNS[j], ""))
                if j in (0, 5, 7, 8, 10):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if j == 4:
                    item.setForeground(QColor(C[colour]))
                if t["status"] == "inactive":
                    item.setForeground(QColor(C["faint"]))
                if j == 1 and t["status"] == "running":
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(i, j, item)
            if t["status"] == "running":
                self.table.setCellWidget(i, BAR, bar(share(t["done"], t["total"], percent),
                                                     110, C["weak"]))
            elif t["status"] in ("done", "earlier"):
                self.table.setCellWidget(i, BAR, bar(100, 110, C["promising"]))
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(BAR, QHeaderView.Fixed)
        self.table.setColumnWidth(BAR, 120)
