"""The cone block: the simulated equity bands, the real curve on top and where the OOS starts."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card
from ui.desktop.blocks.states import MEDIAN, REAL, SIM
from ui.desktop.theme import T

FILLS = (("2.5", "97.5", 0.20), ("25", "75", 0.42))


def _range(b: dict) -> tuple[float, float]:
    """The y range over every band and the real curve."""
    v = [y for s in (*b["bands"].values(), b["real"]) for y in s if y is not None]
    margin = 0.06 * (max(v) - min(v))   # so no mark sits on the frame
    return min(v) - margin, max(v) + margin


def _split(b: dict) -> int | None:
    """The first point at or after the OOS start, None without one."""
    if b["split"] is None:
        return None
    return next((i for i, x in enumerate(b["x"]) if str(x) >= str(b["split"])), None)


def _draw(b: dict) -> Callable:
    """The painter of one cone."""

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        box = chart.area(rect)
        px, xt = axis.xaxis(b["x"], box.left(), box.right())
        lo, hi = _range(b)
        y = axis.scale(lo, hi, box.bottom(), box.top())
        chart.axes(p, box, xt, [(y(v), chart.num(v)) for v in axis.ticks(lo, hi, 5)])
        for down, up, alpha in FILLS:
            pts = [QPointF(a, y(v)) for a, v in zip(px, b["bands"][up]) if v is not None]
            pts += [QPointF(a, y(v)) for a, v in reversed(list(zip(px, b["bands"][down])))
                    if v is not None]
            fill = QColor(SIM)
            fill.setAlphaF(alpha)
            p.setPen(Qt.NoPen)
            p.setBrush(fill)
            p.drawPolygon(QPolygonF(pts))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(MEDIAN), 1.5, Qt.DashLine))
        p.drawPath(axis.curve(px, b["bands"]["50"], y))
        p.setPen(QPen(QColor(REAL), 2.8))
        p.drawPath(axis.curve(px, b["real"], y))
        s = _split(b)
        if s is not None:
            chart.vline(p, px[s], box, T["text"], 1.5, Qt.DotLine)
            p.setFont(chart.font(11, True))
            p.setPen(QColor(T["text"]))
            p.drawText(QRectF(px[s] + 6, box.top() + 2, 200, 20), Qt.AlignLeft, "OOS →")
        if hover is not None and box.contains(hover):
            chart.vline(p, px[axis.nearest(px, hover.x())], box, T["faint"], 1)

    return draw


def _tip(b: dict) -> Callable:
    """The bands and the real value at the point under the pointer."""

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        box = chart.area(rect)
        if not box.contains(pos):
            return None
        px, _ = axis.xaxis(b["x"], box.left(), box.right())
        i = axis.nearest(px, pos.x())
        unit = f" {b['unit']}" if b["unit"] else ""
        rows = [f"x = {b['x'][i]}", f"real: {chart.num(b['real'][i])}{unit}"]
        rows += [f"p{k}: {chart.num(v[i])}{unit}" for k, v in reversed(b["bands"].items())]
        return "\n".join(rows)

    return tip


def widget(block: dict) -> QWidget:
    """One cone, drawn and explained.

    Args:
        block: A contract `cone` block.

    Returns:
        The framed chart and its key.
    """
    b = block
    real = any(v is not None for v in b["real"])
    items = [("box", chart.blend(SIM, FILLS[0][2]), "2,5–97,5 % de las simulaciones"),
             ("box", chart.blend(SIM, FILLS[0][2] + FILLS[1][2]), "25–75 %"),
             ("dash", MEDIAN, "mediana simulada"),
             ("line", REAL, "curva real") if real else
             ("line", T["faint"], "sin curva real: el estudio no la dio")]
    if _split(b) is not None:
        items.append(("dash", T["text"], f"empieza el fuera de muestra ({b['split']})"))
    return card(b, chart.Canvas(_draw(b), _tip(b)), chart.key(items))
