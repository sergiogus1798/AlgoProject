"""The two bar figures: the sub-scores against their cutoffs, and a signed bar per group."""

from strategies.monteCarlo.charts import (GRID, H, NAMES, PAD, REAL, SIM, W, _box, _line, _x,
                                          _y, legend)


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
  <figcaption><b>Puntuación por familia</b></figcaption>
  <svg viewBox="0 0 {W} {height}" role="img" aria-label="puntuación por familia">
    {marks}{''.join(rows)}
  </svg>
  {legend([(_box(SIM), "Sub-score (0-100)"),
          (_line(REAL, "dashed"), f"Cortes {cutoffs[0]} / {cutoffs[1]} / {cutoffs[2]}")])}
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
  {legend([(_box(SIM), "Positivo"), (_box(REAL), "Negativo")])}
</figure>'''
