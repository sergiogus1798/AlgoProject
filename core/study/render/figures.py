"""The four drawings over a continuous axis: distribution, cone, lines and bars."""

from collections.abc import Callable
from html import escape

from core.study.render import svg
from core.study.render.svg import H, PAD, REAL, SIM, STATE, W

ROLE = {"real": REAL, "sim": SIM, "reference": svg.INK2}


def _xfmt(labels: list) -> Callable:
    """Tick formatter for an x axis that is either positions or labels such as dates."""
    return lambda v: labels[min(int(round(v)), len(labels) - 1)]


def distribution(b: dict) -> str:
    """Histogram of the null, its band shaded, the median dashed and the real value marked."""
    edges, counts = b["bins"], b["counts"]
    x = svg.scale(edges[0], edges[-1], PAD["l"], W - PAD["r"])
    y = svg.scale(0, max(counts) or 1, H - PAD["b"], PAD["t"])
    lo, hi = b["band"]
    body = ([f'<rect x="{x(lo):.1f}" y="{PAD["t"]}" width="{x(hi) - x(lo):.1f}" '
             f'height="{H - PAD["b"] - PAD["t"]}" fill="{SIM}" opacity=".10"/>']
            if lo is not None else [])
    body += [f'<rect x="{x(a) + .5:.1f}" y="{y(c):.1f}" width="{max(x(z) - x(a) - 1, .5):.1f}" '
             f'height="{y(0) - y(c):.1f}" fill="{SIM}" opacity=".75"/>'
             for a, z, c in zip(edges, edges[1:], counts)]
    body.append(svg.axes(x, y, svg.ticks(edges[0], edges[-1]), svg.ticks(0, max(counts) or 1)))
    body.append(f'<line x1="{x(b["median"]):.1f}" x2="{x(b["median"]):.1f}" y1="{PAD["t"]}" '
                f'y2="{H - PAD["b"]}" stroke="{svg.INK2}" stroke-dasharray="4 3"/>')
    if b["real"] is not None:
        body.append(f'<line x1="{x(b["real"]):.1f}" x2="{x(b["real"]):.1f}" y1="{PAD["t"]}" '
                    f'y2="{H - PAD["b"]}" stroke="{REAL}" stroke-width="3"/>'
                    f'<text class="mark" x="{x(b["real"]) + 5:.1f}" y="{PAD["t"] + 12}">'
                    f'real {svg.num(b["real"])}</text>')
    p = "" if b["p"] is None else f" · p = {b['p']:.4f}"
    key = svg.legend([(svg.box(SIM, .75), "simuladas"), (svg.box(SIM, .2), "banda"),
                      (svg.line(svg.INK2, "dashed"), f"mediana {svg.num(b['median'])}"),
                      (svg.line(REAL), f"real{p}")])
    return svg.figure(b["title"], b["note"], svg.canvas("".join(body)), key)


def _path(xs: list[float], ys: list, x: Callable, y: Callable) -> str:
    """An SVG path through the points, broken where a value is missing."""
    out, pen = [], "M"
    for a, v in zip(xs, ys):
        if v is None:
            pen = "M"
            continue
        out.append(f"{pen}{x(a):.1f},{y(v):.1f}")
        pen = "L"
    return " ".join(out)


def cone(b: dict) -> str:
    """The simulated percentile bands as nested fills, the real curve drawn over them."""
    n = len(b["x"])
    xs = list(range(n))
    values = [v for band in b["bands"].values() for v in band if v is not None]
    values += [v for v in b["real"] if v is not None]
    x = svg.scale(0, max(n - 1, 1), PAD["l"], W - PAD["r"])
    y = svg.scale(min(values), max(values), H - PAD["b"], PAD["t"])
    body = []
    for lo, hi, alpha in (("2.5", "97.5", .15), ("25", "75", .3)):
        up, down = b["bands"][hi], b["bands"][lo]
        pts = [f"{x(i):.1f},{y(v):.1f}" for i, v in zip(xs, up) if v is not None]
        pts += [f"{x(i):.1f},{y(v):.1f}" for i, v in reversed(list(zip(xs, down))) if v is not None]
        body.append(f'<polygon points="{" ".join(pts)}" fill="{SIM}" opacity="{alpha}"/>')
    body.append(svg.axes(x, y, svg.ticks(0, n - 1), svg.ticks(min(values), max(values)),
                         _xfmt(b["x"])))
    body.append(f'<path d="{_path(xs, b["bands"]["50"], x, y)}" fill="none" stroke="{SIM}" '
                f'stroke-dasharray="4 3"/>')
    body.append(f'<path d="{_path(xs, b["real"], x, y)}" fill="none" stroke="{REAL}" '
                f'stroke-width="2.5"/>')
    if b["split"] in b["x"]:
        s = x(b["x"].index(b["split"]))
        body.append(f'<line x1="{s:.1f}" x2="{s:.1f}" y1="{PAD["t"]}" y2="{H - PAD["b"]}" '
                    f'stroke="{svg.INK2}" stroke-dasharray="2 4"/>')
    key = svg.legend([(svg.box(SIM, .15), "2,5–97,5 %"), (svg.box(SIM, .3), "25–75 %"),
                      (svg.line(SIM, "dashed"), "mediana"), (svg.line(REAL), "real")])
    return svg.figure(b["title"], b.get("note", ""), svg.canvas("".join(body)), key)


