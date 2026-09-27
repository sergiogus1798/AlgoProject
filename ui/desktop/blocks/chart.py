"""The painting ground every chart block shares: the canvas, its axes, its numbers and its key."""

from collections.abc import Callable
from html import escape

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QLabel, QToolTip, QWidget

from ui.desktop.theme import T

HEIGHT = 340                      # the owner reads these from across the desk: never below 320
PAD = {"l": 84, "r": 28, "t": 18, "b": 44}
FACE = "DejaVu Sans Mono"


def font(size: int = 11, bold: bool = False) -> QFont:
    """The monospace face every figure on a chart is written in.

    Args:
        size: Point size.
        bold: True for the marks that must be found first.

    Returns:
        The font.
    """
    f = QFont(FACE, size)
    f.setBold(bold)
    return f


def num(v: float | str | None) -> str:
    """A figure as the window prints it: thousands grouped, four significant digits below.

    Args:
        v: The value, None for a missing one; text passes through.

    Returns:
        The text; an em dash for a missing value.
    """
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    a = abs(v)
    if float(v).is_integer() and a < 1e15:
        return f"{int(v):,}".replace(",", " ")
    if a >= 1000:
        return f"{v:,.0f}".replace(",", " ")
    if a >= 100:
        return f"{v:.1f}"
    return f"{v:.4g}"


def area(rect: QRectF) -> QRectF:
    """The plotting rectangle inside a canvas, leaving room for the axis labels.

    Args:
        rect: The whole canvas.

    Returns:
        The inner rectangle.
    """
    return rect.adjusted(PAD["l"], PAD["t"], -PAD["r"], -PAD["b"])


def axes(p: QPainter, box: QRectF, xt: list[tuple[float, str]],
         yt: list[tuple[float, str]]) -> None:
    """Grid lines and labels: recessive, so the data is what the eye lands on.

    Args:
        p: The painter.
        box: The plotting rectangle.
        xt, yt: (pixel, text) for each tick on each axis.
    """
    p.setFont(font(10))
    for x, text in xt:
        p.setPen(QPen(QColor(T["line"]), 1))
        p.drawLine(QPointF(x, box.top()), QPointF(x, box.bottom()))
        p.setPen(QColor(T["muted"]))
        p.drawText(QRectF(x - 60, box.bottom() + 6, 120, 18), Qt.AlignHCenter, text)
    for y, text in yt:
        p.setPen(QPen(QColor(T["line"]), 1))
        p.drawLine(QPointF(box.left(), y), QPointF(box.right(), y))
        p.setPen(QColor(T["muted"]))
        p.drawText(QRectF(0, y - 9, box.left() - 8, 18), Qt.AlignRight | Qt.AlignVCenter, text)
    p.setPen(QPen(QColor(T["rule"]), 1))
    p.drawLine(box.bottomLeft(), box.bottomRight())
    p.drawLine(box.bottomLeft(), box.topLeft())


def vline(p: QPainter, x: float, box: QRectF, colour: str, width: float = 1.5,
          style: Qt.PenStyle = Qt.SolidLine) -> None:
    """A vertical mark across the plotting rectangle.

    Args:
        p: The painter.
        x: Pixel column.
        box: The plotting rectangle.
        colour: Hex colour.
        width: Pen width in pixels.
        style: Qt pen style.
    """
    pen = QPen(QColor(colour), width)
    pen.setStyle(style)
    p.setPen(pen)
    p.drawLine(QPointF(x, box.top()), QPointF(x, box.bottom()))


def blend(colour: str, alpha: float) -> str:
    """A colour laid at some opacity over the chart's black, as the solid hex a key can print.

    Args:
        colour: Hex colour.
        alpha: Its opacity, 0..1.

    Returns:
        The hex colour of the mix.
    """
    a, b = QColor(colour), QColor(T["bg"])
    mix = [round(alpha * x + (1 - alpha) * y) for x, y in
           zip((a.red(), a.green(), a.blue()), (b.red(), b.green(), b.blue()))]
    return "#" + "".join(f"{c:02x}" for c in mix)


def key(items: list[tuple[str, str, str]]) -> QLabel:
    """The legend under a chart, as one line of rich text.

    Args:
        items: (mark, hex colour, text): mark is "box", "line" or "dash".

    Returns:
        A wrapped label.
    """
    glyph = {"box": "■", "line": "━━", "dash": "╍╍"}
    html = "&nbsp;&nbsp;&nbsp;".join(
        f'<span style="color:{c}; font-size:15px;">{glyph[m]}</span>&nbsp;'
        f'<span style="color:{T["text"]};">{escape(t)}</span>' for m, c, t in items)
    label = QLabel(html)
    label.setWordWrap(True)
    label.setStyleSheet(f"font-family:{FACE}; font-size:12px;")
    return label


class Canvas(QWidget):
    """A painted chart that explains the mark under the pointer. The drawing and the
    tooltip are two functions handed in, so each block kind stays a function of its data."""

    def __init__(self, draw: Callable[[QPainter, QRectF, QPointF | None], None],
                 tip: Callable[[QPointF, QRectF], str | None], height: int = HEIGHT) -> None:
        """Wire the two functions.

        Args:
            draw: Paints the chart into the canvas rectangle; the pointer, if over it, is
                passed for a guide line.
            tip: The sentence for the mark under the pointer, None over empty ground.
            height: Fixed pixel height.
        """
        super().__init__()
        self.draw, self.tip, self.hover = draw, tip, None
        self.setFixedHeight(height)
        self.setMinimumWidth(360)
        self.setMouseTracking(True)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """Paint the chart.

        Args:
            event: Qt's paint event, unused.
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(T["bg"]))
        self.draw(p, QRectF(self.rect()), self.hover)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt's name
        """Show the value under the pointer.

        Args:
            event: Qt's mouse event.
        """
        self.hover = event.position()
        text = self.tip(self.hover, QRectF(self.rect()))
        if text:
            QToolTip.showText(event.globalPosition().toPoint(), text, self)
        else:
            QToolTip.hideText()
        self.update()

    def leaveEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Drop the guide line when the pointer leaves.

        Args:
            event: Qt's leave event, unused.
        """
        self.hover = None
        self.update()
