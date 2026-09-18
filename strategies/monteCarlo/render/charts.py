"""The study's two figures: a simulated distribution, and the equity cone around the real curve."""

from strategies.monteCarlo.render.svg import (GAP, GRID, H, PAD, REAL, SIM, W, box, legend,
                                              line, num, xpos, ypos)


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
        f'<text x="{xpos(lo + (hi - lo) * i / 4, lo, hi):.1f}" y="{floor + 18}" '
        f'text-anchor="middle" class="tick">{label(lo + (hi - lo) * i / 4)}</text>'
        for i in range(5))
    at = xpos(shape["observed"], lo, hi)
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
  {legend([(box(SIM, 0.9), "Simulaciones — pasa el ratón por una barra para verla"),
          (line(REAL), "Backtest")])}
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
        head = " ".join(f"{xpos(s, 0, last):.1f},{ypos(v, lo, hi):.1f}"
                        for s, v in zip(steps, values))
        if back is None:
            return head
        tail = " ".join(f"{xpos(s, 0, last):.1f},{ypos(v, lo, hi):.1f}"
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
    <text x="{PAD['l'] - 8}" y="{ypos(hi, lo, hi):.1f}" text-anchor="end"
          class="tick">{hi:,.0f}</text>
    <text x="{PAD['l'] - 8}" y="{ypos(lo, lo, hi):.1f}" text-anchor="end"
          class="tick">{lo:,.0f}</text>
  </svg>
  {legend([(box(SIM, 0.18), f"Banda {qs[0]}-{qs[-1]}"),
          (box(SIM, 0.35), f"Banda {qs[1]}-{qs[-2]}"),
          (line(SIM), "Mediana simulada"), (line(REAL), "Backtest")])}
</figure>'''

