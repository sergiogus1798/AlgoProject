"""The per-market comparison figures: one bar or one cell per market, as inline SVG."""

import math

from strategies.crossmarket.charts import GRID, INK, NAMES, NULL, PAD, REAL, W, H, _x, legend


def bars_by_market(rows: list[dict], key: str, label: str, rule: float | None = None) -> str:
    """One horizontal bar per market, for a single scalar (E, A, breakeven, PC1...).

    Args:
        rows: Dicts with keys "market" and `key`.
        key: Which field to draw.
        label: Axis caption.
        rule: An optional threshold drawn as a dashed line, e.g. the PDF's gate for that test.

    Returns:
        An SVG element, one bar per row, market names on the left like models().
    """
    values = [r[key] for r in rows]
    lo, hi = min(0.0, *values), max(values) * 1.1 or 1.0
    height = 34 * len(rows) + PAD["t"] + 34
    bars = []
    for i, r in enumerate(rows):
        y = PAD["t"] + i * 34
        start, end = _x(min(0.0, r[key]), lo, hi, NAMES), _x(max(0.0, r[key]), lo, hi, NAMES)
        bars.append(
            f'<rect x="{start:.1f}" y="{y}" width="{max(end - start, 1):.1f}" height="20" '
            f'rx="4" fill="{NULL}"/>'
            f'<text x="{NAMES - 10}" y="{y + 15}" text-anchor="end" class="tick">'
            f'{r["market"]}</text>'
            f'<text x="{end + 8:.1f}" y="{y + 15}" class="mark">{r[key]:+.3f}</text>')
    rule_line = (f'<line x1="{_x(rule, lo, hi, NAMES):.1f}" y1="{PAD["t"] - 10}" '
                f'x2="{_x(rule, lo, hi, NAMES):.1f}" y2="{height - 34}" stroke="{REAL}" '
                f'stroke-width="2" stroke-dasharray="4 3"/>' if rule is not None else "")
    return f'''<figure class="fig">
  <figcaption><b>{label}</b></figcaption>
  <svg viewBox="0 0 {W} {height}" role="img" aria-label="{label}">
    {rule_line}{''.join(bars)}
  </svg>
</figure>'''


def curve(points: list[dict], x_key: str, y_key: str, label: str) -> str:
    """A simple line, for the cost gradient or any other x/y sweep.

    Args:
        points: Dicts with keys x_key and y_key, in x order.
        x_key, y_key: Which fields to plot.
        label: Figure caption.

    Returns:
        An SVG element: a polyline with a marker on every point.
    """
    xs, ys = [p[x_key] for p in points], [p[y_key] for p in points]
    x_lo, x_hi = min(xs), max(xs)
    y_lo, y_hi = min(0.0, *ys), max(0.0, *ys)
    floor = H - PAD["b"]

    def _y(value: float) -> float:
        """Position a data value on the vertical axis, floor at y_lo."""
        span = (y_hi - y_lo) or 1.0
        return floor - (value - y_lo) / span * (floor - PAD["t"])

    coords = [(_x(x, x_lo, x_hi), _y(y)) for x, y in zip(xs, ys)]
    poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in coords)
    dots = "".join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{REAL}"/>'
                   for px, py in coords)
    zero = f'<line x1="{PAD["l"]}" y1="{_y(0):.1f}" x2="{W - PAD["r"]}" y2="{_y(0):.1f}" ' \
           f'stroke="{GRID}"/>'
    return f'''<figure class="fig">
  <figcaption><b>{label}</b></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
    {zero}
    <polyline points="{poly}" fill="none" stroke="{NULL}" stroke-width="2"/>
    {dots}
  </svg>
</figure>'''


def heatmap(matrix: dict[str, dict[str, float]], label: str) -> str:
    """A correlation matrix as a grid of shaded cells.

    Args:
        matrix: {row market: {column market: correlation}}, square, as pandas' to_dict()
            leaves it.
        label: Figure caption.

    Returns:
        An SVG element. Darker means more correlated; the reader is meant to spot the block
        of dark cells that says "one bet, not eight".
    """
    names = list(matrix)
    n = len(names)
    cell = min((W - PAD["l"] - PAD["r"]) / n, 60)
    height = PAD["t"] + n * cell + 40
    cells = []
    for i, row in enumerate(names):
        for j, col in enumerate(names):
            v = matrix[row][col]
            shade = min(abs(v), 1.0)
            colour = REAL if v >= 0 else NULL
            cells.append(
                f'<rect x="{PAD["l"] + j * cell:.1f}" y="{PAD["t"] + i * cell:.1f}" '
                f'width="{cell - 1:.1f}" height="{cell - 1:.1f}" fill="{colour}" '
                f'fill-opacity="{0.15 + 0.7 * shade:.2f}"/>'
                f'<text x="{PAD["l"] + j * cell + cell / 2:.1f}" '
                f'y="{PAD["t"] + i * cell + cell / 2 + 4:.1f}" text-anchor="middle" '
                f'class="tick">{v:.2f}</text>')
    labels = "".join(
        f'<text x="{PAD["l"] - 6}" y="{PAD["t"] + i * cell + cell / 2 + 4:.1f}" '
        f'text-anchor="end" class="tick">{name}</text>' for i, name in enumerate(names))
    return f'''<figure class="fig">
  <figcaption><b>{label}</b></figcaption>
  <svg viewBox="0 0 {W} {height}" role="img" aria-label="{label}">
    {labels}{''.join(cells)}
  </svg>
</figure>'''


