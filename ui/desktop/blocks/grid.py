"""The grid block: a heat map on a discrete scale, every cell labelled, θ₀ marked, the scale's key beneath."""

from bisect import bisect_right
from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import chart
from ui.desktop.blocks.card import card, text
from ui.desktop.blocks.states import DIVERGING, REAL, SEQUENTIAL
from ui.text.glossary import label
from ui.desktop.theme import T

HEAD = 30


def levels(b: dict) -> list[float]:
    """The cut points of the colour scale: the block's own, or eight even steps of its range.

    Args:
        b: A grid block.

    Returns:
        Ascending cuts; n cuts make n + 1 colours. With `scale_range` the eight steps span
        that shared extent, so several grids read on one scale. A diverging scale without
        either is made symmetric around zero on the 95th percentile of |value|, so one outlier
        does not wash every other cell into the middle colour.
    """
    if b["levels"]:
        return b["levels"]
    if b.get("scale_range"):
        lo, hi = b["scale_range"]
        return [lo + (hi - lo) * i / 9 for i in range(1, 9)]
    v = sorted(c for r in b["values"] for c in r if c is not None)
    if b["scale"] == "diverging":
        mags = sorted(abs(c) for c in v)
        top = mags[int(0.95 * (len(mags) - 1))] or 1.0
        return [-top + 2 * top * i / 9 for i in range(1, 9)]
    return [v[0] + (v[-1] - v[0]) * i / 9 for i in range(1, 9)]


def palette(b: dict) -> list[str]:
    """One colour per step of the scale, sampled evenly from the nine-step ramp.

    Args:
        b: A grid block.

    Returns:
        len(levels) + 1 hex colours.
    """
    ramp = DIVERGING if b["scale"] == "diverging" else SEQUENTIAL
    n = len(levels(b)) + 1
    return [ramp[round(i * (len(ramp) - 1) / max(n - 1, 1))] for i in range(n)]


def _ink(fill: str) -> str:
    """Black or white text, whichever reads on the cell's fill."""
    c = QColor(fill)
    return "#000000" if 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue() > 140 else "#ffffff"


def _geometry(b: dict, rect: QRectF) -> tuple[float, float, float]:
    """The row-label column's width, the cell width and the cell height."""
    left = min(340, 20 + max(QFontMetrics(chart.font(11, True)).horizontalAdvance(str(r))
                             for r in b["rows"]))
    cw = (rect.width() - left - 8) / len(b["cols"])
    ch = (rect.height() - HEAD) / len(b["rows"])
    return left, cw, ch


def _draw(b: dict) -> Callable:
    """The painter of one grid."""
    cuts, colours = levels(b), palette(b)

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        left, cw, ch = _geometry(b, rect)
        p.setFont(chart.font(11, True))
        p.setPen(QColor(T["text"]))
        for j, c in enumerate(b["cols"]):
            p.drawText(QRectF(left + j * cw, 0, cw, HEAD - 4), Qt.AlignCenter, str(c))
        for i, r in enumerate(b["rows"]):
            top = HEAD + i * ch
            p.setFont(chart.font(11, True))
            p.setPen(QColor(T["text"]))
            p.drawText(QRectF(0, top, left - 10, ch), Qt.AlignRight | Qt.AlignVCenter, str(r))
            p.setFont(chart.font(11))
            for j, v in enumerate(b["values"][i]):
                cell = QRectF(left + j * cw + 1, top + 1, cw - 2, ch - 2)
                fill = T["rule"] if v is None else colours[bisect_right(cuts, v)]
                p.fillRect(cell, QColor(fill))
                p.setPen(QColor(T["faint"] if v is None else _ink(fill)))
                text = b["labels"][i][j] if b["labels"] else chart.num(v)
                # Three maps side by side leave ~30 px a cell: a figure that does not fit is
                # left to the hover sentence rather than cut into an unreadable stub.
                if b["labels"] or p.fontMetrics().horizontalAdvance(text) < cw - 6:
                    p.drawText(cell.adjusted(4, 0, -4, 0), Qt.AlignCenter | Qt.TextWordWrap, text)
        if b.get("region"):
            _region(p, b, left, cw, ch)
        if b.get("mark"):
            _mark(p, b, left, cw, ch)

    return draw


