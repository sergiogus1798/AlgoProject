"""«Lanzar en SQX»: pick any task of the project and run it on its worker, behind a confirmation."""

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSizePolicy, QWidget

from ui.desktop import background, client
from ui.desktop.workspace.aggregate import ask
from ui.text.numbers import num
from ui.text.brief import full, off

RECHECK_MS = 20_000     # a worker started or stopped elsewhere shows up within this


class Launcher(QWidget):
    """The row under the project's title: the tasks, the button, and why it is off. The
    button is enabled only when the daemon's preflight passes; a click shows the sentence
    to confirm, and only «Sí» queues the job (owner, 2026-09-28: «un botón para lanzar la
    que yo quiera»)."""

    def __init__(self) -> None:
        """Build it empty; `aim` fills it with a project's tasks."""
        super().__init__()
        self.project, self.text = "", ""
        kicker = QLabel("SQX")
        kicker.setObjectName("kicker")
        self.tasks = QComboBox()
        self.tasks.setMinimumWidth(420)
        self.tasks.currentIndexChanged.connect(lambda _i: self.check())
        self.button = QPushButton("▶ Lanzar en SQX")
        self.button.clicked.connect(self.confirm)
        # A disabled button never shows its tooltip: the reason is a visible line instead.
        self.why = QLabel("")
        self.why.setObjectName("dim")
        self.why.setWordWrap(True)
        self.why.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.addWidget(kicker)
        lay.addWidget(self.tasks)
        lay.addWidget(self.button)
        lay.addWidget(self.why, 1)
        self.timer = QTimer(self, timeout=self.check)
        self.timer.start(RECHECK_MS)
        self.show_state({"ok": False, "reasons": ["elige un proyecto"]})

    def aim(self, project: str) -> None:
        """List one project's tasks, each with what its databanks hold now.

        Args:
            project: The project on screen.
        """
        self.project = project
        self.show_state({"ok": False, "reasons": ["comprobando…"]})   # never the last project's
        background.get("launch/tasks", lambda got: self.listed(project, got),
                       key=f"tasks:{id(self)}", owner=self, project=project)

    def listed(self, project: str, got: dict) -> None:
        """The project's tasks arrived (`aim`): fill the chooser and check the first."""
        if project != self.project:
            return
        self.tasks.blockSignals(True)
        self.tasks.clear()
        for t in got.get("tasks", []):
            reads = f"{t['input']} ({num(t['n_in'])}) → " if t["type"] != "Build" else ""
            self.tasks.addItem(f"{t['title']}  ·  {t['type']}  ·  {reads}{t['output']} "
                               f"({num(t['n_out'])})", t["title"])
        self.tasks.blockSignals(False)
        if "tasks" not in got:
            self.show_state({"ok": False, "reasons": [got.get("refuse") or got.get("error", "?")]})
            return
        self.check()

    def check(self) -> None:
        """Ask the daemon whether the chosen task may run now."""
        if not self.isVisible() or not self.project or self.tasks.currentData() is None:
            return
        project, task = self.project, self.tasks.currentData()
        background.get("launch/preflight",
                       lambda got: self.show_state(got) if (project, task) == (
                           self.project, self.tasks.currentData()) else None,
                       key=f"preflight:{id(self)}", owner=self, project=project, task=task)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 — Qt's name
        """Check on coming into view: `aim` may have run while the zone was hidden."""
        super().showEvent(event)
        QTimer.singleShot(0, self.check)

    def show_state(self, got: dict) -> None:
        """Enable the button, or disable it with a few words beside it; every reason is in
        their tooltip (owner, 2026-09-30: a run going filled the row with install details)."""
        reasons = got.get("reasons") or ([got["error"]] if "error" in got else [])
        self.text = got.get("text", "")
        self.button.setEnabled(bool(got.get("ok")))
        self.why.setText("" if got.get("ok") else off(reasons))
        self.why.setToolTip("" if got.get("ok") else full(reasons))

    def confirm(self) -> None:
        """Re-run the preflight for the project and task on screen and show its fresh
        sentence; only «Sí» queues the job, and the daemon re-checks there."""
        task = self.tasks.currentData()
        got = ask("launch/preflight", project=self.project, task=task) if task else {
            "ok": False, "reasons": ["ninguna tarea elegida"]}
        self.show_state(got)
        if not got.get("ok"):
            return
        if QMessageBox.question(self, "Lanzar en SQX", got["text"] + "\n\n¿Confirmas?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            got = client.post("launch/run", {"project": self.project, "task": task})
        except httpx.HTTPError as failed:
            got = {"ok": False, "reasons": [f"El demonio no respondió: {failed}"]}
        if got.get("job"):
            self.button.setEnabled(False)
            self.why.setText(f"En marcha: «{task}» — sigue su avance en «En marcha»")
        else:
            self.show_state(got)
