"""The ficha's «calcular» buttons: one study queued for this strategy or the whole databank, then watched."""

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton

from ui.desktop.studypage.net import fetch, send
from ui.desktop.theme import C

POLL_MS = 3000
SCOPES = (("calcular", "one", "Calcula esta métrica para esta estrategia."),
          ("todo el databank", "many", "La calcula para todas las estrategias del databank, "
                                       "en paralelo; tarda más."))


class Compute(QObject):
    """Queues `POST /api/study/run` and polls `/api/jobs` until its jobs end. `said(text)`
    narrates, `done()` fires once every job it started has an exit code."""

    said = Signal(str)
    done = Signal()

    def __init__(self) -> None:
        """Idle; `where` is set by the ficha on each fill."""
        super().__init__()
        self.where: dict = {}
        self.ids: list[str] = []
        self.timer = QTimer(self)
        self.timer.setInterval(POLL_MS)
        self.timer.timeout.connect(self.poll)

    def run(self, study: str, scope: str) -> None:
        """Queue a study on the strategy on screen, or on its whole databank.

        Args:
            study: Catalogue key, e.g. "spread".
            scope: "one" or "many".
        """
        w = self.where
        got = send("study/run", {"study": study, "scope": scope, "project": w["project"],
                                 "databank": w["databank"], "asset": w.get("asset") or "",
                                 "strategies": [w["strategy"]] if scope == "one" else []})
        if "error" in got:
            self.said.emit(f"{study}: {got['error']}")
            return
        self.ids += [j["id"] for j in got["jobs"]]
        self.said.emit(f"{study} en cola ({'esta estrategia' if scope == 'one' else 'todo el databank'}); "
                       "la ficha se redibuja cuando termine")
        self.timer.start()

    def poll(self) -> None:
        """Look at the jobs; when all of this ficha's have ended, say so and stop."""
        jobs = {j["id"]: j for j in fetch("jobs").get("jobs", [])}
        mine = [jobs[i] for i in self.ids if i in jobs]
        if any(j["rc"] is None for j in mine):
            return
        self.timer.stop()
        failed = [j for j in mine if j["rc"] != 0]
        self.ids = []
        self.said.emit(f"terminó con error: {failed[0]['label']}" if failed else "calculado")
        self.done.emit()


def uncomputed(study: str, compute: Compute) -> QHBoxLayout:
    """«no calculado» and its two buttons, for a figure a study has not produced yet.

    Args:
        study: The catalogue key that computes it.
        compute: The ficha's queue.

    Returns:
        A row to put in the figure's cell.
    """
    box = QHBoxLayout()
    box.setSpacing(4)
    note = QLabel("no calculado", objectName="dim")
    note.setStyleSheet(f"color: {C['weak']};")
    box.addWidget(note)
    for label, scope, tip in SCOPES:
        button = QPushButton(label)
        button.setToolTip(f"{tip} Estudio: {study}.")
        button.clicked.connect(lambda _=False, s=scope: compute.run(study, s))
        box.addWidget(button)
    box.addStretch(1)
    return box
