"""The two locks above the rail: how often oos2 has been looked at, and whether 17-19 are sealed."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.theme import C, T
from ui.desktop.workflow.steprow import FACE, envelope

CELL = 34      # one look, one cell: a discrete count, never a bar to interpolate
HEIGHT = 92


class Oos2Gauge(QWidget):
    """One cell per look at oos2, labelled with the step that looked: amber when the step is
    one the policy reserves it for, red when it is not. Empty and green while virgin."""

    def __init__(self) -> None:
        """Start empty."""
        super().__init__()
        self.data: dict = {}
        self.asset = ""
        self.setFixedHeight(HEIGHT)

    def fill(self, oos2: dict, asset: str | None) -> None:
        """Replace the gauge.

        Args:
            oos2: The route's `oos2` block.
            asset: The project's asset, for the title.
        """
        self.data, self.asset = oos2, asset or "?"
        self.setToolTip(oos2["text"] + "\n\nCada celda es una lectura apuntada en el ledger; "
                        "ámbar = paso al que la política reserva oos2, rojo = paso fuera de "
                        "la reserva.")
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """Draw the title, the cells and the reserve line.

        Args:
            event: Qt's paint event, unused.
        """
        if not self.data:
            return
        d, w = self.data, self.width()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setFont(QFont(FACE, 10, QFont.Bold))
        p.setPen(QColor(T["text"]))
        p.drawText(QRectF(8, 2, w - 16, 20), Qt.AlignVCenter | Qt.AlignLeft,
                   f"OOS2 · {self.asset}")
        word, ink = (("VIRGEN", C["promising"]) if d["virgin"] else
                     (f"GASTADO · {d['looks']} MIRADAS", C["weak"]))
        p.setPen(QColor(ink))
        p.drawText(QRectF(8, 2, w - 16, 20), Qt.AlignVCenter | Qt.AlignRight, word)
        looks = [step for step, n in d["by_step"].items() for _ in range(n)]
        fits = max(1, int((w - 16) // (CELL + 3)))
        if not looks:
            p.setPen(QPen(QColor(C["promising"]), 2, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(8, 28, w - 16, 28))
            p.drawText(QRectF(8, 28, w - 16, 28), Qt.AlignCenter, "sin miradas")
        for i, step in enumerate(looks[:fits]):
            box = QRectF(8 + i * (CELL + 3), 28, CELL, 28)
            fill = C["weak"] if step in d["reserved_for"] else C["dead"]
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(fill))
            p.drawRect(box)
            p.setPen(QColor(T["bg"]))
            p.setFont(QFont(FACE, 9, QFont.Bold))
            p.drawText(box, Qt.AlignCenter, step if len(looks) <= fits or i < fits - 1
                       else f"+{len(looks) - fits + 1}")
        p.setFont(QFont(FACE, 9, QFont.Bold))
        p.setPen(QColor(T["muted"]))
        p.drawText(QRectF(8, 62, w - 16, 22), Qt.AlignVCenter | Qt.AlignLeft,
                   "reservado a " + " · ".join(d["reserved_for"]) + " · sin tope de miradas")


class BlindBanner(QWidget):
    """Steps 17, 18 and 19: an envelope while the ledger keeps them sealed, open when all
    three have run — the owner's rule that the three are read at once or not at all."""

    def __init__(self) -> None:
        """Start empty."""
        super().__init__()
        self.data: dict = {}
        self.setFixedHeight(44)

    def fill(self, blind: dict) -> None:
        """Replace the banner.

        Args:
            blind: The route's `blind` block.
        """
        self.data = blind
        self.setToolTip(blind["text"])
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """Draw the envelope and what it says.

        Args:
            event: Qt's paint event, unused.
        """
        if not self.data:
            return
        sealed = self.data["sealed"]
        ink = C["weak"] if sealed else C["promising"]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        box = QRectF(12, 16, 26, 18)
        if sealed:
            envelope(p, box, ink)
        else:   # the flap folded back up: the body, and a V pointing away from it
            p.setPen(QPen(QColor(ink), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRect(box)
            p.drawPolyline([box.topLeft(), QPointF(box.center().x(), box.top() - 10),
                            box.topRight()])
        p.setFont(QFont(FACE, 10, QFont.Bold))
        p.setPen(QColor(ink))
        done = ", ".join(self.data["done"]) or "ninguno"
        p.drawText(QRectF(50, 0, self.width() - 58, 44), Qt.AlignVCenter | Qt.AlignLeft,
                   f"17 · 18 · 19 SELLADOS — hechos: {done}" if sealed
                   else "17 · 18 · 19 ABIERTOS — se leen a la vez")