def _region(p: QPainter, b: dict, left: float, cw: float, ch: float) -> None:
    """A faint outline on every cell of `region` (2026-09-30, §8.5): a plateau box carried
    over from another surface. Never touches `values` or `labels` — only `mark` draws a tag."""
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(T["faint"]), 2))
    for cell in b["region"]:
        i, j = b["rows"].index(cell["row"]), b["cols"].index(cell["col"])
        p.drawRect(QRectF(left + j * cw, HEAD + i * ch, cw, ch).adjusted(1, 1, -1, -1))


def _mark(p: QPainter, b: dict, left: float, cw: float, ch: float) -> None:
    """The marked cell (θ₀, the mother's parameters) outlined in the real ink, its label on it."""
    m = b["mark"]
    i, j = b["rows"].index(m["row"]), b["cols"].index(m["col"])
    cell = QRectF(left + j * cw, HEAD + i * ch, cw, ch)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(T["bg"]), 5))
    p.drawRect(cell.adjusted(1, 1, -1, -1))
    p.setPen(QPen(QColor(REAL), 3))
    p.drawRect(cell.adjusted(1, 1, -1, -1))
    p.setFont(chart.font(10, True))
    tag = QRectF(cell.left() + 3, cell.top() + 2, p.fontMetrics().horizontalAdvance(m["label"]) + 6,
                 p.fontMetrics().height())
    p.fillRect(tag, QColor(T["bg"]))
    p.setPen(QColor(REAL))
    p.drawText(tag, Qt.AlignCenter, m["label"])


def _tip(b: dict) -> Callable:
    """The row, the column, the value and the label of the cell under the pointer."""

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        left, cw, ch = _geometry(b, rect)
        i, j = int((pos.y() - HEAD) // ch), int((pos.x() - left) // cw)
        if not (0 <= i < len(b["rows"]) and 0 <= j < len(b["cols"])) or pos.y() < HEAD:
            return None
        out = f"{b['rows'][i]} × {b['cols'][j]}\nvalor: {chart.num(b['values'][i][j])}"
        m = b.get("mark")
        if m and (m["row"], m["col"]) == (b["rows"][i], b["cols"][j]):
            out += f"\n{m['label']}: {label('grid.mark')}"
        if any((c["row"], c["col"]) == (b["rows"][i], b["cols"][j]) for c in b.get("region") or []):
            out += "\ndentro de la región marcada"
        return out + (f"\n{b['labels'][i][j]}" if b["labels"] else "")

    return tip


def _key(b: dict) -> QWidget:
    """The discrete scale: each colour beside the interval it paints."""
    cuts, colours = levels(b), palette(b)
    # Repeated cuts (a scale of three states written as eight cuts) paint empty steps: skipped.
    bounds = ([(True, f"< {chart.num(cuts[0])}")]
              + [(a < z, f"{chart.num(a)} … {chart.num(z)}") for a, z in zip(cuts, cuts[1:])]
              + [(True, f"≥ {chart.num(cuts[-1])}")])
    items = [("box", c, t) for c, (live, t) in zip(colours, bounds) if live]
    items.append(("box", T["rule"], label("grid.empty")))
    if b.get("mark"):
        items.append(("line", REAL, f"{b['mark']['label']} — {label('grid.mark')}"))
    if b.get("scale_range"):
        lo, hi = b["scale_range"]
        items.append(("box", T["faint"], f"{label('grid.shared')} {chart.num(lo)} … {chart.num(hi)}"))
    return chart.key(items)


def widget(block: dict) -> QWidget:
    """One heat map, drawn and explained.

    Args:
        block: A contract `grid` block.

    Returns:
        The framed map and its scale.
    """
    b = block
    # 🔬 2026-09-27: isOos on a build-only export wrote 21 rows and no column, and painting
    # it killed the whole window with a segfault — an empty map is said, never painted.
    if not b["rows"] or not b["cols"]:
        return card(b, text("(vacía: el estudio no dejó ninguna celda aquí)", T["faint"]))
    # Sized to its rows, not to the charts' 320 px: two rows stretched to 320 read as a
    # colour field, and blank rows under a short map read as missing data.
    row = max(36, min(72, (chart.HEIGHT - HEAD) // len(b["rows"])))
    height = HEAD + row * len(b["rows"])
    return card(b, chart.Canvas(_draw(b), _tip(b), height), _key(b))
