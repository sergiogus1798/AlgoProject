"""The figure: every parameter tuple as one point, in-sample against out-of-sample."""

import numpy as np
import pandas as pd


W, H = 900, 640
PAD = {"l": 110, "r": 40, "t": 96, "b": 96}
INK, MUTED, GRID = "#14181f", "#5b6675", "#d8dde5"
LABELS = 25          # above this many points, per-point captions stop helping and start hiding
# One hue per stratum, high contrast and distinguishable in greyscale by shape as well.
HUE = {"origin": "#b3261e", "canary": "#8250df", "neighbourhood": "#0969da",
       "factorial": "#1a7f37", "coverage": "#9a6700"}


def _scale(values: np.ndarray, lo_px: float, hi_px: float) -> tuple:
    """A linear mapping from data to pixels, padded so no point sits on the frame.

    Args:
        values: The data this axis has to hold.
        lo_px: Pixel of the low end.
        hi_px: Pixel of the high end.

    Returns:
        (function, low, high) with the domain widened 8 % at each end.
    """
    lo, hi = float(np.min(values)), float(np.max(values))
    pad = (hi - lo) * 0.08 or (abs(hi) or 1) * 0.08
    lo, hi = lo - pad, hi + pad
    return (lambda v: lo_px + (v - lo) / (hi - lo) * (hi_px - lo_px)), lo, hi


def _money(v: float) -> str:
    """A net profit short enough for an axis tick.

    Args:
        v: Dollars.

    Returns:
        Thousands with a k, sign always shown, because the sign is the whole story here.
    """
    return f"{v/1000:+.0f}k" if abs(v) >= 1000 else f"{v:+.0f}"


def scatter(kept: pd.DataFrame, found: dict, said: dict, title: str, cols: dict) -> str:
    """In-sample net profit against out-of-sample net profit, one mark per tuple.

    Args:
        kept: The usable points.
        found: What `measure.correlation` returned.
        said: What `measure.verdict` returned.
        title: Strategy name.
        cols: What `measure.correlation.columns` returned — which segments are the two
            axes. The labels say so on the figure, because the same batch is read two
            ways and a chart that does not name its split is unreadable a week later.

    Returns:
        An SVG element. The two rules at zero are what the eye should find first: a point
        in the upper-right made money in both samples, one in the lower-right made money
        in-sample and lost it out-of-sample, and a cloud that fills all four quadrants is
        a surface where in-sample profit carries no information about the future.
    """
    IS, OOS = cols["is"], cols["oos"]
    x, lo_x, hi_x = _scale(kept[IS].to_numpy(), PAD["l"], W - PAD["r"])
    y, lo_y, hi_y = _scale(kept[OOS].to_numpy(), H - PAD["b"], PAD["t"])
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="Inter, system-ui, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#fff"/>',
           f'<text x="{PAD["l"]}" y="38" font-size="21" font-weight="600" fill="{INK}">'
           f'{title} — walk forward correlation</text>',
           f'<text x="{PAD["l"]}" y="62" font-size="14" fill="{MUTED}">'
           f'cada punto es una combinacion de parametros · eje X lo que gano en '
           f'{cols["is_label"]} · eje Y lo que gano en {cols["oos_label"]}</text>']

    for frac in (0, .25, .5, .75, 1):
        gx, gy = PAD["l"] + frac * (W - PAD["l"] - PAD["r"]), PAD["t"] + frac * (H - PAD["t"] - PAD["b"])
        out += [f'<line x1="{gx:.1f}" y1="{PAD["t"]}" x2="{gx:.1f}" y2="{H-PAD["b"]}" '
                f'stroke="{GRID}" stroke-width="1"/>',
                f'<line x1="{PAD["l"]}" y1="{gy:.1f}" x2="{W-PAD["r"]}" y2="{gy:.1f}" '
                f'stroke="{GRID}" stroke-width="1"/>',
                f'<text x="{gx:.1f}" y="{H-PAD["b"]+22}" font-size="13" fill="{MUTED}" '
                f'text-anchor="middle">{_money(lo_x + frac*(hi_x-lo_x))}</text>',
                f'<text x="{PAD["l"]-12}" y="{gy+5:.1f}" font-size="13" fill="{MUTED}" '
                f'text-anchor="end">{_money(hi_y - frac*(hi_y-lo_y))}</text>']

    # The two rules that split profit from loss. Everything else on the chart is relative;
    # these are the only absolute reference the reader has.
    if lo_x < 0 < hi_x:
        out.append(f'<line x1="{x(0):.1f}" y1="{PAD["t"]}" x2="{x(0):.1f}" y2="{H-PAD["b"]}" '
                   f'stroke="{INK}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    if lo_y < 0 < hi_y:
        out.append(f'<line x1="{PAD["l"]}" y1="{y(0):.1f}" x2="{W-PAD["r"]}" y2="{y(0):.1f}" '
                   f'stroke="{INK}" stroke-width="1.5" stroke-dasharray="5 4"/>')

    # Marks shrink and go translucent as the cloud fills, and the per-point labels stop
    # entirely: a chart of three hundred tuples each captioned with its id is a chart
    # nobody can read, and the ids are in the table underneath anyway.
    big = len(kept) > LABELS
    r, opacity = (4, 0.55) if big else (7, 0.85)
    for _, row in kept.iterrows():
        cx, cy = x(row[IS]), y(row[OOS])
        colour = HUE.get(row["stratum"], MUTED)
        # The origin is a square, so it stays findable in a crowd and in greyscale.
        out.append(
            f'<rect x="{cx-7:.1f}" y="{cy-7:.1f}" width="14" height="14" fill="{colour}" '
            f'stroke="#fff" stroke-width="2"/>'
            if row["stratum"] == "origin" else
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{colour}" '
            f'fill-opacity="{opacity}" stroke="#fff" stroke-width="{1 if big else 2}"/>')
        if not big:
            out.append(f'<text x="{cx:.1f}" y="{cy-13:.1f}" font-size="11" fill="{MUTED}" '
                       f'text-anchor="middle">{row["variant_id"]}</text>')

    for i, (name, colour) in enumerate(h for h in HUE.items() if h[0] in set(kept["stratum"])):
        lx = PAD["l"] + i * 150
        out += [f'<circle cx="{lx}" cy="{H-34}" r="6" fill="{colour}"/>',
                f'<text x="{lx+13}" y="{H-29}" font-size="13" fill="{INK}">{name}</text>']

    rho = found["rho"]
    lo, hi = found["ci95"]
    out += [f'<text x="{W-PAD["r"]}" y="38" font-size="19" font-weight="600" '
            f'fill="{INK}" text-anchor="end">rho {rho:.2f}</text>',
            f'<text x="{W-PAD["r"]}" y="60" font-size="13" fill="{MUTED}" text-anchor="end">'
            f'IC 95% [{lo:.2f}, {hi:.2f}] · n={found["n"]} · {said["call"]}</text>',
            "</svg>"]
    return "\n".join(out)
