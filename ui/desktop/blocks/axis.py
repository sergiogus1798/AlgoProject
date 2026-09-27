"""The geometry of a chart: round ticks, data-to-pixel maps and paths through the points."""

import math
from collections.abc import Callable

from PySide6.QtGui import QPainterPath

from ui.desktop.blocks.chart import num


def ticks(lo: float, hi: float, n: int = 6) -> list[float]:
    """Round tick positions covering a range.

    Args:
        lo, hi: The range.
        n: About how many ticks.

    Returns:
        Ticks at 1, 2 or 5 times a power of ten, inside [lo, hi].
    """
    if hi <= lo:
        return [lo]
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 5, 10)), key=lambda st: abs(st - raw))
    first = math.ceil(lo / step) * step
    return [first + i * step for i in range(int((hi - first) / step + 1e-9) + 1)]


def scale(lo: float, hi: float, a: float, b: float) -> Callable[[float], float]:
    """A linear map from data to pixels.

    Args:
        lo, hi: The data range; a flat range is widened so nothing divides by zero.
        a, b: The pixel range.

    Returns:
        The map.
    """
    if hi == lo:
        lo, hi = lo - 1, hi + 1
    return lambda v: a + (v - lo) * (b - a) / (hi - lo)


def xaxis(xs: list, a: float, b: float) -> tuple[list[float], list[tuple[float, str]]]:
    """The pixel of each point along x, and the ticks to label it with.

    Args:
        xs: The block's x values: numbers are placed to scale, anything else (dates, labels)
            evenly by position.
        a, b: The pixel range.

    Returns:
        (pixel per point, [(pixel, text)] ticks).
    """
    if all(isinstance(v, (int, float)) for v in xs):
        x = scale(min(xs), max(xs), a, b)
        return [x(v) for v in xs], [(x(v), num(v)) for v in ticks(min(xs), max(xs))]
    x = scale(0, max(len(xs) - 1, 1), a, b)
    step = max(1, round(len(xs) / 6))
    return [x(i) for i in range(len(xs))], [(x(i), str(xs[i])) for i in range(0, len(xs), step)]


def nearest(pixels: list[float], at: float) -> int:
    """The index of the point closest to a pixel column.

    Args:
        pixels: Pixel per point, as `xaxis` returns them.
        at: The pointer's column.

    Returns:
        The index.
    """
    return min(range(len(pixels)), key=lambda i: abs(pixels[i] - at))


def curve(px: list[float], ys: list, y: Callable[[float], float]) -> QPainterPath:
    """A path through the points, broken where a value is missing.

    Args:
        px: Pixel column per point.
        ys: Values, None where missing.
        y: The data-to-pixel map of the y axis.

    Returns:
        The path.
    """
    path, pen = QPainterPath(), False
    for a, v in zip(px, ys):
        if v is None:
            pen = False
            continue
        if pen:
            path.lineTo(a, y(v))
        else:
            path.moveTo(a, y(v))
        pen = True
    return path
