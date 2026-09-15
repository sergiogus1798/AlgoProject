"""Draw the study's figures as inline SVG: nothing to load, nothing to run in the browser."""

W, H = 760, 300                       # one figure, wide enough for 60 bins at 2px apart
WIDE, NARROW = 820, 620               # the equity/histogram pair, side by side
PAD = {"l": 56, "r": 20, "t": 28, "b": 46}
NAMES = 150                           # room for a model name; "resampled_holds" must not clip
NULL, REAL, GRID, INK = "var(--null)", "var(--real)", "var(--grid)", "var(--ink-2)"
GAP = 2                               # surface gap between adjacent bars


def _x(value: float, lo: float, hi: float, left: int = PAD["l"], width: int = W) -> float:
    """Position a data value on the horizontal axis.

    Args:
        value: The value to place.
        lo, hi: Axis extent in data units.
        left: Left margin, wider when the rows carry names rather than ticks.
        width: Total figure width; the pair of figures beside each other are not W wide.

    Returns:
        A pixel coordinate inside the plot area.
    """
    span = hi - lo or 1.0
    return left + (value - lo) / span * (width - left - PAD["r"])


def _ticks(lo: float, hi: float, count: int = 5) -> list[float]:
    """Evenly spaced axis values.

    Args:
        lo, hi: Axis extent.
        count: How many ticks.

    Returns:
        The tick values, ends included.
    """
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def num(value: float) -> str:
    """One axis or mark number, in the shape a reader expects for its size.

    Args:
        value: The number.

    Returns:
        Thousands separated above 1,000, two decimals down to 1, four significant figures
        below it. The general-purpose format turns 46,191 into 4.619e+04, which is correct
        and unreadable.
    """
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:,.2f}" if abs(value) >= 1 else f"{value:.4g}"


def distribution(shape: dict, title: str, subtitle: str, width: int = W) -> str:
    """One statistic's random distribution, with the real backtest marked on it.

    Args:
        shape: What metrics.shape() returned — counts, range, observed, median, p5, p95.
        title: Figure title, normally the statistic's own sentence.
        subtitle: One line saying what the reader is looking at.
        width: Figure width in viewBox units; NARROW when it sits beside the equity cone.

    Returns:
        An SVG element. The bars are the random runs; the solid rule is the real backtest,
        the dashed one their median, and the two thin ones the 2.5 and 97.5 percentiles,
        with the interval between them shaded. Only the real value is labelled inside the
        figure — the other three numbers live in the table beside it, because at some values
        the labels collided with each other on top of the plot.
    """
    counts, lo, hi = shape["counts"], shape["lo"], shape["hi"]
    top, floor = max(counts) or 1, H - PAD["b"]
    step = (width - PAD["l"] - PAD["r"]) / len(counts)
    bars = []
    for i, n in enumerate(counts):
        if not n:
            continue
        height = n / top * (floor - PAD["t"])
        bars.append(f'<rect x="{PAD["l"] + i * step:.1f}" y="{floor - height:.1f}" '
                    f'width="{max(step - GAP, 0.5):.1f}" height="{height:.1f}" rx="1" '
                    f'fill="{NULL}"/>')
    left, right = (_x(shape[k], lo, hi, width=width) for k in ("lo_ci", "hi_ci"))
    band = (f'<rect x="{left:.1f}" y="{PAD["t"]}" width="{max(right - left, 1):.1f}" '
            f'height="{floor - PAD["t"]:.1f}" fill="{NULL}" fill-opacity="0.12"/>'
            + "".join(f'<line x1="{x:.1f}" y1="{PAD["t"]}" x2="{x:.1f}" y2="{floor}" '
                      f'stroke="{NULL}" stroke-width="1" stroke-dasharray="2 3"/>'
                      for x in (left, right)))
    axis = "".join(
        f'<text x="{_x(t, lo, hi, width=width):.1f}" y="{floor + 18}" text-anchor="middle" '
        f'class="tick">{num(t)}</text>' for t in _ticks(lo, hi, 4))
    mid = _x(shape["median"], lo, hi, width=width)
    at = _x(shape["observed"], lo, hi, width=width)
    side = "end" if at > width * 0.6 else "start"
    nudge = -8 if side == "end" else 8
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {width} {H}" role="img" aria-label="{title}">
    {band}
    <line x1="{PAD['l']}" y1="{floor}" x2="{width - PAD['r']}" y2="{floor}" stroke="{GRID}"/>
    {''.join(bars)}
    <line x1="{mid:.1f}" y1="{PAD['t']}" x2="{mid:.1f}" y2="{floor}" stroke="{INK}"
          stroke-width="1.5" stroke-dasharray="5 4"/>
    <line x1="{at:.1f}" y1="{PAD['t'] - 10}" x2="{at:.1f}" y2="{floor}" stroke="{REAL}"
          stroke-width="2.5"/>
    <text x="{at + nudge:.1f}" y="{PAD['t'] - 14}" text-anchor="{side}" class="mark">
      real {num(shape['observed'])}</text>
    {axis}
  </svg>
  {legend([(f"border-top:3px solid {REAL}", "backtest real"),
           (f"border-top:3px dashed var(--ink-2)", "mediana simulada"),
           (f"background:{NULL};opacity:.25", "IC 95% de las simulaciones (p2,5-p97,5)")])}
