"""The bar that walks a saved workflow's strategies one by one: «anterior», where you are, «siguiente»."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ui.desktop.theme import T


class SeriesBar(QWidget):
    """`step(i)` asks the page to open the i-th strategy of the series."""

    step = Signal(int)

    def __init__(self) -> None:
        """Build it hidden; `show_at` fills it."""
        super().__init__()
        self.index, self.total = 0, 0
        self.prev, self.next = QPushButton("◀ anterior"), QPushButton("siguiente ▶")
        self.where = QLabel("", objectName="mono")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.where.setStyleSheet(f"font-size: 14px; color: {T['text']};")
        for button, delta in ((self.prev, -1), (self.next, 1)):
            button.setToolTip("Pasa a la estrategia vecina del workflow sin volver a la lista.")
            button.clicked.connect(lambda _=False, d=delta: self.step.emit(self.index + d))
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        for w in (self.prev, self.next, self.where):
            row.addWidget(w)
        row.addStretch(1)
        self.hide()

    def show_at(self, workflow: str, index: int, total: int) -> None:
        """Put the bar at one place of a series.

        Args:
            workflow: The workflow's folder name.
            index: Zero-based position on screen.
            total: How many strategies the series has.
        """
        self.index, self.total = index, total
        self.prev.setEnabled(index > 0)
        self.next.setEnabled(index < total - 1)
        self.where.setText(f"estrategia {index + 1} de {total} · {workflow}")
        self.setVisible(total > 1)
