"""The drawing primitives every figure shares: the canvas, the axes, the number and the legend."""

W, H = 760, 300
PAD = {"l": 62, "r": 20, "t": 28, "b": 46}
NAMES = 150
SIM, REAL, GRID = "var(--null)", "var(--real)", "var(--grid)"
GAP = 2


def xpos(value: float, lo: float, hi: float, left: int = PAD["l"]) -> float:
    """Position a data value on the horizontal axis.

    Args:
        value: The value to place.
        lo, hi: Axis extent in data units.
        left: Left margin.

    Returns:
        A pixel coordinate inside the plot area.
    """
    span = hi - lo or 1.0
    return left + (value - lo) / span * (W - left - PAD["r"])


def ypos(value: float, lo: float, hi: float) -> float:
    """Position a data value on the vertical axis.

    Args:
        value: The value to place.
        lo, hi: Axis extent in data units.

    Returns:
        A pixel coordinate, top of the plot area being hi.
    """
    span = hi - lo or 1.0
    return H - PAD["b"] - (value - lo) / span * (H - PAD["b"] - PAD["t"])


def num(value: float) -> str:
    """One axis number, in the shape a reader expects for its size.

    Args:
        value: The number.

    Returns:
        Thousands separated above 1,000, two decimals down to 1, and four significant
        figures below it. The general-purpose format turns 46,191 into 4.619e+04, which is
        correct and unreadable.
    """
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:,.2f}" if abs(value) >= 1 else f"{value:.4g}"


def legend(items: list[tuple[str, str]]) -> str:
    """A row of colour-coded chips under a figure, instead of a caption sentence to decode.

    Args:
        items: (swatch style, label) pairs. The swatch style is a raw inline CSS string the
            caller builds to match exactly what the figure drew — a filled box for a bar or
            band, a line style (solid/dashed/dotted border) for a line.

    Returns:
        One HTML block, plain enough to render identically in the panel and in the
        self-contained batch report — no script, just a `<style>`-free inline row.
    """
    chips = "".join(f'<span class="chip"><i style="{style}"></i>{label}</span>'
                    for style, label in items)
    return f'<div class="legend">{chips}</div>'


def box(color: str, opacity: float = 1.0) -> str:
    """Legend swatch style for a filled bar or band."""
    return f"background:{color};opacity:{opacity}"


def line(color: str, dash: str = "solid") -> str:
    """Legend swatch style for a line — dash is a border-style keyword."""
    return f"border-top:3px {dash} {color}"
