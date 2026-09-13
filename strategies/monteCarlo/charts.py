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


def _box(color: str, opacity: float = 1.0) -> str:
    """Legend swatch style for a filled bar or band."""
    return f"background:{color};opacity:{opacity}"


def _line(color: str, dash: str = "solid") -> str:
    """Legend swatch style for a line — dash is a border-style keyword."""
    return f"border-top:3px {dash} {color}"


def distribution(shape: dict, title: str, subtitle: str, unit: str, pct: bool = False) -> str:
    """A simulated distribution with the observed backtest marked on it.

    Args:
        shape: What metrics.shape() returned.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.
        unit: Axis label.
        pct: True for a statistic stored as a fraction (dd_pct, return_pct) — the axis and
            the backtest mark read in percent instead of the raw fraction.

    Returns:
        An SVG element. The bars are the simulations; the single rule is what actually
        happened. Where that rule sits inside the bars is the whole reading.
    """
    label = (lambda v: f"{v * 100:,.1f}%") if pct else num
    counts, lo, hi = shape["counts"], shape["lo"], shape["hi"]
    top, floor = max(counts) or 1, H - PAD["b"]
    width = (W - PAD["l"] - PAD["r"]) / len(counts)
    total = sum(counts) or 1
    cum = 0
    bars = []
    for i, n in enumerate(counts):
        if not n:
            continue
        cum += n
        edge_lo, edge_hi = lo + i * (hi - lo) / len(counts), lo + (i + 1) * (hi - lo) / len(counts)
        tip = (f"{label(edge_lo)} a {label(edge_hi)}&#10;{n:,} simulaciones "
              f"({n / total:.1%})&#10;Percentil hasta aquí: {100 * cum / total:.0f}")
        bars.append(
            f'<rect x="{PAD["l"] + i * width:.1f}" '
            f'y="{floor - n / top * (floor - PAD["t"]):.1f}" '
            f'width="{max(width - GAP, 0.5):.1f}" height="{n / top * (floor - PAD["t"]):.1f}" '
            f'rx="1" fill="{SIM}"><title>{tip}</title></rect>')
    axis = "".join(
        f'<text x="{_x(lo + (hi - lo) * i / 4, lo, hi):.1f}" y="{floor + 18}" '
        f'text-anchor="middle" class="tick">{label(lo + (hi - lo) * i / 4)}</text>'
        for i in range(5))
    at = _x(shape["observed"], lo, hi)
    side = "end" if at > W * 0.62 else "start"
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <line x1="{PAD['l']}" y1="{floor}" x2="{W - PAD['r']}" y2="{floor}" stroke="{GRID}"/>
    {"".join(bars)}
    <line x1="{at:.1f}" y1="{PAD['t'] - 10}" x2="{at:.1f}" y2="{floor}" stroke="{REAL}"
          stroke-width="2"/>
    <text x="{at + (-8 if side == 'end' else 8):.1f}" y="{PAD['t'] - 14}"
          text-anchor="{side}" class="mark">Backtest {label(shape['observed'])}</text>
    {axis}
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">{unit}</text>
  </svg>
  {legend([(_box(SIM, 0.9), "Simulaciones — pasa el ratón por una barra para verla"),
          (_line(REAL), "Backtest")])}
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
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">
      operaciones, en orden</text>
    <text x="{PAD['l'] - 8}" y="{_y(hi, lo, hi):.1f}" text-anchor="end"
          class="tick">{hi:,.0f}</text>
    <text x="{PAD['l'] - 8}" y="{_y(lo, lo, hi):.1f}" text-anchor="end"
          class="tick">{lo:,.0f}</text>
  </svg>
  {legend([(_box(SIM, 0.18), f"Banda {qs[0]}-{qs[-1]}"),
          (_box(SIM, 0.35), f"Banda {qs[1]}-{qs[-2]}"),
          (_line(SIM), "Mediana simulada"), (_line(REAL), "Backtest")])}
</figure>'''

