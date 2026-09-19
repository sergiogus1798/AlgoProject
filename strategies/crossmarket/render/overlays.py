"""The two figures that lay several series over one axis: market equity curves, and two
distributions drawn through each other. Both answer "is this the same shape?" by eye, which
no table does."""

import datetime as dt

from strategies.crossmarket.render.svg import GRID, H, PAD, W, legend, num, tickvals

TALL = 420          # the equity overlay is the page's main figure and gets room to be read
FADE = 0.45         # the base asset's fill, so the market on top stays legible through it


def _day(iso: str) -> int:
    """One ISO date as a day number, for positioning on a real calendar axis."""
    return dt.date.fromisoformat(iso).toordinal()


def equity(curves: dict[str, dict], colours: dict[str, str], base: str, label: str,
           note: str, lead_note: str = "activo base") -> str:
    """Every market's equity on one shared calendar axis, each on its own account.

    Args:
        curves: {feed: what curves.series() returned}.
        colours: {feed: CSS colour}, so a market keeps its colour across the whole panel.
        base: The series drawn thicker — the base asset here, the combined account in the
            portfolio tab.
        label: Figure title.
        note: The line under it.
        lead_note: What that thicker series is, said once in the legend.

    Returns:
        An SVG element. The x axis is real calendar time over the union of every market's own
        window, so a market whose backtest began later **starts later on the chart** instead
        of being stretched to share an origin it never had. The y axis is per cent of each
        market's own starting account, which is what makes curves of different position sizes
        comparable at all.
    """
    days = [d for c in curves.values() for d in map(_day, c["dates"])]
    values = [v for c in curves.values() for v in c["pct"]] + [0.0]
    x0, x1 = min(days), max(days)
    lo, hi = min(values), max(values)
    floor, top = TALL - PAD["b"], PAD["t"]

    def _px(day: int) -> float:
        """Horizontal pixel of a calendar day."""
        return PAD["l"] + (day - x0) / max(x1 - x0, 1) * (W - PAD["l"] - PAD["r"])

    def _py(value: float) -> float:
        """Vertical pixel of a per-cent value."""
        return floor - (value - lo) / ((hi - lo) or 1.0) * (floor - top)

    grid = "".join(
        f'<line x1="{PAD["l"]}" y1="{_py(v):.1f}" x2="{W - PAD["r"]}" y2="{_py(v):.1f}" '
        f'stroke="{GRID}"/><text x="{PAD["l"] - 6}" y="{_py(v) + 4:.1f}" text-anchor="end" '
        f'class="tick">{num(v)}%</text>' for v in tickvals(lo, hi, 6))
    ticks = "".join(
        f'<text x="{_px(int(d)):.1f}" y="{floor + 18}" text-anchor="middle" class="tick">'
        f'{dt.date.fromordinal(int(d)).year}</text>' for d in tickvals(x0, x1, 7))
    lines, keys = [], []
    for feed, c in curves.items():
        points = " ".join(f"{_px(_day(d)):.1f},{_py(v):.1f}"
                          for d, v in zip(c["dates"], c["pct"]))
        wide = feed == base
        lines.append(f'<polyline points="{points}" fill="none" stroke="{colours[feed]}" '
                     f'stroke-width="{3.2 if wide else 2}" '
                     f'stroke-opacity="{1 if wide else 0.9}"/>')
        keys.append((f'border-top:{"4px" if wide else "3px"} solid {colours[feed]}',
                     f"{feed}{' · ' + lead_note if wide else ''} · {c['pct'][-1]:+.1f}%"))
    zero = (f'<line x1="{PAD["l"]}" y1="{_py(0):.1f}" x2="{W - PAD["r"]}" y2="{_py(0):.1f}" '
            f'stroke="{GRID}" stroke-width="1.5" stroke-dasharray="4 4"/>')
    return f'''<figure class="fig wide">
  <figcaption><b>{label}</b><span>{note}</span></figcaption>
  <svg viewBox="0 0 {W} {TALL}" role="img" aria-label="{label}">
    {grid}{zero}{''.join(lines)}{ticks}
  </svg>
  {legend(keys)}
</figure>'''


def distributions(shape: dict, market: str, base: str, colour: str,
                  base_colour: str) -> str:
    """One quantity's distribution on this market, drawn through the base asset's.

    Args:
        shape: What fingerprint.overlay() returned — shared edges and two share arrays.
        market: This market's feed, for the legend.
        base: The base asset's feed.
        colour, base_colour: Their colours, the same ones they carry everywhere else.

    Returns:
        An SVG element. Both series are shares of their own trade count, not counts, so a
        market with 300 trades and one with 900 are compared on shape alone. Semi-transparent
        fills rather than bars side by side: side by side, the eye compares neighbours, and
        the question here is whether one distribution sits **inside** the other.
    """
    bars, top = shape["market"], max(max(shape["market"]), max(shape["base"]), 1e-9)
    floor = H - PAD["b"]
    step = (W - PAD["l"] - PAD["r"]) / len(bars)
    layers = []
    for values, fill, opacity in ((shape["base"], base_colour, FADE),
                                  (shape["market"], colour, 0.62)):
        rects = "".join(
            f'<rect x="{PAD["l"] + i * step:.1f}" '
            f'y="{floor - v / top * (floor - PAD["t"]):.1f}" width="{step:.1f}" '
            f'height="{v / top * (floor - PAD["t"]):.1f}" fill="{fill}"/>'
            for i, v in enumerate(values) if v)
        layers.append(f'<g fill-opacity="{opacity}">{rects}</g>')
    ticks = "".join(
        f'<text x="{PAD["l"] + (t - shape["lo"]) / ((shape["hi"] - shape["lo"]) or 1) * (W - PAD["l"] - PAD["r"]):.1f}" '
        f'y="{floor + 18}" text-anchor="middle" class="tick">{num(t)}</text>'
        for t in tickvals(shape["lo"], shape["hi"], 5))
    return f'''<figure class="fig">
  <figcaption><b>{shape["label"]}</b><span>{shape["unit"]} · eje recortado en el
    percentil 99 de las dos series juntas</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{shape['label']}">
    <line x1="{PAD['l']}" y1="{floor}" x2="{W - PAD['r']}" y2="{floor}" stroke="{GRID}"/>
    {''.join(layers)}{ticks}
  </svg>
  {legend([(f"background:{colour};opacity:.62", market),
           (f"background:{base_colour};opacity:{FADE}", f"{base} · activo base")])}
</figure>'''
