"""«Continuar workflow»: the one button of the window that deletes in SQX, behind its preflight."""

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QSizePolicy, QWidget

from ui.desktop import client
from ui.desktop.workspace.aggregate import ask

RECHECK_MS = 20_000     # a filter applied or a worker started elsewhere shows up within this


class Advance(QWidget):
    """The button and, beside it, why it is off. `aim(project, databank)` asks the daemon's
    preflight; the button is enabled only when every check passes, and a click asks the owner
    to confirm the literal sentence of encargo 22 §7.2 before anything is queued."""

    def __init__(self) -> None:
        """Build it off; nothing is aimed yet."""
        super().__init__()
        self.project, self.databank, self.text = "", "", ""
        self.button = QPushButton("▶▶ Continuar workflow")
        self.button.clicked.connect(self.confirm)
        # A disabled button never shows its tooltip: the reason is a visible line instead.
        self.why = QLabel("")
        self.why.setObjectName("dim")
        self.why.setWordWrap(True)
        self.why.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.why, 1)
        lay.addWidget(self.button)
        self.show_state({"ok": False, "reasons": ["elige un databank"]})
        self.panel = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.follow)

    def attach(self, panel: QWidget) -> "Advance":
        """Follow a databank panel: re-aim whenever it paints a table, and every RECHECK_MS.

        Args:
            panel: The workspace's `Panel`.

        Returns:
            Itself, so the panel's header mounts it in one line.
        """
        self.panel = panel
        panel.table.model().modelReset.connect(lambda: QTimer.singleShot(0, self.follow))
        self.timer.start(RECHECK_MS)
        return self

    def follow(self) -> None:
        """Aim at the panel's live, unlocked databank; nothing to aim at leaves it off."""
        if not self.isVisible():
            return
        spec = self.panel.sub_spec() if self.panel.live else {}
        if spec.get("databank") and not spec.get("blocked"):
            self.aim(self.panel.project, spec["databank"])
        else:
            self.show_state({"ok": False, "reasons": ["este panel no muestra un databank vivo"]})

    def aim(self, project: str, databank: str) -> None:
        """Point the button at one databank and ask the daemon whether it may run.

        Args:
            project: The project on screen.
            databank: The databank of the sub-panel on screen, as SQX spells it.
        """
        self.project, self.databank = project, databank
        self.show_state(ask("advance/preflight", project=project, databank=databank))

    def show_state(self, got: dict) -> None:
        """Enable the button, or disable it with every reason written beside it."""
        reasons = got.get("reasons") or ([got["error"]] if "error" in got else [])
        self.text = got.get("text", "")
        self.button.setEnabled(bool(got.get("ok")))
        self.why.setText("" if got.get("ok") else "No se puede continuar: " + " · ".join(reasons))

    def confirm(self) -> None:
        """Show the sentence; only «Sí» queues the job, and the preflight runs again there."""
        if QMessageBox.question(self, "Continuar workflow", self.text + "\n\n¿Confirmas?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            got = client.post("advance/run", {"project": self.project, "databank": self.databank})
        except httpx.HTTPError as failed:
            got = {"ok": False, "reasons": [f"El demonio no respondió: {failed}"]}
        if got.get("job"):
            self.button.setEnabled(False)
            self.why.setText(f"En marcha: {got['task']} — sigue su avance en «En marcha»")
        else:
            self.show_state(got)
