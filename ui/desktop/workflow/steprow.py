"""One step of the rail, painted: the node on the line, number, title, kind, state and funnel."""

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.theme import C, MONO, T
from ui.desktop.workflow.states import KIND_HELP, KIND_LABEL, colour, label

ROW = 50
LINE_X = 22
FACE = MONO.split(",")[0].strip('"')


def envelope(p: QPainter, box: QRectF, ink: str) -> None:
    """A sealed envelope: the body and the flap's V, the mark of a result held back.

    Args:
        p: An active painter.
        box: Where to draw it.
        ink: Its colour.
    """
    p.setPen(QPen(QColor(ink), 2))
    p.setBrush(QColor(T["bg"]))
    p.drawRect(box)
    p.drawPolyline([box.topLeft(), QPointF(box.center().x(), box.center().y() + 1),
                    box.topRight()])


def tooltip(step: dict) -> str:
    """Everything the row abbreviates, in words: state, why, funnel, day and studies."""
    funnel = ("" if step["in"] is None and step["out"] is None else
              f"\nEmbudo: entraron {step['in'] if step['in'] is not None else '—'}, "
              f"salieron {step['out'] if step['out'] is not None else '—'}.")
    return (f"Paso {step['n']} · {step['title']} — {label(step['state'])}\n"
            f"{KIND_HELP.get(step['kind'], step['kind'])}\n\n{step['why']}{funnel}"
            + (f"\nDía: {step['day']}" if step["day"] else "")
            + (f"\nEstudios: {', '.join(step['studies'])}" if step["studies"] else ""))


class StepRow(QWidget):
    """One step. Clicking it emits `clicked(dict)` with the step as the daemon sent it."""

    clicked = Signal(dict)

    def __init__(self, step: dict, first: bool, last: bool) -> None:
        """Hold the step and whether the rail's line starts or ends here."""
        super().__init__()
        self.step, self.first, self.last, self.chosen = step, first, last, False
        self.setFixedHeight(ROW)
        self.setMinimumWidth(340)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip(step))

    def choose(self, on: bool) -> None:
        """Mark this row as the one open, or not."""
        self.chosen = on
        self.update()

    def node(self, p: QPainter, ink: str) -> None:
        """The step's mark on the line, one shape per state so it reads without colour."""
        c = QPointF(LINE_X, ROW / 2)
        state = self.step["state"]
        if state == "sealed":
            envelope(p, QRectF(c.x() - 11, c.y() - 8, 22, 16), ink)
            return
        pen = QPen(QColor(ink), 2, Qt.DashLine if state == "missing" else Qt.SolidLine)
        p.setPen(pen)
        p.setBrush(QColor(ink) if state in ("done", "running", "blocked") else QColor(T["bg"]))
        p.drawEllipse(c, 8, 8)
        p.setPen(QPen(QColor(T["bg"]), 2))
        if state == "done":
            p.drawPolyline([c + QPointF(-4, 0), c + QPointF(-1, 3), c + QPointF(4, -3)])
        elif state == "blocked":
            p.drawLine(c + QPointF(-3, -3), c + QPointF(3, 3))
            p.drawLine(c + QPointF(-3, 3), c + QPointF(3, -3))
        elif state == "running":
            p.setBrush(QColor(T["bg"]))
            p.drawEllipse(c, 3, 3)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """Draw the row.

        Args:
            event: Qt's paint event, unused.
        """
        s, w = self.step, self.width()
        ink = colour(s["state"])
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.chosen:
            p.fillRect(self.rect(), QColor(T["select"]))
            p.fillRect(QRectF(0, 0, 3, ROW), QColor(C["accent"]))
        p.setPen(QPen(QColor(T["rule"]), 2))
        p.drawLine(QPointF(LINE_X, 0 if not self.first else ROW / 2),
                   QPointF(LINE_X, ROW if not self.last else ROW / 2))
        self.node(p, ink)
        p.setPen(QColor(T["text"]))
        p.setFont(QFont(FACE, 12, QFont.Bold))
        p.drawText(QRectF(42, 5, 44, 22), Qt.AlignVCenter | Qt.AlignLeft, s["n"])
        p.setFont(QFont("DejaVu Sans", 11, QFont.DemiBold))
        numbers = self.funnel_text()
        right = 120 if numbers else 8
        p.drawText(QRectF(88, 5, w - 88 - right, 22), Qt.AlignVCenter | Qt.AlignLeft,
                   p.fontMetrics().elidedText(s["title"], Qt.ElideRight, int(w - 88 - right)))
        p.setFont(QFont(FACE, 9, QFont.Bold))
        p.setPen(QColor(T["muted"]))
        p.drawText(QRectF(42, 27, 44, 18), Qt.AlignVCenter | Qt.AlignLeft,
                   KIND_LABEL.get(s["kind"], s["kind"]))
        p.setPen(QColor(ink))
        p.drawText(QRectF(88, 27, 140, 18), Qt.AlignVCenter | Qt.AlignLeft,
                   label(s["state"]).upper())
        if numbers:
            p.setFont(QFont(FACE, 11, QFont.Bold))
            p.setPen(QColor(T["text"]))
            p.drawText(QRectF(w - right, 5, right - 10, 22), Qt.AlignVCenter | Qt.AlignRight,
                       numbers)
            lost = (s["in"] or 0) - (s["out"] or 0)
            if s["in"] is not None and s["out"] is not None and lost > 0:
                p.setFont(QFont(FACE, 9, QFont.Bold))
                p.setPen(QColor(C["dead"]))
                p.drawText(QRectF(w - right, 27, right - 10, 18),
                           Qt.AlignVCenter | Qt.AlignRight, f"−{lost}")
        p.setPen(QPen(QColor(T["line"]), 1))
        p.drawLine(QPointF(42, ROW - 1), QPointF(w, ROW - 1))

    def funnel_text(self) -> str:
        """`N → M`, `→ M` or '' when the step counts nothing."""
        n_in, n_out = self.step["in"], self.step["out"]
        if n_in is None and n_out is None:
            return ""
        return f"{'' if n_in is None else n_in} → {'—' if n_out is None else n_out}".strip()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt's name
        """Open this step.

        Args:
            event: Qt's mouse event, unused.
        """
        self.clicked.emit(self.step)
