"""The lines block: several series over one x axis, each in the colour of its role."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card
from ui.desktop.blocks.states import REAL, SERIES
from ui.desktop.theme import T

# Past six drawn series the hues repeat, so the pen style changes with each lap.
STYLES = (Qt.SolidLine, Qt.DashDotLine, Qt.DotLine)


def _pens(b: dict) -> list[tuple[str, Qt.PenStyle, float]]:
    """(colour, style, width) per series: a lone real series in the real ink, references
    dashed grey, the rest in the fixed series order."""
    drawn = [s for s in b["series"] if s["role"] != "reference"]
    out, k = [], 0
    for s in b["series"]:
        if s["role"] == "reference":
            out.append((T["muted"], Qt.DashLine, 1.5))
            continue
        if len(drawn) == 1:
            out.append((REAL if s["role"] == "real" else SERIES[0], Qt.SolidLine, 2.5))
        else:
            out.append((SERIES[k % len(SERIES)], STYLES[k // len(SERIES) % 3],
                        2.5 if s["role"] == "real" else 1.8))
            k += 1
    return out


def _range(b: dict) -> tuple[float, float]:
    """The y range over every series."""
    v = [y for s in b["series"] for y in s["values"] if y is not None]
    margin = 0.06 * (max(v) - min(v))   # so no mark sits on the frame
    return min(v) - margin, max(v) + margin


def _draw(b: dict) -> Callable:
    """The painter of one line chart."""
    pens = _pens(b)

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        box = chart.area(rect)
        px, xt = axis.xaxis(b["x"], box.left(), box.right())
        lo, hi = _range(b)
        y = axis.scale(lo, hi, box.bottom(), box.top())
        chart.axes(p, box, xt, [(y(v), chart.num(v)) for v in axis.ticks(lo, hi, 5)])
        p.setBrush(Qt.NoBrush)
        for s, (c, style, width) in zip(b["series"], pens):
            p.setPen(QPen(QColor(c), width, style))
            p.drawPath(axis.curve(px, s["values"], y))
            if len(px) <= 40:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(c))
                for a, v in zip(px, s["values"]):
                    if v is not None:
                        p.drawEllipse(QPointF(a, y(v)), 3.5, 3.5)
                p.setBrush(Qt.NoBrush)
        if hover is not None and box.contains(hover):
            chart.vline(p, px[axis.nearest(px, hover.x())], box, T["faint"], 1)

    return draw


def _tip(b: dict) -> Callable:
    """Every series' value at the point under the pointer."""

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        box = chart.area(rect)
        if not box.contains(pos):
            return None
        px, _ = axis.xaxis(b["x"], box.left(), box.right())
        i = axis.nearest(px, pos.x())
        unit = f" {b['unit']}" if b["unit"] else ""
        rows = [f"x = {chart.num(b['x'][i])}"]
        rows += [f"{s['label']}: {chart.num(s['values'][i])}{unit}" for s in b["series"]]
        return "\n".join(rows[:16])

    return tip


def widget(block: dict) -> QWidget:
    """One line chart, drawn and explained.

    Args:
        block: A contract `lines` block.

    Returns:
        The framed chart, with a key when there is more than one series.
    """
    b = block
    canvas = chart.Canvas(_draw(b), _tip(b))
    if len(b["series"]) == 1:
        return card(b, canvas)
    marks = {Qt.SolidLine: "line", Qt.DashLine: "dash"}
    key = chart.key([(marks.get(style, "dash"), c, s["label"])
                     for s, (c, style, _) in zip(b["series"], _pens(b))])
    return card(b, canvas, key)
