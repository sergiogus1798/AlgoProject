"""Draw the study's figures as inline SVG: nothing to load, nothing to run in the browser."""

W, H = 760, 300                       # one figure, wide enough for 60 bins at 2px apart
PAD = {"l": 56, "r": 20, "t": 28, "b": 46}
NAMES = 150                           # room for a model name; "resampled_holds" must not clip
NULL, REAL, GRID, INK = "var(--null)", "var(--real)", "var(--grid)", "var(--ink-2)"
GAP = 2                               # surface gap between adjacent bars


def _x(value: float, lo: float, hi: float, left: int = PAD["l"]) -> float:
    """Position a data value on the horizontal axis.

    Args:
        value: The value to place.
        lo, hi: Axis extent in data units.
        left: Left margin, wider when the rows carry names rather than ticks.

    Returns:
        A pixel coordinate inside the plot area.
    """
    span = hi - lo or 1.0
    return left + (value - lo) / span * (W - left - PAD["r"])


def _ticks(lo: float, hi: float, count: int = 5) -> list[float]:
    """Evenly spaced axis values.

    Args:
        lo, hi: Axis extent.
        count: How many ticks.

    Returns:
        The tick values, ends included.
    """
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def distribution(shape: dict, title: str, subtitle: str) -> str:
    """The null distribution with the real run marked on it.

    Args:
        shape: What inference.shape() returned.
        title: Figure title, normally the market.
        subtitle: One line saying what the reader is looking at.

    Returns:
        An SVG element. The bars are the 5,000 random runs; the single rule is the real one.
        Two marks, two colours, both direct-labelled — the reader never has to consult a key
        to know which is which.
    """
    counts, lo, hi = shape["counts"], shape["lo"], shape["hi"]
    top, floor = max(counts) or 1, H - PAD["b"]
    width = (W - PAD["l"] - PAD["r"]) / len(counts)
    bars = []
    for i, n in enumerate(counts):
        if not n:
            continue
        height = n / top * (floor - PAD["t"])
        bars.append(f'<rect x="{PAD["l"] + i * width:.1f}" y="{floor - height:.1f}" '
                    f'width="{max(width - GAP, 0.5):.1f}" height="{height:.1f}" rx="1" '
                    f'fill="{NULL}"/>')
    axis = "".join(
        f'<text x="{_x(t, lo, hi):.1f}" y="{floor + 18}" text-anchor="middle" '
        f'class="tick">{t:+.2f}</text>' for t in _ticks(lo, hi))
    at = _x(shape["real"], lo, hi)
    side = "end" if at > W * 0.62 else "start"
    nudge = -8 if side == "end" else 8
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}: {subtitle}">
    <line x1="{PAD['l']}" y1="{floor}" x2="{W - PAD['r']}" y2="{floor}" stroke="{GRID}"/>
    {''.join(bars)}
    <line x1="{at:.1f}" y1="{PAD['t'] - 10}" x2="{at:.1f}" y2="{floor}" stroke="{REAL}"
          stroke-width="2"/>
    <text x="{at + nudge:.1f}" y="{PAD['t'] - 14}" text-anchor="{side}" class="mark">
      real {shape['real']:+.3f}</text>
    <text x="{PAD['l']}" y="{PAD['t'] - 14}" class="tick">5.000 aleatorios</text>
    {axis}
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">
      retorno medio por operación, en barras típicas del mercado</text>
  </svg>
</figure>'''


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


def models(rows: list[dict], alpha: float) -> str:
    """One bar per way of randomising, against the level it has to clear.

    Args:
        rows: Dicts with keys model, p and randomises, in the order they were run.
        alpha: The level, drawn as a rule.

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
  <figcaption><b>Modelos de aleatorización</b>
    <span>si discrepan, el resultado dependía de una suposición y no del timing</span></figcaption>
  <svg viewBox="0 0 {W} {height}" role="img" aria-label="p-valor por modelo">
    <line x1="{rule:.1f}" y1="{PAD['t'] - 10}" x2="{rule:.1f}" y2="{height - 34}"
          stroke="{REAL}" stroke-width="2" stroke-dasharray="4 3"/>
    <text x="{rule + 8:.1f}" y="{PAD['t'] - 14}" class="mark">límite 0,05</text>
    {''.join(bars)}
  </svg>
</figure>'''
