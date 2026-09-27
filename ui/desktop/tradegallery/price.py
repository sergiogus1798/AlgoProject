"""The price painter of one trade: bar ranges, the close line, the entry and exit marked, on `chart.Canvas`."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.states import REAL, SERIES
from ui.desktop.theme import T

ENTRY, EXIT = SERIES[0], SERIES[1]     # blue in, orange out: never a verdict's green or red
HEIGHT = 320


def _range(w: dict, tile: dict) -> tuple[float, float]:
    """The y range over the bars and both fill prices, with a margin."""
    v = w["h"] + w["l"] + [tile["open_price"], tile["close_price"]]
    margin = 0.06 * (max(v) - min(v))
    return min(v) - margin, max(v) + margin


def _geometry(w: dict, tile: dict, rect: QRectF) -> tuple[QRectF, list[float], Callable]:
    """The plotting box, the pixel column per bar and the price-to-pixel map."""
    box = chart.area(rect)
    px = [axis.scale(0, max(len(w["t"]) - 1, 1), box.left() + 6, box.right() - 6)(i)
          for i in range(len(w["t"]))]
    return box, px, axis.scale(*_range(w, tile), box.bottom(), box.top())


def _marker(p: QPainter, x: float, y: float, colour: str, up: bool) -> None:
    """A filled triangle at a fill price: pointing up for the entry, down for the exit."""
    d = 8 if up else -8
    p.setPen(QPen(QColor(T["bg"]), 1.5))
    p.setBrush(QColor(colour))
    p.drawPolygon(QPolygonF([QPointF(x, y), QPointF(x - 7, y + d * 1.4),
                             QPointF(x + 7, y + d * 1.4)]))


def draw_for(tile: dict) -> Callable:
    """The painter of one trade's window.

    Args:
        tile: One tile of `/api/tearsheet/trades`, with `bars` holding `t, o, h, l, c, entry, exit`.

    Returns:
        The draw function `chart.Canvas` takes.
    """
    w = tile["bars"]

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        box, px, y = _geometry(w, tile, rect)
        lo, hi = _range(w, tile)
        step = max(1, round(len(px) / 5))
        xt = [(px[i], w["t"][i][5:]) for i in range(0, len(px), step)]
        chart.axes(p, box, xt, [(y(v), chart.num(v)) for v in axis.ticks(lo, hi, 5)])
        p.fillRect(QRectF(px[w["entry"]], box.top(), px[w["exit"]] - px[w["entry"]],
                          box.height()), QColor(chart.blend(ENTRY, 0.12)))
        p.setPen(QPen(QColor(T["faint"]), 1.2))
        for x, h, l in zip(px, w["h"], w["l"]):
            p.drawLine(QPointF(x, y(h)), QPointF(x, y(l)))
        p.setPen(QPen(QColor(REAL), 2.2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(axis.curve(px, w["c"], y))
        for k, price, colour, up in ((w["entry"], tile["open_price"], ENTRY, True),
                                     (w["exit"], tile["close_price"], EXIT, False)):
            chart.vline(p, px[k], box, colour, 1.2, Qt.DashLine)
            _marker(p, px[k], y(price), colour, up)
        if hover is not None and box.contains(hover):
            chart.vline(p, px[axis.nearest(px, hover.x())], box, T["muted"], 1, Qt.DotLine)

    return draw


def tip_for(tile: dict) -> Callable:
    """The sentence for the bar under the pointer.

    Args:
        tile: As in `draw_for`.

    Returns:
        The tip function `chart.Canvas` takes.
    """
    w = tile["bars"]

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """What the bar under `pos` is, None outside the plot."""
        box, px, _ = _geometry(w, tile, rect)
        if not box.contains(pos):
            return None
        i = axis.nearest(px, pos.x())
        out = (f"vela que abre {w['t'][i]}\napertura {chart.num(w['o'][i])} · máximo "
               f"{chart.num(w['h'][i])} · mínimo {chart.num(w['l'][i])} · cierre {chart.num(w['c'][i])}")
        if i == w["entry"]:
            out += f"\nENTRADA en esta vela a {tile['open_price']} (precio de la operación)"
        if i == w["exit"]:
            out += f"\nSALIDA en esta vela a {tile['close_price']} (precio de la operación)"
        return out

    return tip


def canvas(tile: dict) -> chart.Canvas:
    """The painted window of one trade.

    Args:
        tile: As in `draw_for`.

    Returns:
        The canvas, 320 px high.
    """
    return chart.Canvas(draw_for(tile), tip_for(tile), HEIGHT)
