"""The cone block: the simulated equity bands, the real curve on top and where the OOS starts."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card
from ui.desktop.blocks.states import MEDIAN, REAL, SIM
from ui.text.numbers import num
from ui.desktop.theme import T

ALPHAS = (0.30, 0.55)


def _fills(b: dict) -> tuple:
    """(low, high, alpha) of the outer and the inner band, read from the block's own keys,
    so 5-95 and 25-75 (or 2.5-97.5) draw with no special case."""
    k = sorted(b["bands"], key=float)
    return ((k[0], k[-1], ALPHAS[0]), (k[1], k[-2], ALPHAS[1]))


def _range(b: dict) -> tuple[float, float]:
    """The y range over every band and the real curve."""
    v = [y for s in (*b["bands"].values(), b["real"]) for y in s if y is not None]
    margin = 0.06 * (max(v) - min(v))   # so no mark sits on the frame
    return min(v) - margin, max(v) + margin


def _mid(b: dict) -> str:
    """The key of the median curve: the middle one of the sorted levels."""
    k = sorted(b["bands"], key=float)
    return k[len(k) // 2]


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
        for down, up, alpha in _fills(b):
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
        p.drawPath(axis.curve(px, b["bands"][_mid(b)], y))
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
        rows = [f"x = {b['x'][i]}", f"real: {chart.num(b['real'][i], b['unit'])}"]
        rows += [f"p{k}: {chart.num(v[i], b['unit'])}" for k, v in reversed(b["bands"].items())]
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
    (a, z, _), (c, d, _) = _fills(b)
    name = b.get("real_label", "curva real")
    items = [("box", chart.blend(SIM, ALPHAS[0]), f"{num(float(a))}–{num(float(z))} % de las simulaciones"),
             ("box", chart.blend(SIM, sum(ALPHAS)), f"{num(float(c))}–{num(float(d))} %"),
             ("dash", MEDIAN, "mediana simulada"),
             ("line", REAL, name) if real else
             ("line", T["faint"], "sin curva real: el estudio no la dio")]
    if _split(b) is not None:
        items.append(("dash", T["text"], f"empieza el fuera de muestra ({b['split']})"))
    return card(b, chart.Canvas(_draw(b), _tip(b)), chart.key(items))
