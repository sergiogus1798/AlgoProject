"""The bars block: one bar per item, coloured by its state, with its error and a reference — horizontal, or columns over their labels."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card, text
from ui.desktop.blocks.states import CURVE, colour, label
from ui.desktop.theme import T

TOP, BOTTOM, RIGHT = 14, 40, 100


def _geometry(b: dict, rect: QRectF) -> tuple[float, float, tuple[float, float], Callable]:
    """The label column's width, the row height, the value range and its pixel map."""
    items = b["items"]
    left = min(340, 16 + max(QFontMetrics(chart.font(11)).horizontalAdvance(i["label"])
                             for i in items))
    row = max(30.0, min(56.0, (rect.height() - TOP - BOTTOM) / len(items)))
    ends = [0.0] + [i["value"] for i in items if i["value"] is not None]
    ends += [e for i in items for e in (i.get("error") or []) if e is not None]
    ends += [b["reference"]] if b["reference"] is not None else []
    span = min(ends), max(ends)
    return left, row, span, axis.scale(*span, left, rect.width() - RIGHT)


def _draw(b: dict) -> Callable:
    """The painter of one bar chart."""

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        left, row, span, x = _geometry(b, rect)
        bottom = TOP + row * len(b["items"])
        p.setFont(chart.font(10))
        for v in axis.ticks(*span):
            p.setPen(QPen(QColor(T["line"]), 1))
            p.drawLine(QPointF(x(v), TOP), QPointF(x(v), bottom))
            p.setPen(QColor(T["muted"]))
            p.drawText(QRectF(x(v) - 50, bottom + 6, 100, 18), Qt.AlignHCenter, chart.num(v))
        for k, i in enumerate(b["items"]):
            top = TOP + k * row
            thick = min(row - 10, 26)
            mid = top + row / 2
            p.setFont(chart.font(11))
            p.setPen(QColor(T["text"]))
            p.drawText(QRectF(0, top, left - 10, row), Qt.AlignRight | Qt.AlignVCenter, i["label"])
            if i["value"] is None:
                continue
            a, z = sorted((x(0.0), x(i["value"])))
            p.fillRect(QRectF(a, mid - thick / 2, max(z - a, 1.5), thick),
                       QColor(colour(i.get("state", "none"))))
            end = z
            if i.get("error"):
                e0, e1 = (x(e) for e in i["error"])
                end = max(z, e0, e1)
                p.setPen(QPen(QColor(T["text"]), 2))
                p.drawLine(QPointF(e0, mid), QPointF(e1, mid))
                for e in (e0, e1):
                    p.drawLine(QPointF(e, mid - 6), QPointF(e, mid + 6))
            # The figure goes past the whisker too, so no line ever runs through it.
            p.setPen(QColor(T["text"]))
            p.setFont(chart.font(11, True))
            p.drawText(QRectF(end + 8, top, rect.width() - end, row), Qt.AlignLeft | Qt.AlignVCenter,
                       chart.num(i["value"]))
        p.setPen(QPen(QColor(T["rule"]), 1))
        p.drawLine(QPointF(x(0.0), TOP), QPointF(x(0.0), bottom))
        if b["reference"] is not None:
            p.setPen(QPen(QColor(T["text"]), 1.5, Qt.DashLine))
            p.drawLine(QPointF(x(b["reference"]), TOP - 6), QPointF(x(b["reference"]), bottom))

    return draw


def _tip(b: dict) -> Callable:
    """The item under the pointer, with its error and state."""

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        _, row, _, _ = _geometry(b, rect)
        k = int((pos.y() - TOP) // row)
        if not 0 <= k < len(b["items"]):
            return None
        i = b["items"][k]
        unit = f" {b['unit']}" if b["unit"] else ""
        out = f"{i['label']}: {chart.num(i['value'])}{unit}"
        if i.get("error"):
            out += f"\nintervalo {chart.num(i['error'][0])} … {chart.num(i['error'][1])}"
        return out + f"\nestado: {label(i.get('state', 'none'))}"

    return tip


def _columns(b: dict) -> Callable:
    """The painter of a `vertical` bar chart: one column per item, its label under it and
    its figure over it, in its `ink` of `CURVE` when it names one."""

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, unused."""
        box = chart.area(rect)
        values = [0.0] + [i["value"] for i in b["items"] if i["value"] is not None]
        room = 0.1 * (max(values) - min(values) or 1)       # for the figure past each end
        lo, hi = min(values) - (room if min(values) < 0 else 0), max(values) + room
        span = axis.ticks(lo, hi, 5)
        y = axis.scale(lo, hi, box.bottom(), box.top())
        width = box.width() / max(len(b["items"]), 1)
        chart.axes(p, box, [], [(y(v), chart.num(v)) for v in span])
        p.setPen(QPen(QColor(T["rule"]), 1))
        p.drawLine(QPointF(box.left(), y(0.0)), QPointF(box.right(), y(0.0)))
        for k, i in enumerate(b["items"]):
            left = box.left() + k * width
            p.setFont(chart.font(10))
            p.setPen(QColor(T["muted"]))
            p.drawText(QRectF(left, box.bottom() + 6, width, 18), Qt.AlignHCenter, i["label"])
            if i["value"] is None:
                continue
            a, z = sorted((y(0.0), y(i["value"])))
            ink = CURVE[i["ink"]] if i.get("ink") else colour(i.get("state", "none"))
            p.fillRect(QRectF(left + width * 0.18, a, width * 0.64, max(z - a, 1.5)), QColor(ink))
            p.setPen(QColor(T["text"]))
            p.setFont(chart.font(9, True))
            above = i["value"] >= 0
            p.drawText(QRectF(left - 10, (a - 18) if above else z + 2, width + 20, 16),
                       Qt.AlignHCenter, chart.num(i["value"]))

    return draw


def _column_tip(b: dict) -> Callable:
    """The column under the pointer."""

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        box = chart.area(rect)
        k = int((pos.x() - box.left()) // (box.width() / max(len(b["items"]), 1)))
        if not (box.contains(pos) and 0 <= k < len(b["items"])):
            return None
        i = b["items"][k]
        return f"{i['label']}: {chart.num(i['value'])}{' ' + b['unit'] if b['unit'] else ''}"

    return tip


def widget(block: dict) -> QWidget:
    """One bar chart, drawn and explained.

    Args:
        block: A contract `bars` block.

    Returns:
        The framed chart and its key; with `vertical`, the columns alone — their ink is the
        sample's and the card's note names it.
    """
    b = block
    if not b["items"]:
        # A chart of nothing painted max() of an empty list inside paintEvent, and the window
        # died with a segfault (a filters.json with no filter applied, 2026-09-28).
        return card(b, text("sin barras: el estudio no dejó ningún valor que dibujar",
                            T["muted"]))
    if b.get("vertical"):
        return card(b, chart.Canvas(_columns(b), _column_tip(b)))
    states = sorted({i.get("state", "none") for i in b["items"]})
    items = [("box", colour(s), label(s)) for s in states]
    if any(i.get("error") for i in b["items"]):
        items.append(("line", T["text"], "intervalo"))
    if b["reference"] is not None:
        items.append(("dash", T["text"], f"referencia {chart.num(b['reference'])}"))
    if b["unit"]:
        items.append(("box", T["bg"], f"unidad: {b['unit']}"))
    height = max(chart.HEIGHT - 20, TOP + BOTTOM + 30 * len(b["items"]))
    return card(b, chart.Canvas(_draw(b), _tip(b), height), chart.key(items))
