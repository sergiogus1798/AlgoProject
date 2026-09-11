"""The study's figures as inline SVG: nothing to load, nothing to run in the browser."""

W, H = 760, 300
PAD = {"l": 62, "r": 20, "t": 28, "b": 46}
NAMES = 150
SIM, REAL, GRID = "var(--null)", "var(--real)", "var(--grid)"
GAP = 2


def _x(value: float, lo: float, hi: float, left: int = PAD["l"]) -> float:
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


def _y(value: float, lo: float, hi: float) -> float:
    """Position a data value on the vertical axis.

    Args:
        value: The value to place.
        lo, hi: Axis extent in data units.

    Returns:
        A pixel coordinate, top of the plot area being hi.
    """
    span = hi - lo or 1.0
    return H - PAD["b"] - (value - lo) / span * (H - PAD["b"] - PAD["t"])


def _num(value: float) -> str:
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


def distribution(shape: dict, title: str, subtitle: str, unit: str) -> str:
    """A simulated distribution with the observed backtest marked on it.

    Args:
        shape: What metrics.shape() returned.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.
        unit: Axis label.

    Returns:
        An SVG element. The bars are the simulations; the single rule is what actually
        happened. Where that rule sits inside the bars is the whole reading.
    """
    counts, lo, hi = shape["counts"], shape["lo"], shape["hi"]
    top, floor = max(counts) or 1, H - PAD["b"]
    width = (W - PAD["l"] - PAD["r"]) / len(counts)
    bars = "".join(
        f'<rect x="{PAD["l"] + i * width:.1f}" y="{floor - n / top * (floor - PAD["t"]):.1f}" '
        f'width="{max(width - GAP, 0.5):.1f}" height="{n / top * (floor - PAD["t"]):.1f}" '
        f'rx="1" fill="{SIM}"/>' for i, n in enumerate(counts) if n)
    axis = "".join(
        f'<text x="{_x(lo + (hi - lo) * i / 4, lo, hi):.1f}" y="{floor + 18}" '
        f'text-anchor="middle" class="tick">{_num(lo + (hi - lo) * i / 4)}</text>'
        for i in range(5))
    at = _x(shape["observed"], lo, hi)
    side = "end" if at > W * 0.62 else "start"
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <line x1="{PAD['l']}" y1="{floor}" x2="{W - PAD['r']}" y2="{floor}" stroke="{GRID}"/>
    {bars}
    <line x1="{at:.1f}" y1="{PAD['t'] - 10}" x2="{at:.1f}" y2="{floor}" stroke="{REAL}"
          stroke-width="2"/>
    <text x="{at + (-8 if side == 'end' else 8):.1f}" y="{PAD['t'] - 14}"
          text-anchor="{side}" class="mark">backtest {_num(shape['observed'])}</text>
    <text x="{PAD['l']}" y="{PAD['t'] - 14}" class="tick">simulaciones</text>
    {axis}
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">{unit}</text>
  </svg>
</figure>'''


def cone(band: dict, title: str, subtitle: str) -> str:
    """The equity curves order luck could have produced, around the one it did.

    Args:
        band: What fan.envelope() returned.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.

    Returns:
        An SVG element: the 5-95 and 25-75 bands as filled areas, the median as a line and
        the real curve on top. The width of the cone at the right edge is what the same
        trades in another order were worth.
    """
    qs = sorted(band["bands"])
    every = [v for row in band["bands"].values() for v in row] + band["observed"]
    lo, hi = min(every), max(every)
    steps = band["at"]
    last = steps[-1] or 1

    def path(values: list[float], back: list[float] | None = None) -> str:
        """One polyline, optionally closed with a second series drawn backwards."""
        head = " ".join(f"{_x(s, 0, last):.1f},{_y(v, lo, hi):.1f}"
                        for s, v in zip(steps, values))
        if back is None:
            return head
        tail = " ".join(f"{_x(s, 0, last):.1f},{_y(v, lo, hi):.1f}"
                        for s, v in zip(reversed(steps), reversed(back)))
        return f"{head} {tail}"

    outer = path(band["bands"][qs[0]], band["bands"][qs[-1]])
    inner = path(band["bands"][qs[1]], band["bands"][qs[-2]])
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <polygon points="{outer}" fill="{SIM}" opacity="0.18"/>
    <polygon points="{inner}" fill="{SIM}" opacity="0.28"/>
    <polyline points="{path(band['bands'][qs[len(qs) // 2]])}" fill="none" stroke="{SIM}"
              stroke-width="1.5"/>
    <polyline points="{path(band['observed'])}" fill="none" stroke="{REAL}"
              stroke-width="2"/>
    <text x="{PAD['l']}" y="{PAD['t'] - 14}" class="tick">
      bandas {qs[0]}-{qs[-1]} y {qs[1]}-{qs[-2]} · línea naranja: el backtest</text>
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">
      operaciones, en orden</text>
    <text x="{PAD['l'] - 8}" y="{_y(hi, lo, hi):.1f}" text-anchor="end"
          class="tick">{hi:,.0f}</text>
    <text x="{PAD['l'] - 8}" y="{_y(lo, lo, hi):.1f}" text-anchor="end"
          class="tick">{lo:,.0f}</text>
  </svg>
</figure>'''


