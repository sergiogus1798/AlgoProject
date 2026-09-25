"""The two drawings over two axes: the heat grid and the scatter."""

from html import escape

import numpy as np

from core.study.render import svg
from core.study.render.svg import H, PAD, REAL, SIM, W

# Discrete steps, as the owner wants them: never a continuous ramp. Diverging runs cold to
# warm through a neutral middle; sequential runs light to dark in one hue.
DIVERGING = ("#2166ac", "#4393c3", "#92c5de", "#d1e5f0", "#f7f7f7",
             "#fddbc7", "#f4a582", "#d6604d", "#b2182b")
SEQUENTIAL = ("#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6",
              "#4292c6", "#2171b5", "#08519c", "#08306b")
DARK = {"#2166ac", "#b2182b", "#d6604d", "#2171b5", "#08519c", "#08306b", "#4292c6"}


def _levels(b: dict) -> list[float]:
    """The cut points of the colour scale: the block's own, or nine even steps of its range."""
    if b["levels"]:
        return b["levels"]
    v = np.array([c for r in b["values"] for c in r if c is not None], dtype=float)
    if b["scale"] == "diverging":
        top = float(np.percentile(np.abs(v), 95)) or 1.0
        return list(np.linspace(-top, top, len(DIVERGING) + 1)[1:-1])
    return list(np.linspace(v.min(), v.max(), len(SEQUENTIAL) + 1)[1:-1])


def grid(b: dict) -> str:
    """One cell per (row, col), filled by its step on a discrete scale, its label written in."""
    rows, cols = b["rows"], b["cols"]
    cut = _levels(b)
    colours = DIVERGING if b["scale"] == "diverging" else SEQUENTIAL
    left, top = 150, 40
    cw = (W - left - PAD["r"]) / max(len(cols), 1)
    ch = 26
    body = [f'<text class="tick" x="{left + (j + .5) * cw:.1f}" y="{top - 8}" '
            f'text-anchor="middle">{escape(str(c))}</text>' for j, c in enumerate(cols)]
    for i, r in enumerate(rows):
        y = top + i * ch
        body.append(f'<text class="tick" x="{left - 8}" y="{y + 17}" text-anchor="end">'
                    f"{escape(str(r))}</text>")
        for j, v in enumerate(b["values"][i]):
            fill = "var(--card)" if v is None else colours[int(np.searchsorted(cut, v))]
            text = (b["labels"][i][j] if b["labels"] else svg.num(v))
            ink = "cell dark" if fill in DARK else "cell"
            body.append(f'<rect x="{left + j * cw:.1f}" y="{y}" width="{cw - 1:.1f}" '
                        f'height="{ch - 1}" fill="{fill}"/><text class="{ink}" '
                        f'x="{left + (j + .5) * cw:.1f}" y="{y + 17}" text-anchor="middle">'
                        f"{escape(str(text))}</text>")
    height = top + ch * len(rows) + 12
    bounds = ["<"] + [svg.num(c) for c in cut]
    key = svg.legend([(svg.box(c), f"{a}") for c, a in zip(colours, bounds)])
    return svg.figure(b["title"], b.get("note", ""), svg.canvas("".join(body), height), key)


def scatter(b: dict) -> str:
    """Points by group, the fitted line if any, and the quadrants through zero if asked."""
    pts = b["points"]
    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts]
    x = svg.scale(min(xs), max(xs), PAD["l"], W - PAD["r"])
    y = svg.scale(min(ys), max(ys), H - PAD["b"], PAD["t"])
    body = [svg.axes(x, y, svg.ticks(min(xs), max(xs)), svg.ticks(min(ys), max(ys)))]
    if b["quadrants"]:
        if min(xs) < 0 < max(xs):
            body.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{PAD["t"]}" '
                        f'y2="{H - PAD["b"]}" stroke="var(--ink)"/>')
        if min(ys) < 0 < max(ys):
            body.append(f'<line x1="{PAD["l"]}" x2="{W - PAD["r"]}" y1="{y(0):.1f}" '
                        f'y2="{y(0):.1f}" stroke="var(--ink)"/>')
    groups = sorted({p["group"] for p in pts})
    palette = [SIM, REAL, "var(--good)", "var(--bad)", "var(--watch)"]
    for p in pts:
        c = palette[groups.index(p["group"]) % len(palette)]
        body.append(f'<circle cx="{x(p["x"]):.1f}" cy="{y(p["y"]):.1f}" r="2.6" fill="{c}" '
                    f'opacity=".7"><title>{escape(p["label"])}</title></circle>')
    if b["fit"]:
        f = b["fit"]
        a, z = min(xs), max(xs)
        body.append(f'<line x1="{x(a):.1f}" y1="{y(f["intercept"] + f["slope"] * a):.1f}" '
                    f'x2="{x(z):.1f}" y2="{y(f["intercept"] + f["slope"] * z):.1f}" '
                    f'stroke="var(--ink)" stroke-dasharray="5 4"/>')
    body.append(f'<text class="tick" x="{W / 2}" y="{H - 6}" text-anchor="middle">'
                f'{escape(b["x_label"])}</text><text class="tick" x="14" y="{H / 2}" '
                f'transform="rotate(-90 14 {H / 2})" text-anchor="middle">'
                f'{escape(b["y_label"])}</text>')
    key = svg.legend([(svg.box(palette[i % len(palette)]), g) for i, g in enumerate(groups)]
                     + ([(svg.line("var(--ink)", "dashed"), f"r = {b['fit']['r']:.3f}")]
                        if b["fit"] else []))
    return svg.figure(b["title"], b.get("note", ""), svg.canvas("".join(body)), key)
