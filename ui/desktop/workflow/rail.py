"""The workflow rail: every step of the chosen project down one line, with its two locks on top."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.selection import SELECTION
from ui.desktop.workflow.gauge import BlindBanner, Oos2Gauge
from ui.desktop.workflow.steprow import StepRow


class WorkflowRail(QFrame):
    """The steps of docs/AgentPDFs/WORKFLOW.md for the project in `SELECTION`, each with its
    state, its funnel and its why on hover. Clicking a step emits `open_step(dict)`."""

    open_step = Signal(dict)

    def __init__(self) -> None:
        """Build the empty rail and follow the global selection."""
        super().__init__()
        self.setObjectName("term")
        self.project: str | None = None
        self.rows: list[StepRow] = []
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(6)
        head = QHBoxLayout()
        kicker = QLabel("WORKFLOW")
        kicker.setObjectName("kicker")
        self.title = QLabel("—")
        self.title.setObjectName("mono")
        again = QPushButton("↻")
        again.setToolTip("Volver a leer el disco y el ledger")
        again.clicked.connect(lambda: self.load(self.project))
        head.addWidget(kicker)
        head.addWidget(self.title, 1)
        head.addWidget(again)
        outer.addLayout(head)
        self.note = QLabel("Elige un proyecto.")
        self.note.setObjectName("dim")
        self.note.setWordWrap(True)
        outer.addWidget(self.note)
        self.gauge, self.banner = Oos2Gauge(), BlindBanner()
        outer.addWidget(self.gauge)
        outer.addWidget(self.banner)
        rule = QFrame()
        rule.setObjectName("rule")
        outer.addWidget(rule)
        self.list = QVBoxLayout()
        self.list.setContentsMargins(0, 0, 0, 0)
        self.list.setSpacing(0)
        inner = QWidget()
        inner.setLayout(self.list)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)
        SELECTION.changed.connect(self.follow)

    def follow(self, chosen: dict) -> None:
        """Reload when the global selection names another project.

        Args:
            chosen: What `SELECTION.changed` carries.
        """
        if chosen["project"] != self.project:
            self.load(chosen["project"])

    def load(self, project: str | None) -> None:
        """Ask the daemon for one project's rail and draw it; say why when it cannot.

        Args:
            project: Project name, or None to empty the rail.
        """
        self.project = project
        if not project:
            self.show_workflow(None, "Elige un proyecto.")
            return
        try:
            data = client.get("workflow", project=project)
        except Exception as failed:  # noqa: BLE001 — the ui boundary: show it, do not die
            self.show_workflow(None, f"El demonio no respondió: {failed}")
            return
        self.show_workflow(None if "error" in data else data, data.get("error", ""))

    def show_workflow(self, data: dict | None, note: str = "") -> None:
        """Replace everything drawn.

        Args:
            data: What `GET /api/workflow` returned, or None.
            note: A sentence to show above the gauge; empty hides it.
        """
        while self.list.count():
            gone = self.list.takeAt(0).widget()
            if gone:
                gone.setParent(None)   # off screen now; deleteLater alone waits for the loop
                gone.deleteLater()
        self.rows = []
        self.note.setText(note)
        self.note.setVisible(bool(note))
        self.gauge.setVisible(data is not None)
        self.banner.setVisible(data is not None)
        if data is None:
            self.title.setText(self.project or "—")
            return
        self.title.setText(f"{data['project']} · {data['asset'] or 'activo ?'}")
        self.gauge.fill(data["oos2"], data["asset"])
        self.banner.fill(data["blind"])
        steps = data["steps"]
        for i, step in enumerate(steps):
            row = StepRow(step, i == 0, i == len(steps) - 1)
            # The row itself, not the dict: a signal hands over a copy, never the same object.
            row.clicked.connect(lambda _step, chosen=row: self.open(chosen))
            self.rows.append(row)
            self.list.addWidget(row)
        self.list.addStretch(1)

    def open(self, chosen: StepRow) -> None:
        """Mark the clicked step and pass it on.

        Args:
            chosen: The row clicked; its step goes out as the daemon sent it.
        """
        for row in self.rows:
            row.choose(row is chosen)
        self.open_step.emit(chosen.step)
