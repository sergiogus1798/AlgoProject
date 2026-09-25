"""The drawing primitives every figure shares: the canvas, the scales, the ticks and the legend."""

import math
from collections.abc import Callable
from html import escape

W, H = 760, 300
PAD = {"l": 70, "r": 20, "t": 20, "b": 46}
SIM, REAL, GRID, INK2 = "var(--null)", "var(--real)", "var(--grid)", "var(--ink-2)"
STATE = {"pass": "var(--good)", "fail": "var(--bad)", "watch": "var(--watch)",
         "info": "var(--null)", "none": "var(--ink-2)"}


def num(value: float | None) -> str:
    """One number in the shape a reader expects for its size.

    Args:
        value: The number, or None for a gap.

    Returns:
        Thousands separated above 1,000, two decimals down to 1, four significant figures
        below it, and an em dash for a gap.
    """
    if value is None:
        return "—"
    if abs(value) >= 1000 or value == int(value):
        return f"{value:,.0f}"
    return f"{value:,.2f}" if abs(value) >= 1 else f"{value:.4g}"


def scale(lo: float, hi: float, a: float, b: float) -> Callable[[float], float]:
    """A linear map from data [lo, hi] to pixels [a, b].

    Args:
        lo, hi: Data extent; a zero span is widened so nothing divides by zero.
        a, b: Pixel extent; b < a flips the axis, as a vertical one needs.

    Returns:
        A function data -> pixel.
    """
    span = (hi - lo) or 1.0
    return lambda v: a + (v - lo) / span * (b - a)


def ticks(lo: float, hi: float, count: int = 5) -> list[float]:
    """Round tick values inside an extent: steps of 1, 2 or 5 times a power of ten.

    Args:
        lo, hi: Data extent.
        count: Roughly how many ticks.

    Returns:
        The tick values; one tick at lo when the extent is a single point.
    """
    if hi <= lo:
        return [lo]
    raw = (hi - lo) / (count - 1)
    power = 10 ** math.floor(math.log10(raw))
    step = next(m * power for m in (1, 2, 5, 10) if m * power >= raw)
    first = math.ceil(lo / step) * step
    return [round(first + i * step, 12) for i in range(int((hi - first) / step + 1e-9) + 1)]


def canvas(body: str, height: int = H) -> str:
    """Wrap drawn elements in one responsive SVG."""
    return f'<svg viewBox="0 0 {W} {height}" role="img">{body}</svg>'


def axes(x: Callable, y: Callable, xs: list[float], ys: list[float], xfmt: Callable = num,
         height: int = H) -> str:
    """The grid lines and tick labels of both axes.

    Args:
        x, y: The data -> pixel maps.
        xs, ys: Tick values on each axis.
        xfmt: Formats an x tick; dates pass their own.
        height: Canvas height.

    Returns:
        SVG elements.
    """
    out = [f'<line x1="{PAD["l"]}" x2="{W - PAD["r"]}" y1="{y(v):.1f}" y2="{y(v):.1f}" '
           f'stroke="{GRID}"/><text class="tick" x="{PAD["l"] - 6}" y="{y(v) + 4:.1f}" '
           f'text-anchor="end">{num(v)}</text>' for v in ys]
    out += [f'<text class="tick" x="{x(v):.1f}" y="{height - PAD["b"] + 18}" '
            f'text-anchor="middle">{escape(str(xfmt(v)))}</text>' for v in xs]
    return "".join(out)


def legend(items: list[tuple[str, str]]) -> str:
    """A row of colour chips under a figure.

    Args:
        items: (inline swatch style, label) pairs.

    Returns:
        One HTML block, no script.
    """
    chips = "".join(f'<span class="chip"><i style="{style}"></i>{escape(label)}</span>'
                    for style, label in items)
    return f'<div class="legend">{chips}</div>'


def box(color: str, opacity: float = 1.0) -> str:
    """Legend swatch style for a filled bar or band."""
    return f"background:{color};opacity:{opacity}"


def line(color: str, dash: str = "solid") -> str:
    """Legend swatch style for a line; dash is a border-style keyword."""
    return f"border-top:3px {dash} {color}"


def figure(title: str, note: str, svg: str, key: str = "") -> str:
    """A figure with its title above and its reading note below the title.

    Args:
        title: What it shows.
        note: How to read it, one sentence.
        svg: The drawing.
        key: The legend, if any.

    Returns:
        One <figure>.
    """
    lede = f"<span>{escape(note)}</span>" if note else ""
    return (f'<figure class="fig"><figcaption><b>{escape(title)}</b>{lede}</figcaption>'
            f"{svg}{key}</figure>")
