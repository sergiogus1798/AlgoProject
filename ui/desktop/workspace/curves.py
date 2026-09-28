"""Two cumulative equity curves on one axis, SQX's and the real-cost one, each switchable."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from ui.text.numbers import num
from ui.desktop.theme import C, MONO, T

FACE = MONO.split(",")[0].strip('"')
INK = {"sqx": C["accent"], "real": C["weak"]}
NAME = {"sqx": "SQX", "real": "spread y slippage reales"}


class Curves(QWidget):
    """The equity of a strategy or a databank. `shown` says which series are drawn; the
    segment boundary, when given, is a dashed line labelled on both sides."""

    def __init__(self, height: int) -> None:
        """Start empty at a fixed height."""
        super().__init__()
        self.series: dict[str, list[float]] = {}
        self.shown = {"sqx": True, "real": True}
        self.split: int | None = None
        self.setMinimumHeight(height)

    def fill(self, sqx: list[float], real: list[float], split: int | None = None) -> None:
        """Replace both curves.

        Args:
            sqx: Cumulative daily P&L as SQX computed it.
            real: The same, with the real spread and slippage.
            split: Index where OOS1 starts, or None for a databank aggregate.
        """
        self.series, self.split = {"sqx": sqx, "real": real}, split
        self.update()

    def toggle(self, key: str, on: bool) -> None:
        """Show or hide one series."""
        self.shown[key] = on
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """Draw the axis, the zero line, the boundary and the visible curves.

        Args:
            event: Qt's paint event, unused.
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        font = QFont(FACE, 9, QFont.Bold)
        values = [v for k, s in self.series.items() if self.shown[k] for v in s] or [0.0]
        lo, hi = min(values + [0.0]), max(values + [0.0])
        # The axis is as wide as its widest figure: a fixed 58 px cut «1.808.633» to «.808.633».
        ticks = {v: num(v) for v in (lo, 0.0, hi)}
        gutter = max(QFontMetrics(font).horizontalAdvance(t) for t in ticks.values()) + 10
        box = QRectF(gutter + 6, 10, self.width() - gutter - 18, self.height() - 34)
        p.setPen(QPen(QColor(T["rule"]), 1))
        p.drawRect(box)
        if not self.series:
            return
        n = len(self.series["sqx"])
        def at(i: int, v: float) -> QPointF:
            """Screen point of day i at value v."""
            return QPointF(box.left() + box.width() * i / max(n - 1, 1),
                           box.bottom() - box.height() * (v - lo) / (hi - lo or 1))
        p.setFont(font)
        p.setPen(QColor(T["muted"]))
        for v, shown in ticks.items():
            if v == 0.0 and min(abs(at(0, 0.0).y() - at(0, x).y()) for x in (lo, hi)) < 16:
                continue
            p.drawText(QRectF(0, at(0, v).y() - 8, gutter, 16), Qt.AlignRight | Qt.AlignVCenter,
                       shown)
        p.setPen(QPen(QColor(T["line"]), 1, Qt.DashLine))
        p.drawLine(at(0, 0.0), at(n - 1, 0.0))
        if self.split is not None:
            x = at(self.split, lo).x()
            p.setPen(QPen(QColor(T["faint"]), 1, Qt.DashLine))
            p.drawLine(QPointF(x, box.top()), QPointF(x, box.bottom()))
            p.setPen(QColor(T["muted"]))
            p.drawText(QRectF(x - 90, box.bottom() + 4, 84, 16), Qt.AlignRight, "IS ◂")
            p.drawText(QRectF(x + 6, box.bottom() + 4, 84, 16), Qt.AlignLeft, "▸ OOS1")
        for key, s in self.series.items():
            if self.shown[key] and len(s) > 1:
                p.setPen(QPen(QColor(INK[key]), 1.6))
                p.drawPolyline(QPolygonF([at(i, v) for i, v in enumerate(s)]))
