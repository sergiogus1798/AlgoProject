"""The study's three figures: what a task cost, the envelope of its re-runs, and its outcome."""

import numpy as np

from strategies.retest.inputs import tasks
from strategies.retest.render.svg import (GAP, GRID, H, PAD, REAL, SIM, W, box, legend, line,
                                          num, xpos, ypos)


def distribution(values: np.ndarray, observed: float, title: str, subtitle: str,
                 unit: str, bins: int = 48) -> str:
    """One task's outcomes with the unperturbed backtest marked on them.

    Args:
        values: One value per simulation.
        observed: The original backtest's value of the same metric.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.
        unit: Axis label.
        bins: Histogram resolution.

    Returns:
        An SVG element. The bars are the re-runs, the rule is what actually happened. Where
        the rule sits inside the bars is the whole reading -- far to the right means the
        real backtest was luckier than almost every plausible version of the same world.
    """
    counts, edges = np.histogram(values, bins=bins)
    lo, hi = float(edges[0]), float(edges[-1])
    top, floor = int(counts.max()) or 1, H - PAD["b"]
    width = (W - PAD["l"] - PAD["r"]) / bins
    total, cum, bars = int(counts.sum()) or 1, 0, []
    for i, n in enumerate(counts):
        if not n:
            continue
        cum += int(n)
        tip = (f"{num(float(edges[i]))} a {num(float(edges[i + 1]))}&#10;{n:,} simulaciones"
               f"&#10;Percentil hasta aqui: {100 * cum / total:.0f}")
        bars.append(f'<rect x="{PAD["l"] + i * width:.1f}" '
                    f'y="{floor - n / top * (floor - PAD["t"]):.1f}" '
                    f'width="{max(width - GAP, 0.5):.1f}" '
                    f'height="{n / top * (floor - PAD["t"]):.1f}" rx="1" fill="{SIM}">'
                    f'<title>{tip}</title></rect>')
    axis = "".join(f'<text x="{xpos(lo + (hi - lo) * i / 4, lo, hi):.1f}" y="{floor + 18}" '
                   f'text-anchor="middle" class="tick">{num(lo + (hi - lo) * i / 4)}</text>'
                   for i in range(5))
    at = xpos(min(max(observed, lo), hi), lo, hi)
    side = "end" if at > W * 0.62 else "start"
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <line x1="{PAD['l']}" y1="{floor}" x2="{W - PAD['r']}" y2="{floor}" stroke="{GRID}"/>
    {"".join(bars)}
    <line x1="{at:.1f}" y1="{PAD['t'] - 10}" x2="{at:.1f}" y2="{floor}" stroke="{REAL}"
          stroke-width="2"/>
    <text x="{at + (-8 if side == 'end' else 8):.1f}" y="{PAD['t'] - 14}"
          text-anchor="{side}" class="mark">Sin perturbar {num(observed)}</text>
    {axis}
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">{unit}</text>
  </svg>
  {legend([(box(SIM, 0.9), "Re-ejecuciones — pasa el raton por una barra"),
           (line(REAL), "Backtest sin perturbar")])}
