"""The lines block: several series over one x axis, each in the colour of its role."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card
from ui.desktop.blocks.states import CURVE, REAL, SERIES, colour
from ui.desktop.theme import T

# Past six drawn series the hues repeat, so the pen style changes with each lap — except
# under `auto_dash_negative`, where the style is the sign's alone.
STYLES = (Qt.SolidLine, Qt.DashDotLine, Qt.DotLine)


def _ends_negative(s: dict) -> bool:
    """Whether a series' last known value sits below zero."""
    last = next((v for v in reversed(s["values"]) if v is not None), None)
    return last is not None and last < 0


def _pens(b: dict) -> list[tuple[str, Qt.PenStyle, float]]:
    """(colour, style, width) per series: one naming an `ink` of `CURVE` in it (dashed with
    `dash`), a lone real series in the real ink, references grey, the rest in the fixed
    series order.

    With `auto_dash_negative` (owner's rule) the style follows the sign and nothing else, for
    every series, the reference included: a curve that ends below zero is dashed, one that
    ends at or above it solid. Colours may cycle past six series; styles never do. Without
    it, references are dashed and past six series each lap of colours changes the style."""
    drawn = [s for s in b["series"] if s["role"] != "reference"]
    auto = b.get("auto_dash_negative")
    out, k = [], 0
    for s in b["series"]:
        signed = Qt.DashLine if _ends_negative(s) else Qt.SolidLine
        if s.get("ink"):
            style = signed if auto else (Qt.DashLine if s.get("dash") else Qt.SolidLine)
            out.append((CURVE[s["ink"]], style, 2.0))
            continue
        if s["role"] == "reference":
            out.append((T["muted"], signed if auto else Qt.DashLine, 2.0 if auto else 1.5))
            continue
        lap = Qt.SolidLine if len(drawn) == 1 else STYLES[k // len(SERIES) % 3]
        style = signed if auto else lap
        if len(drawn) == 1:
            out.append((REAL if s["role"] == "real" else SERIES[0], style, 2.5))
        else:
            out.append((SERIES[k % len(SERIES)], style, 2.5 if s["role"] == "real" else 1.8))
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
        if b.get("zero_shade") and lo < 0 < hi:
            above, below = QColor(colour("pass")), QColor(colour("fail"))
            above.setAlphaF(0.08)
            below.setAlphaF(0.08)
            p.fillRect(QRectF(box.left(), box.top(), box.width(), y(0) - box.top()), above)
            p.fillRect(QRectF(box.left(), y(0), box.width(), box.bottom() - y(0)), below)
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
        rows = [f"x = {chart.num(b['x'][i])}"]
        rows += [f"{s['label']}: {chart.num(s['values'][i], b['unit'])}" for s in b["series"]]
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
