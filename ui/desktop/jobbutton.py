"""A button that queues one daemon job after a confirmation, and follows it to its end."""

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ui.desktop import background
from ui.desktop.theme import C

POLL_MS = 4000
FLAGS = ("PREGUNTA:", "YA EXISTE:", "PLANTILLA:")   # lines of the author worth lifting out


class JobButton(QWidget):
    """«▶ text» → `confirm()` (None to refuse, with the reason said) → «Sí» → POST `path`
    with `body()`; then `/api/jobs` every POLL_MS until the job ends, its state and the end of
    its log under the button. `ended(job)` fires once, with the job's record."""

    def __init__(self, text: str, path: str, body: Callable[[], dict],
                 confirm: Callable[[], str | None], ended: Callable[[dict], None] = print) -> None:
        """Build the button and the empty state line."""
        super().__init__()
        self.path, self.body, self.confirm, self.ended = path, body, confirm, ended
        self.job = ""
        self.button = QPushButton(f"▶ {text}", objectName="primary")
        self.button.clicked.connect(self.press)
        self.state = QLabel("")
        self.state.setObjectName("mono")
        self.state.setWordWrap(True)
        row = QHBoxLayout()
        row.addWidget(self.button)
        row.addStretch(1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(row)
        lay.addWidget(self.state)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)

    def press(self) -> None:
        """Confirm, then queue; a refusal or a daemon error is said under the button."""
        sentence = self.confirm()
        if sentence is None:
            return
        if QMessageBox.question(self, "Confirmar", sentence) != QMessageBox.Yes:
            return
        self.button.setEnabled(False)
        self.state.setText("enviando…")
        background.post(self.path, self.body(), self.queued, owner=self)

    def queued(self, got: dict) -> None:
        """The daemon answered: follow the job, or say why it was refused."""
        if "error" in got or "id" not in got:
            self.button.setEnabled(True)
            self.say(got.get("error", "el demonio no devolvió un trabajo"), C["dead"])
            return
        self.job = got["id"]
        self.say(f"en cola · log {got['log']}", C["accent"])
        self.timer.start(POLL_MS)

    def poll(self) -> None:
        """Ask the job list off the GUI thread."""
        background.get("jobs", self.landed, key=f"jobbutton:{id(self)}", owner=self)

    def landed(self, got: dict) -> None:
        """Paint the job's state; on its end, stop polling and hand it over."""
        job = next((j for j in got.get("jobs", []) if j["id"] == self.job), None)
        if job is None:
            return
        tail = [line for line in job.get("tail", []) if line.strip()]
        lifted = [line for line in tail if line.startswith(FLAGS)]
        text = f"{job.get('state') or 'en marcha'}\n" + "\n".join((lifted or tail)[-4:])
        if job["rc"] is None:
            self.say(text, C["accent"])
            return
        self.timer.stop()
        self.button.setEnabled(True)
        self.say(text, C["promising"] if job["rc"] == 0 else C["dead"])
        self.ended(job)

    def say(self, text: str, colour: str) -> None:
        """The line under the button, in a colour."""
        self.state.setText(text)
        self.state.setStyleSheet(f"color: {colour};")
