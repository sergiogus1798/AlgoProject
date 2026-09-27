"""The scatter block: points by group, the quadrants through zero and the fitted line if any."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card
from ui.desktop.blocks.states import SERIES
from ui.desktop.theme import T


def _maps(b: dict, box: QRectF) -> tuple[Callable, Callable, tuple, tuple]:
    """The two data-to-pixel maps and the two data ranges."""
    xs = [p["x"] for p in b["points"]]
    ys = [p["y"] for p in b["points"]]
    sx, sy = (min(xs), max(xs)), (min(ys), max(ys))
    return (axis.scale(*sx, box.left(), box.right()), axis.scale(*sy, box.bottom(), box.top()),
            sx, sy)


def _groups(b: dict) -> list[str]:
    """The groups in a fixed order, so a colour follows its group."""
    return sorted({p["group"] for p in b["points"]})


def _draw(b: dict) -> Callable:
    """The painter of one scatter."""
    groups = _groups(b)

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        box = chart.area(rect)
        x, y, sx, sy = _maps(b, box)
        chart.axes(p, box, [(x(v), chart.num(v)) for v in axis.ticks(*sx)],
                   [(y(v), chart.num(v)) for v in axis.ticks(*sy, 5)])
        p.setFont(chart.font(11, True))
        p.setPen(QColor(T["text"]))
        p.drawText(QRectF(box.left(), rect.bottom() - 20, box.width(), 18), Qt.AlignHCenter,
                   b["x_label"])
        p.save()
        p.translate(14, box.center().y())
        p.rotate(-90)
        p.drawText(QRectF(-box.height() / 2, -9, box.height(), 18), Qt.AlignHCenter,
                   b["y_label"])
        p.restore()
        if b["quadrants"]:
            p.setPen(QPen(QColor(T["muted"]), 1.2))
            if sx[0] < 0 < sx[1]:
                p.drawLine(QPointF(x(0), box.top()), QPointF(x(0), box.bottom()))
            if sy[0] < 0 < sy[1]:
                p.drawLine(QPointF(box.left(), y(0)), QPointF(box.right(), y(0)))
        p.setPen(QPen(QColor(T["bg"]), 1.5))
        for pt in b["points"]:
            p.setBrush(QColor(SERIES[groups.index(pt["group"]) % len(SERIES)]))
            p.drawEllipse(QPointF(x(pt["x"]), y(pt["y"])), 5, 5)
        if b["fit"]:
            f = b["fit"]
            p.setPen(QPen(QColor(T["text"]), 1.5, Qt.DashLine))
            p.drawLine(QPointF(x(sx[0]), y(f["intercept"] + f["slope"] * sx[0])),
                       QPointF(x(sx[1]), y(f["intercept"] + f["slope"] * sx[1])))

    return draw


def _tip(b: dict) -> Callable:
    """The point nearest the pointer, within a few pixels."""

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        x, y, _, _ = _maps(b, chart.area(rect))

        def gap(p: dict) -> float:
            """Squared pixel distance from the pointer to a point."""
            return (x(p["x"]) - pos.x()) ** 2 + (y(p["y"]) - pos.y()) ** 2

        near = min(b["points"], key=gap)
        if gap(near) > 64:
            return None
        return (f"{near['label']} · {near['group']}\n{b['x_label']}: {chart.num(near['x'])}\n"
                f"{b['y_label']}: {chart.num(near['y'])}")

    return tip


def widget(block: dict) -> QWidget:
    """One scatter, drawn and explained.

    Args:
        block: A contract `scatter` block.

    Returns:
        The framed chart and its key.
    """
    b = block
    items = [("box", SERIES[i % len(SERIES)], g) for i, g in enumerate(_groups(b))]
    if b["fit"]:
        f = b["fit"]
        items.append(("dash", T["text"], f"recta ajustada, pendiente {chart.num(f['slope'])}, "
                                         f"r = {f['r']:.3f}"))
    return card(b, chart.Canvas(_draw(b), _tip(b)), chart.key(items))