</figure>'''


def fan(band: dict, title: str, subtitle: str) -> str:
    """The equity curves a perturbed world could have produced.

    Args:
        band: What verdict.fragility.fan() returned.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.

    Returns:
        An SVG element: the outer and inner bands as filled areas and the median on top.
        **The x-axis is progress from 0 to 1, not the trade number.** Simulations differ in
        length -- one may place 676 trades and another 2,031 -- so there is no common trade
        index to stack them on, and every curve is interpolated onto a shared grid instead.
        There is no real curve drawn over it, because the unperturbed backtest has its own
        trade count and would be a fourth length rather than a reference.
    """
    levels = sorted(band["bands"])
    grid = band["progress"]
    every = [v for row in band["bands"].values() for v in row]
    lo, hi = float(min(every)), float(max(every))

    def path(values: list, back: list | None = None) -> str:
        """One polyline, optionally closed with a second series drawn backwards.

        Args:
            values: The series to draw, one value per grid point.
            back: A second series drawn in reverse to close the polygon, or None for a line.

        Returns:
            An SVG points string.
        """
        head = " ".join(f"{xpos(s, 0, 1):.1f},{ypos(v, lo, hi):.1f}" for s, v in zip(grid, values))
        if back is None:
            return head
        tail = " ".join(f"{xpos(s, 0, 1):.1f},{ypos(v, lo, hi):.1f}"
                        for s, v in zip(reversed(grid), reversed(list(back))))
        return f"{head} {tail}"

    mid = band["bands"][levels[len(levels) // 2]]
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <line x1="{PAD['l']}" y1="{ypos(0, lo, hi):.1f}" x2="{W - PAD['r']}"
          y2="{ypos(0, lo, hi):.1f}" stroke="{GRID}" stroke-dasharray="3 3"/>
    <polygon points="{path(band['bands'][levels[0]], band['bands'][levels[-1]])}"
             fill="{SIM}" opacity="0.18"/>
    <polygon points="{path(band['bands'][levels[1]], band['bands'][levels[-2]])}"
             fill="{SIM}" opacity="0.28"/>
    <polyline points="{path(mid)}" fill="none" stroke="{SIM}" stroke-width="1.8"/>
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">
      avance de la simulacion, 0 a 1</text>
    <text x="{PAD['l'] - 8}" y="{ypos(hi, lo, hi):.1f}" text-anchor="end" class="tick">{hi:,.0f}</text>
    <text x="{PAD['l'] - 8}" y="{ypos(lo, lo, hi):.1f}" text-anchor="end" class="tick">{lo:,.0f}</text>
  </svg>
  {legend([(box(SIM, 0.18), f"Banda {levels[0]}-{levels[-1]}"),
           (box(SIM, 0.35), f"Banda {levels[1]}-{levels[-2]}"),
           (line(SIM), "Mediana de las re-ejecuciones")])}
</figure>'''


def cost(ranking: list[dict], sigma: float, title: str, subtitle: str) -> str:
    """What each perturbation cost, in units of the noise floor.

    Args:
        ranking: What verdict.attribution.ranking() returned.
        sigma: The control task's own dispersion, USD.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.

    Returns:
        A horizontal bar per task, longest first, measured in control sigmas. The control
        is the denominator and is not drawn: a re-run moves the result even when nothing
        meaningful changed, and a bar shorter than one sigma is noise, not a finding.
        A negative bar is a task that *improved* the median, which happens and is worth
        seeing rather than clipping to zero.
    """
    rows = ranking[:7]
    reach = max(abs(row["cost_in_sigmas"]) for row in rows) or 1.0
    lo, hi = -reach * 1.1, reach * 1.1
    height = (H - PAD["t"] - PAD["b"]) / max(len(rows), 1)
    zero = xpos(0, lo, hi)
    bars = []
    for i, row in enumerate(rows):
        at = xpos(row["cost_in_sigmas"], lo, hi)
        y = PAD["t"] + i * height + GAP
        left, wide = min(zero, at), abs(at - zero)
        tip = (f"{tasks.TITLES[row['task']]}&#10;{row['cost']:,.0f} USD"
               f"&#10;{row['cost_in_sigmas']:.1f} sigmas del control")
        bars.append(
            f'<rect x="{left:.1f}" y="{y:.1f}" width="{max(wide, 1):.1f}" '
            f'height="{max(height - 2 * GAP, 2):.1f}" rx="2" '
            f'fill="{REAL if row["cost_in_sigmas"] > 0 else SIM}" opacity="0.85">'
            f'<title>{tip}</title></rect>'
            f'<text x="{PAD["l"] - 8}" y="{y + height / 2:.1f}" text-anchor="end" '
            f'dominant-baseline="middle" class="tick">{tasks.TITLES[row["task"]]}</text>')
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <line x1="{zero:.1f}" y1="{PAD['t']}" x2="{zero:.1f}" y2="{H - PAD['b']}" stroke="{GRID}"/>
    {"".join(bars)}
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">
      coste en sigmas del control (el control mueve {sigma:,.0f} USD por si solo)</text>
  </svg>
  {legend([(box(REAL, 0.85), "Empeora el resultado"),
           (box(SIM, 0.85), "Lo mejora")])}
</figure>'''
