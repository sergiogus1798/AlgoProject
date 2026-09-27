"""The parallel-coordinates canvas: one axis per parameter plus the outcome, one line per variant."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap,
                           QResizeEvent)
from PySide6.QtWidgets import QToolTip, QWidget

from ui.desktop.batchview import scale
from ui.desktop.blocks.axis import scale as linear
from ui.desktop.blocks.axis import ticks
from ui.desktop.blocks.chart import font, num
from ui.desktop.blocks.states import REAL
from ui.desktop.theme import T

HEIGHT = 480
PAD = {"l": 96, "r": 100, "t": 44, "b": 30}
NEAR = 7                          # pixels: how close the pointer must be to pick a line


def layout(batch: dict, metric: str, box: QRectF) -> tuple[list[float], list]:
    """Where each axis stands and the pixel map of each.

    Args:
        batch: The `/api/batch` answer.
        metric: The outcome drawn on the last axis and used for colour.
        box: The plotting rectangle.

    Returns:
        (x per axis, [(label, values, y-map, ticks)] per axis).
    """
    cols = [(a["label"], a["values"]) for a in batch["axes"]] + [(metric, batch["outcomes"][metric])]
    xs = [box.left() + i * box.width() / max(1, len(cols) - 1) for i in range(len(cols))]
    out = []
    for label, vals in cols:
        seen = sorted({v for v in vals if v is not None})
        lo, hi = seen[0], seen[-1]
        tk = seen if len(seen) <= 8 else ticks(lo, hi)
        out.append((label, vals, linear(lo, hi, box.bottom(), box.top()), tk))
    return xs, out


class Parallel(QWidget):
    """The painted chart. Lines are painted once into a pixmap; hover repaints only the one
    line under the pointer, so a few thousand variants stay responsive."""

    def __init__(self) -> None:
        """An empty canvas; `set_batch` fills it."""
        super().__init__()
        self.batch, self.outcome, self.cache, self.hot = None, "", None, None
        self.setFixedHeight(HEIGHT)
        self.setMinimumWidth(520)
        self.setMouseTracking(True)

    def set_batch(self, batch: dict, metric: str) -> None:
        """Draw a batch coloured and ranked by one outcome.

        Args:
            batch: The `/api/batch` answer, without `error`.
            metric: "NetProfit (oos1)" or "NetProfit (build)".
        """
        self.batch, self.outcome, self.cache, self.hot = batch, metric, None, None
        self.update()

    def box(self) -> QRectF:
        """The plotting rectangle."""
        return QRectF(self.rect()).adjusted(PAD["l"], PAD["t"], -PAD["r"], -PAD["b"])

    def points(self, i: int, xs: list[float], cols: list) -> list[QPointF | None]:
        """One variant's point on every axis, None where its value is missing."""
        return [None if c[1][i] is None else QPointF(x, c[2](c[1][i])) for x, c in zip(xs, cols)]

    def polyline(self, p: QPainter, pts: list[QPointF | None]) -> None:
        """The segments between consecutive known points."""
        for a, b in zip(pts, pts[1:]):
            if a is not None and b is not None:
                p.drawLine(a, b)

    def paint_lines(self) -> QPixmap:
        """Axes and every variant, worst first so the best lie on top; the mother last."""
        ratio = self.devicePixelRatioF()
        pix = QPixmap(self.size() * ratio)
        pix.setDevicePixelRatio(ratio)
        pix.fill(QColor(T["bg"]))
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        box, vals = self.box(), self.batch["outcomes"][self.outcome]
        xs, cols = layout(self.batch, self.outcome, box)
        cuts = scale.edges(vals)
        n = len(vals)
        alpha, width = (0.9, 1.6) if n <= 150 else (max(0.18, min(0.7, 150 / n)), 1.0)
        order = sorted(range(n), key=lambda i: -1e300 if vals[i] is None else vals[i])
        for i in order:
            c = QColor(scale.colour(vals[i], cuts))
            c.setAlphaF(alpha)
            p.setPen(QPen(c, width))
            self.polyline(p, self.points(i, xs, cols))
        self.paint_axes(p, xs, cols)
        if self.batch["mother"] is not None:
            pts = self.points(self.batch["mother"], xs, cols)
            p.setPen(QPen(QColor(T["bg"]), 6))
            self.polyline(p, pts)
            pen = QPen(QColor(REAL), 3)
            pen.setStyle(Qt.DashLine)
            p.setPen(pen)
            self.polyline(p, pts)
            p.setBrush(QColor(REAL))
            for pt in (pt for pt in pts if pt is not None):
                p.drawEllipse(pt, 4, 4)
        p.end()
        return pix

    def paint_axes(self, p: QPainter, xs: list[float], cols: list) -> None:
        """Each axis as a rule, its name above and its values beside it."""
        box = self.box()
        for k, (x, (label, _, y, tk)) in enumerate(zip(xs, cols)):
            last = k == len(cols) - 1
            p.setPen(QPen(QColor(T["text"] if last else T["rule"]), 2 if last else 1.5))
            p.drawLine(QPointF(x, box.top()), QPointF(x, box.bottom()))
            p.setFont(font(10, bold=True))
            p.setPen(QColor(T["text"]))
            p.drawText(QRectF(x - 80, 4, 160, 34), Qt.AlignHCenter | Qt.AlignBottom
                       | Qt.TextWordWrap, label)
            p.setFont(font(9))
            p.setPen(QColor(T["muted"]))
            for v in tk:
                r = (QRectF(x + 6, y(v) - 8, 80, 16) if last
                     else QRectF(x - 66, y(v) - 8, 60, 16))
                p.fillRect(r.adjusted(2, 1, -2, -1) if last else
                           r.adjusted(60 - 7 * len(num(v)), 1, 0, -1), QColor(T["bg"]))
                p.drawText(r, (Qt.AlignLeft if last else Qt.AlignRight) | Qt.AlignVCenter, num(v))

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """The cached lines, and the hovered variant on top in the brightest ink."""
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(T["bg"]))
        if self.batch is None:
            return
        if self.cache is None or self.cache.size() != self.size() * self.devicePixelRatioF():
            self.cache = self.paint_lines()
        p.drawPixmap(0, 0, self.cache)
        if self.hot is not None:
            p.setRenderHint(QPainter.Antialiasing)
            xs, cols = layout(self.batch, self.outcome, self.box())
            p.setPen(QPen(QColor(REAL), 2.5))
            self.polyline(p, self.points(self.hot, xs, cols))

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 — Qt's name
        """Repaint the lines at the new size."""
        self.cache = None
        super().resizeEvent(event)

    def nearest(self, at: QPointF) -> int | None:
        """The variant whose line passes closest to the pointer, within `NEAR` pixels."""
        xs, cols = layout(self.batch, self.outcome, self.box())
        if not xs[0] <= at.x() <= xs[-1]:
            return None
        k = min(len(xs) - 2, max(0, int((at.x() - xs[0]) / (xs[1] - xs[0])))) if len(xs) > 1 else 0
        t = (at.x() - xs[k]) / (xs[k + 1] - xs[k]) if len(xs) > 1 else 0
        best, gap = None, NEAR
        for i in range(len(self.batch["variants"])):
            a, b = cols[k][1][i], cols[min(k + 1, len(cols) - 1)][1][i]
            if a is None or b is None:
                continue
            d = abs(cols[k][2](a) * (1 - t) + cols[min(k + 1, len(cols) - 1)][2](b) * t - at.y())
            if d < gap:
                best, gap = i, d
        return best

    def sentence(self, i: int) -> str:
        """What one variant is: its name, stratum, every parameter and both outcomes."""
        b = self.batch
        mother = " — la madre" if i == b["mother"] else ""
        rows = [f"{b['variants'][i]} ({b['stratum'][i]}){mother}"]
        rows += [f"{a['label']} = {num(a['values'][i])}" for a in b["axes"]]
        rows += [f"{o} = {num(v[i])}" for o, v in b["outcomes"].items()]
        return "\n".join(rows)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt's name
        """Light the line under the pointer and say its values."""
        if self.batch is None:
            return
        hot = self.nearest(event.position())
        if hot != self.hot:
            self.hot = hot
            self.update()
        if hot is None:
            QToolTip.hideText()
        else:
            QToolTip.showText(event.globalPosition().toPoint(), self.sentence(hot), self)

    def leaveEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Drop the lit line when the pointer leaves."""
        self.hot = None
        self.update()