</figure>'''


def cone(shape: dict, title: str, subtitle: str, width: int = W) -> str:
    """The equity of the real backtest laid over the envelope of the simulated ones.

    Args:
        shape: What backtest.run()'s "cone" holds — bands keyed by percentile, the observed
            curve, and one date per step.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.
        width: Figure width in viewBox units.

    Returns:
        An SVG element. The x axis is **calendar time**, and it spans exactly the backtest's
        own window — first entry to last exit — because that is the stretch the random runs
        are confined to as well (`envelope.window`). The bands darken toward the middle, so
        the eye reads the density rather than counting edges, and the two outermost
        percentiles are drawn as lines of their own because they are the interval a reader
        quotes. Read the cone for its width and for where the real curve leaves it, never
        for any single line inside it.
    """
    qs = sorted(shape["bands"], key=float)
    seen = shape["observed"]
    steps = len(seen)
    curves = [shape["bands"][q] for q in qs] + [seen]
    lo, hi = min(min(c) for c in curves), max(max(c) for c in curves)
    floor, top = H - PAD["b"], PAD["t"]

    def _px(i: int) -> float:
        """Horizontal pixel of time step i."""
        return PAD["l"] + i / max(steps - 1, 1) * (width - PAD["l"] - PAD["r"])

    def _py(v: float) -> float:
        """Vertical pixel of an equity value."""
        return floor - (v - lo) / ((hi - lo) or 1.0) * (floor - top)

    def _poly(values: list[float]) -> str:
        """One polyline's point list."""
        return " ".join(f"{_px(i):.1f},{_py(v):.1f}" for i, v in enumerate(values))

    # Opacity rises toward the median band, so the middle of the distribution looks denser
    # than its tails instead of every ring looking equally likely.
    pairs = list(zip(qs, qs[1:]))
    fills = []
    for k, (a, b) in enumerate(pairs):
        depth = 1 - abs(k - (len(pairs) - 1) / 2) / max(len(pairs) / 2, 1)
        edge = _poly(shape["bands"][a]) + " " + " ".join(
            f"{_px(i):.1f},{_py(v):.1f}"
            for i, v in reversed(list(enumerate(shape["bands"][b]))))
        fills.append(f'<polygon points="{edge}" fill="{NULL}" '
                     f'fill-opacity="{0.10 + 0.22 * depth:.2f}"/>')
    edges = "".join(
        f'<polyline points="{_poly(shape["bands"][q])}" fill="none" stroke="{NULL}" '
        f'stroke-width="1" stroke-opacity="0.75" stroke-dasharray="2 3"/>'
        for q in (qs[0], qs[-1]))
    middle = qs[len(qs) // 2]
    ticks = "".join(
        f'<text x="{_px(i):.1f}" y="{floor + 18}" text-anchor="middle" class="tick">'
        f'{shape["dates"][i][:7]}</text>'
        for i in range(0, steps, max(steps // 6, 1)))
    grid = "".join(
        f'<line x1="{PAD["l"]}" y1="{_py(v):.1f}" x2="{width - PAD["r"]}" y2="{_py(v):.1f}" '
        f'stroke="{GRID}"/>'
        f'<text x="{PAD["l"] - 6}" y="{_py(v) + 4:.1f}" text-anchor="end" class="tick">'
        f'{num(v)}</text>' for v in _ticks(lo, hi, 5))
    end = shape["observed"][-1]
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {width} {H}" role="img" aria-label="{title}">
    {grid}{''.join(fills)}{edges}
    <polyline points="{_poly(shape['bands'][middle])}" fill="none" stroke="{NULL}"
              stroke-width="1.5" stroke-dasharray="5 4"/>
    <polyline points="{_poly(shape['observed'])}" fill="none" stroke="{REAL}"
              stroke-width="2.5"/>
    <circle cx="{_px(steps - 1):.1f}" cy="{_py(end):.1f}" r="3.5" fill="{REAL}"/>
    {ticks}
  </svg>
  {legend([(f"border-top:3px solid {REAL}", "backtest real"),
           (f"border-top:3px dashed {NULL}", "mediana simulada"),
           (f"background:{NULL};opacity:.32", "cuartiles p25-p75"),
           (f"background:{NULL};opacity:.12", "IC 95% (p2,5-p97,5)")])}
</figure>'''


def legend(items: list[tuple[str, str]]) -> str:
    """A row of colour-coded chips under a figure, instead of a caption to decode.

    Args:
        items: (swatch style, label) pairs, the style matching what the figure drew.

    Returns:
        One HTML block, script-free so it renders the same in the panel and anywhere else.
    """
    chips = "".join(f'<span class="chip"><i style="{style}"></i>{label}</span>'
                    for style, label in items)
    return f'<div class="legend">{chips}</div>'
