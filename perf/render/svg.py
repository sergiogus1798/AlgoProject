"""The drawing primitives the catalogue's figures share: the box, the axis and the bar."""

W, H = 900, 300
PAD = {"l": 235, "r": 24, "t": 16, "b": 44}
GOOD, BAD, INK, GRID = "var(--good)", "var(--bad)", "var(--null)", "var(--grid)"
PALETTE = [INK, "var(--real)", GOOD, BAD, "var(--ink-2)"]
LABEL = 230  # room kept at the right for the value or series label


def box(body: str, height: int = H) -> str:
    """One figure's canvas.

    Args:
        body: The shapes already drawn.
        height: Canvas height in pixels.

    Returns:
        An SVG element that scales to the width of its column.
    """
    return f'<svg viewBox="0 0 {W} {height}" role="img">{body}</svg>'


def num(value: float) -> str:
    """One number in the shape a reader expects for its size.

    Args:
        value: The number.

    Returns:
        Fewer decimals the larger it is, thousands separated.
    """
    if value == int(value):
        return f"{int(value):,}"
    if abs(value) >= 100:
        return f"{value:,.0f}"
    return f"{value:.1f}" if abs(value) >= 10 else f"{value:.2f}"


def hbars(rows: list[tuple[str, float]], unit: str, colour: str = INK,
          height: int = H) -> str:
    """A horizontal bar per row, longest at the top.

    Args:
        rows: Label and value, already in the order they should be drawn.
        unit: Printed after each value.
        colour: Bar fill.
        height: Canvas height; give each row about 26 px.

    Returns:
        The finished figure. Horizontal because the labels are module names, and a name
        turned on its side is a name nobody reads.
    """
    top = max(v for _, v in rows) or 1.0
    step = (height - PAD["t"] - PAD["b"]) / max(len(rows), 1)
    width = W - PAD["l"] - PAD["r"] - LABEL
    out = []
    for i, (label, value) in enumerate(rows):
        y = PAD["t"] + i * step
        out.append(f'<text class="tick" x="{PAD["l"] - 10}" y="{y + step / 2 + 4}" '
                   f'text-anchor="end">{label}</text>')
        out.append(f'<rect x="{PAD["l"]}" y="{y + 3}" width="{value / top * width:.1f}" '
                   f'height="{step - 8:.1f}" fill="{colour}" rx="2"/>')
        out.append(f'<text class="mark" x="{PAD["l"] + value / top * width + 8:.1f}" '
                   f'y="{y + step / 2 + 4}">{num(value)} {unit}</text>')
    return box("".join(out), height)


def curves(series: dict[str, list[tuple[float, float]]], ticks: list[float],
           unit: str, zero: bool = True) -> str:
    """Two or more lines over the same discrete x positions.

    Args:
        series: Name to (x, y) points. The name is drawn at the end of its line.
        ticks: The x values, evenly spaced on the axis whatever their numeric gaps.
        unit: Label for the y axis.
        zero: Whether the y axis starts at zero. It should when the quantity is a rate and
            the reader is comparing sizes; it should not when every line sits near 100 and
            the question is how far they moved, which zero would flatten into one stripe.

    Returns:
        The finished figure. X is placed by position rather than by value so 1, 2, 4, 48
        and 96 workers get equal room: the question is the shape, not the arithmetic.
    """
    values = [y for points in series.values() for _, y in points]
    hi, lo = max(values), (0.0 if zero else min(values))
    pad = (hi - lo) * 0.12 or 1.0
    hi, lo = hi + pad, (0.0 if zero else lo - pad)
    span = W - PAD["l"] - PAD["r"] - LABEL
    plot = H - PAD["b"] - PAD["t"]
    xs = {t: PAD["l"] + i * span / max(len(ticks) - 1, 1) for i, t in enumerate(ticks)}

    def ypos(value: float) -> float:
        """Pixel row of one value."""
        return H - PAD["b"] - (value - lo) / (hi - lo) * plot

    out = [f'<line x1="{PAD["l"]}" y1="{H - PAD["b"]}" x2="{W - PAD["r"]}" '
           f'y2="{H - PAD["b"]}" stroke="{GRID}"/>']
    for step in range(4):
        value = lo + (hi - lo) * step / 3
        out.append(f'<line x1="{PAD["l"]}" y1="{ypos(value):.1f}" x2="{W - PAD["r"]}" '
                   f'y2="{ypos(value):.1f}" stroke="{GRID}" stroke-dasharray="2 4"/>')
        out.append(f'<text class="tick" x="{PAD["l"] - 10}" y="{ypos(value) + 4:.1f}" '
                   f'text-anchor="end">{num(value)}</text>')
    for t_ in ticks:
        out.append(f'<text class="tick" x="{xs[t_]}" y="{H - PAD["b"] + 18}" '
                   f'text-anchor="middle">{num(t_)}</text>')
    ends = sorted(((points[-1], name) for name, points in series.items()),
                  key=lambda pair: pair[0][1], reverse=True)
    taken: list[float] = []
    for i, (name, points) in enumerate(series.items()):
        colour = PALETTE[i % len(PALETTE)]
        path = " ".join(f"{xs[x]:.1f},{ypos(y):.1f}" for x, y in points)
        out.append(f'<polyline points="{path}" fill="none" stroke="{colour}" '
                   f'stroke-width="2.5"/>')
    for (last, name) in ends:
        i = list(series).index(name)
        y = ypos(last[1])
        while any(abs(y - other) < 15 for other in taken):
            y += 15
        taken.append(y)
        out.append(f'<text class="mark" x="{xs[last[0]] + 8:.1f}" y="{y + 4:.1f}" '
                   f'fill="{PALETTE[i % len(PALETTE)]}">{name} — {num(last[1])} {unit}</text>')
    return box("".join(out))
