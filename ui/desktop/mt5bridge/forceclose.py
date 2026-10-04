"""The button for a wedged-open MT5 terminal: close it well if possible, kill it if not."""
from collections.abc import Callable

from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from ui.desktop import background
from ui.desktop.blocks.card import text
from ui.desktop.theme import T


class ForceClose(QWidget):
    """A button that posts to `mt5bridge/close-terminal` off the GUI thread and says how it went."""

    def __init__(self, send: Callable[[str, dict], dict]) -> None:
        """Args:
            send: POST a daemon route, never raising.
        """
        super().__init__()
        self.send = send
        self.button = QPushButton("Forzar cierre de MT5 (corta los backtests en curso)")
        # Destructive and rare: it must not weigh what «Verificar» weighs beside it.
        self.button.setStyleSheet(f"QPushButton {{ background: transparent; color: {T['muted']};"
                                  f" border: 1px solid {T['line']}; font-weight: 400; }}")
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
        background.run(lambda: self.send("mt5bridge/close-terminal", {}), self._after, owner=self)

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
