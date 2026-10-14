"""The sign shade of a histogram: faint red behind the negative side of the x axis, faint green behind the positive."""

from collections.abc import Callable

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter

from ui.desktop.blocks.states import colour
from ui.text.numbers import num


def sign_shade(
    p: QPainter,
    box: QRectF,
    x: Callable[[float], float],
    lo: float,
    hi: float,
    pivot: float = 0.0,
) -> None:
    """Paint red left of `pivot` and green right of it, when the axis [lo, hi] crosses it.

    Args:
        p: The painter.
        box: The plot area.
        x: The data-to-pixel map of the x axis.
        lo: Left end of the axis.
        hi: Right end of the axis.
        pivot: Where good starts: 0, or 1 for a ratio.
    """
    if not lo < pivot < hi:
        return
    red, green = QColor(colour("fail")), QColor(colour("pass"))
    red.setAlphaF(0.10)
    green.setAlphaF(0.10)
    p.fillRect(QRectF(box.left(), box.top(), x(pivot) - box.left(), box.height()), red)
    p.fillRect(QRectF(x(pivot), box.top(), box.right() - x(pivot), box.height()), green)


def caption(share: float, pivot: float = 0.0) -> str:
    """«X % rentables» for pivot 0, «X % por encima de P» otherwise (share is 0..1)."""
    return f"{num(100 * share, '%')} " + (
        "rentables" if not pivot else f"por encima de {num(pivot)}"
    )
