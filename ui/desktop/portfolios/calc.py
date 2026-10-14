"""«Calcular»: ask the daemon whether the command may start, confirm when it must, queue it, follow it."""

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget

from ui.desktop import background, jobsfeed
from ui.desktop.theme import C

POLL_MS = 3000


def question(parent: QWidget, sentence: str) -> QMessageBox:
    """The confirmation of a launcher that can open oos2: «No» is the default answer."""
    box = QMessageBox(QMessageBox.Icon.Warning, "Confirmar — lectura de un solo uso", sentence,
                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, parent)
    box.setDefaultButton(QMessageBox.StandardButton.No)
    box.button(QMessageBox.StandardButton.Yes).setText("Sí, lanzar")
    box.button(QMessageBox.StandardButton.No).setText("No")
    return box


class CalcButton(QPushButton):
    """One launcher of a module's strip. Press → `portfolios/preflight` → the reasons it may
    not, or (when the daemon asks) a confirmation → `portfolios/run` → the job polled to its
    end. `say(text, colour)` gets every state; `ended(job)` fires once when it finishes."""

    def __init__(self, text: str, action: str, params: Callable[[], dict], say: Callable[[str, str], None],
                 ended: Callable[[dict], None], tip: str, primary: bool = True) -> None:
        """Build the button; nothing is asked until it is pressed."""
        super().__init__(f"▶ {text}")
        if primary:
            self.setObjectName("primary")
        self.setToolTip(tip)
        self.action, self.params, self.say, self.ended, self.job = action, params, say, ended, ""
        self.clicked.connect(self.press)
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: jobsfeed.read(self.landed, f"calc:{id(self)}", self, 0))

    def press(self) -> None:
        """Ask the daemon's preflight off the GUI thread."""
        self.setEnabled(False)
        self.say("comprobando…", C["accent"])
        background.get("portfolios/preflight", self.checked, owner=self, action=self.action, **self.params())

    def checked(self, got: dict) -> None:
        """The preflight answered: say why not, or confirm (when asked) and queue."""
        if not got.get("ok"):
            self.setEnabled(True)
            why = got.get("reasons") or [got.get("error", "el demonio no respondió")]
            return self.say("No se lanza:\n" + "\n".join(f"· {r}" for r in why), C["weak"])
        if got["confirm"] and question(self, got["text"]).exec() != QMessageBox.StandardButton.Yes:
            self.setEnabled(True)
            return self.say("No se ha lanzado nada.", C["muted"])
        body = {"action": self.action, "params": got["params"], "nonce": got["nonce"]}
        background.post("portfolios/run", body, self.queued, owner=self)

    def queued(self, got: dict) -> None:
        """The job is queued: follow it."""
        if not got.get("ok"):
            self.setEnabled(True)
            why = got.get("reasons") or [got.get("error", "el demonio no devolvió un trabajo")]
            return self.say("No se lanza:\n" + "\n".join(f"· {r}" for r in why), C["dead"])
        self.job = got["job"]
        self.say("en cola…", C["accent"])
        self.timer.start(POLL_MS)

    def landed(self, got: dict) -> None:
        """Paint the job's state; on its end stop polling and hand it over."""
        job = next((j for j in got.get("jobs", []) if j["id"] == self.job), None)
        if job is None:
            return
        tail = [line for line in job.get("tail", []) if line.strip()][-3:]
        if job["rc"] is None:
            return self.say(f"calculando — {job.get('state') or 'en marcha'}\n" + "\n".join(tail), C["accent"])
        self.timer.stop()
        self.setEnabled(True)
        self.say(("Terminado.\n" if job["rc"] == 0 else f"Falló (código {job['rc']}):\n") + "\n".join(tail),
                 C["promising"] if job["rc"] == 0 else C["dead"])
        self.ended(job)
