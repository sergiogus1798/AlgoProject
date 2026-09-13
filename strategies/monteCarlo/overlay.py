"""The IS/OOS overlay: two histograms on one axis, so a drift between them is visible at a
glance instead of read off two separate tables."""

from collections.abc import Callable

from strategies.monteCarlo import panel
from strategies.monteCarlo.charts import GRID, H, PAD, REAL, SIM, W, _box, _line, legend, num

COLOR = {"IS": SIM, "OOS": REAL}
DASH = {"Backtest": "", "Mediana": "5 3", "Percentil": "1.5 3"}


def _bars(shape: dict, color: str, x: Callable[[float], float], label: Callable) -> str:
    """One scope's histogram, translucent so the other one shows through, with a tooltip
    per bar: its range, its share of the simulations, and the running percentile."""
    counts, top = shape["counts"], max(shape["counts"]) or 1
    floor = H - PAD["b"]
    lo, hi = shape["lo"], shape["hi"]
    width = (x(hi) - x(lo)) / len(counts)
    total, cum, bars = sum(counts) or 1, 0, []
    for i, n in enumerate(counts):
        if not n:
            continue
        cum += n
        edge_lo, edge_hi = lo + i * (hi - lo) / len(counts), lo + (i + 1) * (hi - lo) / len(counts)
        tip = (f"{label(edge_lo)} a {label(edge_hi)}&#10;{n:,} simulaciones "
              f"({n / total:.1%})&#10;Percentil hasta aquí: {100 * cum / total:.0f}")
        bars.append(f'<rect x="{x(lo) + i * width:.1f}" '
                    f'y="{floor - n / top * (floor - PAD["t"]):.1f}" '
                    f'width="{max(width - 1, 0.5):.1f}" '
                    f'height="{n / top * (floor - PAD["t"]):.1f}" fill="{color}" '
                    f'opacity="0.45"><title>{tip}</title></rect>')
    return "".join(bars)


def _marks(shape: dict, color: str, x: Callable[[float], float], q: int) -> str:
    """One scope's backtest, median and reference-percentile lines, each its own dash."""
    floor = H - PAD["b"]
    values = [("Backtest", shape["observed"]), ("Mediana", shape["median"]),
             ("Percentil", shape["p_report"])]
    return "".join(
        f'<line x1="{x(v):.1f}" y1="{PAD["t"]}" x2="{x(v):.1f}" y2="{floor}" '
        f'stroke="{color}" stroke-width="1.5" stroke-dasharray="{DASH[name]}">'
        f'<title>{name if name != "Percentil" else f"Percentil {q}"} ({("IS" if color == SIM else "OOS")}): '
        f'{v:,.4g}</title></line>'
        for name, v in values)


def figure(is_: dict, oos: dict, title: str, unit: str, q: int, pct: bool = False) -> str:
    """Both scopes' distributions on one shared axis.

    Args:
        is_: What metrics.shape() returned for the in-sample trades.
        oos: What metrics.shape() returned for the out-of-sample trades.
        title: Figure title.
        unit: Axis label.
        q: The percentile both scopes mark — cfg["global"]["report_percentile"].
        pct: True for a statistic stored as a fraction (dd_pct) — reads in percent.

    Returns:
        An SVG element: both histograms overlaid at half opacity, each scope's backtest
        (solid), median (dashed) and reference percentile (dotted) marked in that scope's
        own colour — colour says which sample, line style says which number. Pass the mouse
        over a bar or a line for its exact numbers.
    """
    label = (lambda v: f"{v * 100:,.1f}%") if pct else num
    lo, hi = min(is_["lo"], oos["lo"]), max(is_["hi"], oos["hi"])
    span = (hi - lo) or 1.0

    def x(v: float) -> float:
        """A data value to a pixel column, shared by both histograms."""
        return PAD["l"] + (v - lo) / span * (W - PAD["l"] - PAD["r"])

    floor = H - PAD["b"]
    zero = (f'<line x1="{x(0):.1f}" y1="{PAD["t"]}" x2="{x(0):.1f}" y2="{floor}" '
            f'stroke="{GRID}" stroke-dasharray="2 2"/>') if lo <= 0 <= hi else ""
    axis = "".join(f'<text x="{x(lo + span * i / 4):.1f}" y="{floor + 18}" '
                   f'text-anchor="middle" class="tick">{label(lo + span * i / 4)}</text>'
                   for i in range(5))
    return f'''<figure class="fig">
  <figcaption><b>{title}</b></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    <line x1="{PAD['l']}" y1="{floor}" x2="{W - PAD['r']}" y2="{floor}" stroke="{GRID}"/>
    {zero}
    {_bars(is_, COLOR["IS"], x, label)}{_bars(oos, COLOR["OOS"], x, label)}
    {_marks(is_, COLOR["IS"], x, q)}{_marks(oos, COLOR["OOS"], x, q)}
    {axis}
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">{unit}</text>
  </svg>
  {legend([(_box(COLOR["IS"], 0.55), "Dentro de muestra"),
          (_box(COLOR["OOS"], 0.55), "Fuera de muestra"),
          (_line("var(--ink-2)"), "Backtest"), (_line("var(--ink-2)", "dashed"), "Mediana"),
          (_line("var(--ink-2)", "dotted"), f"Percentil {q}")])}
</figure>'''


def section(entry: dict, title: str, unit: str, q: int, pct: bool = False) -> str:
    """One family's IS/OOS degradation check, or a note when a scope lacks trades.

    Args:
        entry: {"IS": shape|None, "OOS": shape|None, "metric": name} from degrade.overlay().
        title: Figure title.
        unit: Axis label.
        q: The percentile both scopes mark — cfg["global"]["report_percentile"].
        pct: As figure().

    Returns:
        The overlaid figure and a small numeric table, or an explanatory note.
    """
    is_, oos = entry.get("IS"), entry.get("OOS")
    if is_ is None or oos is None:
        return ('<div class="note">No hay suficientes operaciones dentro o fuera de '
                'muestra para comparar esta distribución.</div>')
    fmt = (lambda v: f"{v * 100:,.1f}%") if pct else (lambda v: f"{v:,.4g}")
    rows = [[name, f"{shape['n']:,}", fmt(shape["observed"]), fmt(shape["median"]),
            fmt(shape["p_report"])]
           for name, shape in (("Dentro de muestra", is_), ("Fuera de muestra", oos))]
    return (figure(is_, oos, title, unit, q, pct)
            + panel.table(["Muestra", "Operaciones", "Backtest", "Mediana",
                           f"Percentil {q}"], rows))
