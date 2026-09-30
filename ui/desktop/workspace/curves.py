"""Two cumulative equity curves on one axis, SQX's and the real-cost one, each switchable."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks.axis import ticks as round_ticks
from ui.desktop.blocks.states import CURVE
from ui.text.numbers import num
from ui.desktop.theme import C, MONO, T

FACE = MONO.split(",")[0].strip('"')
INK = {"sqx": C["accent"], "real": C["weak"]} | CURVE     # "sqx.IS", "real.OOS"…: per sample
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


class SampleCurves(Curves):
    """One strategy's equity: each curve in its IS tone up to the boundary and its OOS tone
    after it, round money ticks on y and one tick per calendar year on x (the Estrategia page)."""

    def __init__(self, height: int) -> None:
        """Start empty at a fixed height."""
        super().__init__(height)
        self.days: list[str] = []

    def fill(self, sqx: list[float], real: list[float], split: int | None = None,
             days: list[str] = ()) -> None:
        """Replace both curves.

        Args:
            sqx, real, split: As `Curves.fill`.
            days: "YYYY-MM-DD" per point, which place the year ticks.
        """
        self.days = list(days)
        super().fill(sqx, real, split)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """Draw the grid, the ticks, the boundary and the visible curves in their sample's tone.

        Args:
            event: Qt's paint event, unused.
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        font = QFont(FACE, 9, QFont.Bold)
        values = [v for k, s in self.series.items() if self.shown[k] for v in s] or [0.0]
        lo, hi = min(values + [0.0]), max(values + [0.0])
        ys = sorted(set(round_ticks(lo, hi, 7)) | {0.0})
        lo, hi = min(ys + [lo]), max(ys + [hi])
        gutter = max(QFontMetrics(font).horizontalAdvance(num(v)) for v in ys) + 10
        box = QRectF(gutter + 6, 10, self.width() - gutter - 18, self.height() - 34)
        p.setPen(QPen(QColor(T["rule"]), 1))
        p.drawRect(box)
        n = len(self.series.get("sqx", []))
        if n < 2:
            return
        def at(i: int, v: float) -> QPointF:
            """Screen point of day i at value v."""
            return QPointF(box.left() + box.width() * i / (n - 1),
                           box.bottom() - box.height() * (v - lo) / (hi - lo or 1))
        p.setFont(font)
        for v in ys:
            y = at(0, v).y()
            p.setPen(QPen(QColor(T["line"]), 1, Qt.DashLine if v == 0.0 else Qt.SolidLine))
            p.drawLine(QPointF(box.left(), y), QPointF(box.right(), y))
            p.setPen(QColor(T["muted"]))
            p.drawText(QRectF(0, y - 8, gutter, 16), Qt.AlignRight | Qt.AlignVCenter, num(v))
        years = [i for i, d in enumerate(self.days) if i == 0 or d[:4] != self.days[i - 1][:4]]
        written = 1e9     # right to left: a partial first year gives way to the next one
        for i in reversed(years):
            x = at(i, lo).x()
            p.setPen(QPen(QColor(T["line"]), 1))
            p.drawLine(QPointF(x, box.top()), QPointF(x, box.bottom()))
            if written - x >= 46:
                written = x
                p.setPen(QColor(T["muted"]))
                p.drawText(QRectF(x - 22, box.bottom() + 4, 44, 16), Qt.AlignHCenter,
                           self.days[i][:4])
        split = self.split if self.split is not None else n - 1
        if self.split is not None:
            x = at(split, lo).x()
            p.setPen(QPen(QColor(T["text"]), 1, Qt.DashLine))
            p.drawLine(QPointF(x, box.top()), QPointF(x, box.bottom()))
            p.drawText(QRectF(x - 90, box.top() + 2, 84, 16), Qt.AlignRight, "IS ◂")
            p.drawText(QRectF(x + 6, box.top() + 2, 84, 16), Qt.AlignLeft, "▸ OOS1")
        for key, s in self.series.items():
            if not (self.shown[key] and len(s) > 1):
                continue
            for part, span in (("IS", range(0, split + 1)), ("OOS", range(split, len(s)))):
                if len(span) > 1:
                    p.setPen(QPen(QColor(INK[f"{key}.{part}"]), 1.6))
                    p.drawPolyline(QPolygonF([at(i, s[i]) for i in span]))