def scores(parts: dict[str, float], cutoffs: list[int]) -> str:
    """One bar per family against the tier cutoffs.

    Args:
        parts: What scoring.subscores() returned.
        cutoffs: The tier boundaries, highest first.

    Returns:
        An SVG element. The lowest bar is the binding constraint, which is the number the
        composite is least able to show.
    """
    height = 34 * len(parts) + PAD["t"] + 34
    rows = []
    for i, (name, value) in enumerate(parts.items()):
        y = PAD["t"] + i * 34
        end = _x(value, 0, 100, NAMES)
        tone = "clears" if value >= cutoffs[1] else "misses"
        inside = end > W - PAD["r"] - 40
        rows.append(
            f'<rect x="{NAMES}" y="{y}" width="{max(end - NAMES, 1):.1f}" height="20" '
            f'rx="4" fill="{SIM}"/>'
            f'<text x="{NAMES - 10}" y="{y + 15}" text-anchor="end" class="tick">'
            f'familia {name}</text>'
            f'<text x="{end + (-8 if inside else 8):.1f}" y="{y + 15}" '
            f'text-anchor="{"end" if inside else "start"}" '
            f'class="mark {tone}">{value:.0f}</text>')
    marks = "".join(
        f'<line x1="{_x(c, 0, 100, NAMES):.1f}" y1="{PAD["t"] - 10}" '
        f'x2="{_x(c, 0, 100, NAMES):.1f}" y2="{height - 34}" stroke="{REAL}" '
        f'stroke-dasharray="4 3"/>' for c in cutoffs)
    return f'''<figure class="fig">
  <figcaption><b>Puntuación por familia</b><span>0 a 100; las líneas son los cortes
    {cutoffs[0]} / {cutoffs[1]} / {cutoffs[2]}</span></figcaption>
  <svg viewBox="0 0 {W} {height}" role="img" aria-label="puntuación por familia">
    {marks}{''.join(rows)}
  </svg>
</figure>'''


def bars(labels: list[str], values: list[float], title: str, subtitle: str) -> str:
    """A signed bar per group, on a zero line.

    Args:
        labels: One label per bar.
        values: One value per bar, in the same order.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.

    Returns:
        An SVG element. Bars below the zero line are periods or regimes in which the
        strategy lost money, and they are the point of the figure.
    """
    lo, hi = min(0.0, min(values)), max(0.0, max(values))
    width = (W - PAD["l"] - PAD["r"]) / max(len(values), 1)
    # Few bars need air between them or three terciles read as one solid block; many bars
    # need the opposite, or a year of windows disappears into the gaps.
    thick = max(width * (0.55 if len(values) <= 14 else 0.85), 0.5)
    zero = _y(0, lo, hi)
    rects, ticks = [], []
    for i, (label, value) in enumerate(zip(labels, values)):
        x = PAD["l"] + i * width
        y = _y(value, lo, hi)
        rects.append(f'<rect x="{x + (width - thick) / 2:.1f}" y="{min(y, zero):.1f}" '
                     f'width="{thick:.1f}" height="{abs(y - zero):.1f}" '
                     f'rx="1" fill="{SIM if value >= 0 else REAL}"/>')
        if len(values) <= 14 or i % max(len(values) // 8, 1) == 0:
            ticks.append(f'<text x="{x + width / 2:.1f}" y="{H - PAD["b"] + 18}" '
                         f'text-anchor="middle" class="tick">{label}</text>')
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <line x1="{PAD['l']}" y1="{zero:.1f}" x2="{W - PAD['r']}" y2="{zero:.1f}"
          stroke="{GRID}"/>
    {''.join(rects)}{''.join(ticks)}
    <text x="{PAD['l'] - 8}" y="{_y(hi, lo, hi):.1f}" text-anchor="end"
          class="tick">{hi:,.0f}</text>
    <text x="{PAD['l'] - 8}" y="{_y(lo, lo, hi):.1f}" text-anchor="end"
          class="tick">{lo:,.0f}</text>
  </svg>
</figure>'''