def lines(b: dict) -> str:
    """Several series over one x axis, each coloured by its role."""
    n = len(b["x"])
    xs = list(range(n))
    values = [v for s in b["series"] for v in s["values"] if v is not None]
    x = svg.scale(0, max(n - 1, 1), PAD["l"], W - PAD["r"])
    y = svg.scale(min(values), max(values), H - PAD["b"], PAD["t"])
    body = [svg.axes(x, y, svg.ticks(0, n - 1), svg.ticks(min(values), max(values)),
                     _xfmt(b["x"]))]
    dash = {"real": "", "sim": "", "reference": ' stroke-dasharray="5 4"'}
    for s in b["series"]:
        body.append(f'<path d="{_path(xs, s["values"], x, y)}" fill="none" '
                    f'stroke="{ROLE[s["role"]]}" stroke-width="2"{dash[s["role"]]} '
                    f'opacity="{1 if s["role"] == "real" else .7}"><title>{escape(s["label"])}'
                    f"</title></path>")
    key = svg.legend([(svg.line(ROLE[s["role"]], "dashed" if s["role"] == "reference"
                                else "solid"), s["label"]) for s in b["series"]][:12])
    return svg.figure(b["title"], b.get("note", ""), svg.canvas("".join(body)), key)


def bars(b: dict) -> str:
    """Horizontal bars, one per item, coloured by state, with error whiskers and a reference."""
    items = b["items"]
    row = 26
    height = PAD["t"] + PAD["b"] + row * len(items)
    ends = [i["value"] for i in items] + [e for i in items for e in (i.get("error") or [])]
    ends += [0.0] + ([b["reference"]] if b["reference"] is not None else [])
    ends = [v for v in ends if v is not None]
    left = PAD["l"] + 150
    x = svg.scale(min(ends), max(ends), left, W - PAD["r"])
    body = []
    for k, i in enumerate(items):
        top = PAD["t"] + k * row
        v = i["value"] if i["value"] is not None else 0.0
        a, z = sorted((x(0.0), x(v)))
        body.append(f'<text class="tick" x="{left - 8}" y="{top + 16}" text-anchor="end">'
                    f'{escape(i["label"])}</text><rect x="{a:.1f}" y="{top + 5}" '
                    f'width="{max(z - a, 1):.1f}" height="{row - 10}" '
                    f'fill="{STATE.get(i.get("state"), SIM)}" opacity=".85"/>'
                    f'<text class="tick" x="{z + 4:.1f}" y="{top + 16}">{svg.num(i["value"])}</text>')
        if i.get("error"):
            lo, hi = i["error"]
            body.append(f'<line x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="{top + row / 2:.1f}" '
                        f'y2="{top + row / 2:.1f}" stroke="var(--ink)" stroke-width="1.5"/>')
    if b["reference"] is not None:
        r = x(b["reference"])
        body.append(f'<line x1="{r:.1f}" x2="{r:.1f}" y1="{PAD["t"] - 4}" '
                    f'y2="{height - PAD["b"] + 4}" stroke="{REAL}" stroke-dasharray="4 3"/>')
    body += [f'<text class="tick" x="{x(v):.1f}" y="{height - PAD["b"] + 20}" '
             f'text-anchor="middle">{svg.num(v)}</text>' for v in svg.ticks(min(ends), max(ends))]
    return svg.figure(b["title"], b.get("note", ""), svg.canvas("".join(body), height))
