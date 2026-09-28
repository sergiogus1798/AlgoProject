"""The price painter of one asset: candles when they fit, each pixel column's range and close when they do not."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.states import REAL, SERIES
from ui.desktop.theme import T

HEIGHT = 440
UP, DOWN = SERIES[0], SERIES[1]   # blue up, orange down: green and red are verdicts here
CANDLE_PX = 3        # below this many pixels per bar a body is a smear: draw ranges instead


def _columns(b: dict, width: float) -> list[tuple[int, int]]:
    """The bars each drawn column holds, as (first, last) index pairs.

    Args:
        b: The `/api/data/bars` body.
        width: Plot width in pixels.

    Returns:
        One pair per bar when the candles fit, otherwise one per pixel column, so a
        history of 140 000 hours is drawn as its envelope instead of as ink.
    """
    n = len(b["t"])
    if n * CANDLE_PX <= width:
        return [(i, i) for i in range(n)]
    cols = max(1, int(width))
    return [(k * n // cols, max(k * n // cols, (k + 1) * n // cols - 1)) for k in range(cols)]


def _geometry(b: dict, rect: QRectF) -> tuple[QRectF, list, list[float], Callable]:
    """The plotting box, the columns, their pixel centres and the price-to-pixel map."""
    box = chart.area(rect)
    cols = _columns(b, box.width() - 12)
    x = axis.scale(0, max(len(cols) - 1, 1), box.left() + 6, box.right() - 6)
    lo, hi = min(b["l"]), max(b["h"])
    margin = 0.04 * (hi - lo)
    return box, cols, [x(i) for i in range(len(cols))], axis.scale(lo - margin, hi + margin,
                                                                    box.bottom(), box.top())


def draw_for(b: dict, mode: Callable[[bool], None]) -> Callable:
    """The painter of one feed at one timeframe.

    Args:
        b: The `/api/data/bars` body, with at least one bar.
        mode: Told on every paint whether candles (True) or range columns (False) were
            drawn — the width decides, so only the painter knows, and the key follows it.

    Returns:
        The draw function `chart.Canvas` takes. Up candles blue, down candles orange,
        as the trade gallery marks entry and exit: green and red are verdicts here.
    """
    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        box, cols, px, y = _geometry(b, rect)
        lo, hi = min(b["l"]), max(b["h"])
        step = max(1, len(cols) // 6)
        xt = [(px[k], b["t"][cols[k][0]][:10]) for k in range(0, len(cols), step)
              if px[k] < box.right() - 50]        # a date at the edge would be cut in half
        chart.axes(p, box, xt, [(y(v), chart.num(v)) for v in axis.ticks(lo, hi, 6)])
        half = max(1.0, (px[1] - px[0]) * 0.35) if len(px) > 1 else 4.0
        mode(len(cols) == len(b["t"]))
        if len(cols) == len(b["t"]):          # one column per bar: real candles
            for x, (i, _) in zip(px, cols):
                ink = QColor(UP if b["c"][i] >= b["o"][i] else DOWN)
                p.setPen(QPen(ink, 1))
                p.drawLine(QPointF(x, y(b["h"][i])), QPointF(x, y(b["l"][i])))
                top, bottom = y(max(b["o"][i], b["c"][i])), y(min(b["o"][i], b["c"][i]))
                p.setBrush(ink)
                p.drawRect(QRectF(x - half, top, 2 * half, max(1.0, bottom - top)))
        else:
            p.setPen(QPen(QColor(T["faint"]), 1))
            for x, (i, j) in zip(px, cols):
                p.drawLine(QPointF(x, y(max(b["h"][i:j + 1]))), QPointF(x, y(min(b["l"][i:j + 1]))))
            p.setPen(QPen(QColor(REAL), 1.6))
            p.setBrush(Qt.NoBrush)
            p.drawPath(axis.curve(px, [b["c"][j] for _, j in cols], y))
        if hover is not None and box.contains(hover):
            chart.vline(p, px[axis.nearest(px, hover.x())], box, T["muted"], 1, Qt.DotLine)

    return draw


def tip_for(b: dict) -> Callable:
    """The sentence for the candle or column under the pointer.

    Args:
        b: As in `draw_for`.

    Returns:
        The tip function `chart.Canvas` takes.
    """
    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """What the bars under `pos` are, None outside the plot."""
        box, cols, px, _ = _geometry(b, rect)
        if not box.contains(pos):
            return None
        i, j = cols[axis.nearest(px, pos.x())]
        span = b["t"][i] if i == j else f"{b['t'][i]} → {b['t'][j]} ({j - i + 1} velas)"
        return (f"{span}\napertura {chart.num(b['o'][i])} · máximo {chart.num(max(b['h'][i:j + 1]))}"
                f" · mínimo {chart.num(min(b['l'][i:j + 1]))} · cierre {chart.num(b['c'][j])}")

    return tip


def canvas(b: dict, mode: Callable[[bool], None]) -> chart.Canvas:
    """The painted history of one feed at one timeframe.

    Args:
        b: As in `draw_for`.
        mode: As in `draw_for`.

    Returns:
        The canvas, 440 px high.
    """
    return chart.Canvas(draw_for(b, mode), tip_for(b), HEIGHT)
