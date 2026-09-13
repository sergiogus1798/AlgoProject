"""Family D's two time-indexed figures: equity against its calendar windows, and price
against the volatility regime."""

from strategies.monteCarlo.charts import GRID, H, PAD, REAL, W, _box, _line, legend, num

PRICE, VOL = "var(--price)", "var(--vol)"
BUCKET_FILL = {"low": "var(--vol-low)", "mid": "var(--vol-mid)", "high": "var(--vol-high)"}


def _scale(values: list[float]) -> tuple[float, float]:
    """Axis extent for one series, widened so a flat line is not a point.

    Args:
        values: The series.

    Returns:
        (lo, hi), never equal.
    """
    lo, hi = min(values), max(values)
    return (lo - 1.0, hi + 1.0) if lo == hi else (lo, hi)


def equity_windows(equity: dict, title: str, subtitle: str) -> str:
    """The backtest's own equity curve, with the non-overlapping windows marked on it.

    Args:
        equity: {"curve": equity value per trade, "marks": trade indices where a window
            starts}, both from run._family_d().
        title: Figure title.
        subtitle: One line saying what the reader is looking at.

    Returns:
        An SVG element: one line, the real curve, with a dashed vertical rule at each
        window boundary — the same blocks the table above and below it scores.
    """
    curve = equity["curve"]
    last = max(len(curve) - 1, 1)
    lo, hi = _scale(curve)

    def x(i: float) -> float:
        """Trade index to a pixel column."""
        return PAD["l"] + i / last * (W - PAD["l"] - PAD["r"])

    def y(v: float) -> float:
        """Equity value to a pixel row."""
        return H - PAD["b"] - (v - lo) / (hi - lo) * (H - PAD["b"] - PAD["t"])

    line = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(curve))
    marks = "".join(f'<line x1="{x(m):.1f}" y1="{PAD["t"]}" x2="{x(m):.1f}" '
                    f'y2="{H - PAD["b"]}" stroke="{GRID}" stroke-dasharray="4 3"/>'
                    for m in equity["marks"])
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    {marks}
    <polyline points="{line}" fill="none" stroke="{REAL}" stroke-width="1.5"/>
    <text x="{PAD['l'] - 8}" y="{y(hi):.1f}" text-anchor="end" class="tick">{num(hi)}</text>
    <text x="{PAD['l'] - 8}" y="{y(lo):.1f}" text-anchor="end" class="tick">{num(lo)}</text>
    <text x="{W / 2}" y="{H - 6}" text-anchor="middle" class="tick">operaciones, en orden</text>
  </svg>
  {legend([(_line(REAL), "Equity real"), (_line("var(--grid)", "dashed"),
           "Inicio de un bloque")])}
</figure>'''


def regime_series(series: dict, title: str, subtitle: str) -> str:
    """Price and volatility over the calendar, with the tercile each day fell into.

    Args:
        series: {"dates", "price", "vol", "bucket"} from run._family_d(), one entry per
            day the volatility model could score. "bucket" is 0/1/2 for low/mid/high.
        title: Figure title.
        subtitle: One line saying what the reader is looking at.

    Returns:
        An SVG element: the tercile as a background band, price and volatility as two
        translucent lines on independent scales — hovering either brings it forward, since
        the two are never on the same axis and reading them stacked is the only way to see
        whether the edge's calmer or rougher periods line up with the price trend at all.
    """
    names = ("low", "mid", "high")
    dates, price, vol, bucket = (series["dates"], series["price"], series["vol"],
                                 series["bucket"])
    last = max(len(dates) - 1, 1)
    p_lo, p_hi = _scale(price)
    v_lo, v_hi = _scale(vol)
    right = PAD["r"] + 34   # wider than the shared margin: a second axis needs room too

    def x(i: float) -> float:
        """Day index to a pixel column."""
        return PAD["l"] + i / last * (W - PAD["l"] - right)

    def y(v: float, lo: float, hi: float) -> float:
        """A value to a pixel row, on the given scale."""
        return H - PAD["b"] - (v - lo) / (hi - lo) * (H - PAD["b"] - PAD["t"])

    bands, run_start = [], 0
    for i in range(1, len(bucket) + 1):
        if i == len(bucket) or bucket[i] != bucket[run_start]:
            bands.append(f'<rect x="{x(run_start):.1f}" y="{PAD["t"]}" '
                         f'width="{x(i - 1) - x(run_start) + 1:.1f}" '
                         f'height="{H - PAD["b"] - PAD["t"]}" '
                         f'fill="{BUCKET_FILL[names[bucket[run_start]]]}"/>')
            run_start = i
    price_line = " ".join(f"{x(i):.1f},{y(v, p_lo, p_hi):.1f}" for i, v in enumerate(price))
    vol_line = " ".join(f"{x(i):.1f},{y(v, v_lo, v_hi):.1f}" for i, v in enumerate(vol))
    ticks = "".join(f'<text x="{x(i * last // 4):.1f}" y="{H - PAD["b"] + 18}" '
                    f'text-anchor="middle" class="tick">{dates[i * last // 4][:7]}</text>'
                    for i in range(5))
    return f'''<figure class="fig">
  <figcaption><b>{title}</b><span>{subtitle}</span></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}">
    {"".join(bands)}
    <polyline class="series-price" points="{price_line}" fill="none" stroke="{PRICE}"
              stroke-width="1.5"/>
    <polyline class="series-vol" points="{vol_line}" fill="none" stroke="{VOL}"
              stroke-width="1.5"/>
    <text x="{PAD['l'] - 8}" y="{y(p_hi, p_lo, p_hi):.1f}" text-anchor="end"
          class="tick" fill="{PRICE}">{num(p_hi)}</text>
    <text x="{PAD['l'] - 8}" y="{y(p_lo, p_lo, p_hi):.1f}" text-anchor="end"
          class="tick" fill="{PRICE}">{num(p_lo)}</text>
    <text x="{W - right + 8}" y="{y(v_hi, v_lo, v_hi):.1f}" text-anchor="start"
          class="tick" fill="{VOL}">{num(v_hi)}</text>
    <text x="{W - right + 8}" y="{y(v_lo, v_lo, v_hi):.1f}" text-anchor="start"
          class="tick" fill="{VOL}">{num(v_lo)}</text>
    {ticks}
  </svg>
  {legend([(_line(PRICE), "Precio (eje izq.)"), (_line(VOL), "Volatilidad (eje der.)"),
          (_box("var(--vol-low)"), "Tercil bajo"), (_box("var(--vol-mid)"), "Tercil medio"),
          (_box("var(--vol-high)"), "Tercil alto")])}
</figure>'''