def models(rows: list[dict], alpha: float, metric: str) -> str:
    """One bar per way of randomising, against the level it has to clear.

    Args:
        rows: Dicts with keys model and p, in the order they were run.
        alpha: The level, drawn as a rule.
        metric: Which statistic these p-values are for, named in the caption — without it the
            number on the chart is unreadable.

    Returns:
        An SVG element. p is on a linear axis rather than a log one because the question is
        only ever "which side of the line", and a log axis would exaggerate the gap between
        two p-values that both mean the same thing.
    """
    hi = max(alpha * 2, max(r["p"] for r in rows) * 1.15)
    height = 34 * len(rows) + PAD["t"] + 34
    bars = []
    for i, r in enumerate(rows):
        y = PAD["t"] + i * 34
        end = _x(r["p"], 0, hi, NAMES)
        clears = "clears" if r["p"] <= alpha else "misses"
        bars.append(
            f'<rect x="{NAMES}" y="{y}" width="{max(end - NAMES, 1):.1f}" height="20" '
            f'rx="4" fill="{NULL}"/>'
            f'<text x="{NAMES - 10}" y="{y + 15}" text-anchor="end" class="tick">'
            f'{r["model"]}</text>'
            f'<text x="{end + 8:.1f}" y="{y + 15}" class="mark {clears}">p = {r["p"]:.4f}</text>')
    rule = _x(alpha, 0, hi, NAMES)
    return f'''<figure class="fig">
  <figcaption><b>Modelos de aleatorización — p sobre {metric}</b>
    <span>si discrepan, el resultado dependía de una suposición y no sólo del timing</span></figcaption>
  <svg viewBox="0 0 {W} {height}" role="img" aria-label="p-valor por modelo">
    <line x1="{rule:.1f}" y1="{PAD['t'] - 10}" x2="{rule:.1f}" y2="{height - 34}"
          stroke="{REAL}" stroke-width="2" stroke-dasharray="4 3"/>
    <text x="{rule + 8:.1f}" y="{PAD['t'] - 14}" class="mark">límite 0,05</text>
    {''.join(bars)}
  </svg>
</figure>'''


def p_curve(points: list[dict], reference: dict | None, alpha: float, floor: float,
            label: str) -> str:
    """One model's p across the window sweep, widest window on the left, on a log axis.

    Args:
        points: Dicts with keys name and detail, the two lines of the axis label, and p —
            None where it was withheld.
        reference: {"name", "p"} of the model drawn flat across the sweep, or None.
        alpha: diagnostics.alpha, drawn dotted.
        floor: The smallest p the draws can produce, 1/(draws+1): the bottom of the axis.
        label: Figure caption.

    Returns:
        An SVG element with its legend. p = 1 is the top, so a curve that climbs as the window
        shrinks is a pass the regime was carrying. A withheld point is a cross on the top edge
        and never a number: its null had no room to say anything. The flat lines are named in
        the legend rather than on the plot, where they collided with the points near alpha.
    """
    top, bottom, span = PAD["t"], H - PAD["b"], -math.log10(floor)

    def _y(p: float) -> float:
        """Position a p-value on the log axis, 1 at the top."""
        return top + -math.log10(max(p, floor)) / span * (bottom - top)

    def _flat(p: float, colour: str, dash: str) -> str:
        """A horizontal reference line across the plot."""
        return (f'<line x1="{PAD["l"]}" y1="{_y(p):.1f}" x2="{W - PAD["r"]}" y2="{_y(p):.1f}" '
                f'stroke="{colour}" stroke-width="2" stroke-dasharray="{dash}"/>')

    xs = [_x(i, -0.5, len(points) - 0.5) for i in range(len(points))]
    grid = "".join(
        f'<line x1="{PAD["l"]}" y1="{_y(t):.1f}" x2="{W - PAD["r"]}" y2="{_y(t):.1f}" '
        f'stroke="{GRID}"/><text x="{PAD["l"] - 8}" y="{_y(t) + 4:.1f}" text-anchor="end" '
        f'class="tick">{t:g}</text>' for t in (10.0 ** -k for k in range(int(span) + 1)))
    names = "".join(f'<text x="{x:.1f}" y="{bottom + 18}" text-anchor="middle" class="tick">'
                    f'{p["name"]}</text><text x="{x:.1f}" y="{bottom + 33}" '
                    f'text-anchor="middle" class="tick">{p["detail"]}</text>'
                    for x, p in zip(xs, points))
    keys = [(f"border-top:3px solid {NULL}", "p del modelo en cada tamaño"),
            (f"border-top:2px dotted {INK}", f"α = {alpha:g}")]
    lines = _flat(alpha, INK, "2 4")
    if reference is not None:
        lines += _flat(reference["p"], REAL, "7 4")
        keys.append((f"border-top:2px dashed {REAL}",
                     f'{reference["name"]} · p = {reference["p"]:.4f}'))
    done = [(x, p["p"]) for x, p in zip(xs, points) if p["p"] is not None]
    path = " ".join(f"{x:.1f},{_y(p):.1f}" for x, p in done)
    marks = (f'<polyline points="{path}" fill="none" stroke="{NULL}" stroke-width="2"/>'
             + "".join(f'<circle cx="{x:.1f}" cy="{_y(p):.1f}" r="4.5" fill="{NULL}"/>'
                       f'<text x="{x:.1f}" y="{_y(p) - 11:.1f}" text-anchor="middle" '
                       f'class="mark">{p:.4f}</text>' for x, p in done)
             + "".join(f'<text x="{x:.1f}" y="{top + 5}" text-anchor="middle" '
                       f'class="mark misses">✕ no fiable</text>'
                       for x, p in zip(xs, points) if p["p"] is None))
    return (f'<figure class="fig">\n  <figcaption><b>{label}</b>{legend(keys)}</figcaption>\n'
            f'  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{label}">\n'
            f'    {grid}{lines}{marks}{names}\n  </svg>\n</figure>')
