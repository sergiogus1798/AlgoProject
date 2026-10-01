"""The button for a wedged-open MT5 terminal: close it well if possible, kill it if not."""
import threading
from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from ui.desktop.blocks.card import text
from ui.desktop.theme import T


class ForceClose(QWidget):
    """A button that posts to `mt5bridge/close-terminal` off the GUI thread and says how it went."""

    closed = Signal(dict)

    def __init__(self, send: Callable[[str, dict], dict]) -> None:
        """Args:
            send: POST a daemon route, never raising.
        """
        super().__init__()
        self.send = send
        self.closed.connect(self._after)
        self.button = QPushButton("Si MT5 se queda bloqueado: forzar su cierre")
        self.button.setToolTip("Para cuando el terminal se queda abierto y ni esta ventana ni tú "
                               "podéis cerrarlo: lo cierra bien si puede, y si no lo mata. Luego "
                               "puedes volver a pulsar «Verificar».")
        self.button.clicked.connect(self._start)
        self.said = text("", T["muted"], 12)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.button)
        lay.addWidget(self.said)

    def _start(self) -> None:
        """Ask the daemon to force the terminal shut, off the GUI thread."""
        self.button.setEnabled(False)
        self.said.setText("cerrando MT5…")
        threading.Thread(target=lambda: self.closed.emit(self.send("mt5bridge/close-terminal",
                                                                    {})),
                         daemon=True).start()

    def _after(self, got: dict) -> None:
        """Say how it went; re-enable the button either way."""
        self.button.setEnabled(True)
        if "error" in got:
            self.said.setText(got["error"])
        elif not got["closed"]:
            self.said.setText("no se ha podido cerrar MT5")
        else:
            how = "matado" if got["forced"] else "cerrado"
            warning = f" ({got['warning']})" if got.get("warning") else ""
            self.said.setText(f"MT5 {how}{warning}")
