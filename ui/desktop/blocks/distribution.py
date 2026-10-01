"""The distribution block: the null's histogram, its band, its median and the real value marked — or several samples as densities."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from ui.desktop.blocks import axis, chart, density
from ui.desktop.blocks.card import card, text
from ui.desktop.blocks.states import MEDIAN, REAL, SIM
from ui.text.numbers import num
from ui.desktop.theme import T


def _span(b: dict) -> tuple[float, float]:
    """The x range: the bins, stretched to reach a real value or band that falls outside."""
    marks = [v for v in (b["real"], b["median"], *b["band"]) if v is not None]
    return min(b["bins"][0], *marks), max(b["bins"][-1], *marks)


def _draw(b: dict) -> Callable:
    """The painter of one distribution."""
    edges, counts = b["bins"], b["counts"]
    top = max(counts) or 1

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        box = chart.area(rect)
        x = axis.scale(*_span(b), box.left(), box.right())
        y = axis.scale(0, top * 1.08, box.bottom(), box.top())
        lo, hi = b["band"]
        if lo is not None and hi is not None:
            band = QColor(SIM)
            band.setAlphaF(0.16)
            p.fillRect(QRectF(x(lo), box.top(), x(hi) - x(lo), box.height()), band)
        chart.axes(p, box, [(x(v), chart.num(v)) for v in axis.ticks(*_span(b))],
                   [(y(v), chart.num(v)) for v in axis.ticks(0, top * 1.08, 4)])
        fill = QColor(SIM)
        fill.setAlphaF(0.85)
        for a, z, c in zip(edges, edges[1:], counts):
            if c:
                p.fillRect(QRectF(x(a) + 0.5, y(c), max(x(z) - x(a) - 1, 1.5), y(0) - y(c)), fill)
        chart.vline(p, x(b["median"]), box, MEDIAN, 1.5, Qt.DashLine)
        if b["real"] is not None:
            xr = x(b["real"])
            chart.vline(p, xr, box, REAL, 3)
            label = f"{b.get('mark') or 'Real'} {chart.num(b['real'])}"
            p.setFont(chart.font(11, True))
            w = p.fontMetrics().horizontalAdvance(label) + 10
            left = xr + 6 if xr + 6 + w < box.right() else xr - 6 - w
            p.fillRect(QRectF(left, box.top() + 2, w, 20), QColor(T["bg"]))
            p.setPen(QColor(REAL))
            p.drawText(QRectF(left, box.top() + 2, w, 20), Qt.AlignCenter, label)

    return draw


def _tip(b: dict) -> Callable:
    """The sentence for the bin or the line under the pointer."""
    edges, counts = b["bins"], b["counts"]
    total = sum(counts) or 1

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        box = chart.area(rect)
        x = axis.scale(*_span(b), box.left(), box.right())
        if b["real"] is not None and abs(pos.x() - x(b["real"])) < 5:
            return f"{b.get('mark') or 'valor real'}: {chart.num(b['real'], b['unit'])}"
        if abs(pos.x() - x(b["median"])) < 5:
            return f"mediana de la distribución: {chart.num(b['median'], b['unit'])}"
        for a, z, c in zip(edges, edges[1:], counts):
            if x(a) <= pos.x() < x(z):
                return (f"de {chart.num(a, b['unit'])} a {chart.num(z, b['unit'])}\n{c} casos "
                        f"({100 * c / total:.1f} %)")
        return None

    return tip


def _percentiles(b: dict) -> QTableWidget:
    """The percentile row under the chart, the bracket that holds the real value outlined.
    With `row_unit` the heads read «1%», «10%»… and every cell carries that unit."""
    keys = sorted(b["percentiles"], key=float)       # JSON may hand them back as text-sorted
    vals = [b["percentiles"][k] for k in keys]
    unit = f" {b['row_unit']}" if b.get("row_unit") else ""
    table = QTableWidget(1, len(keys))
    table.setHorizontalHeaderLabels([f"{k}%" if unit else f"p{k}" for k in keys])
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.NoSelection)    # a click only recoloured the cell
    table.setFocusPolicy(Qt.NoFocus)
    real = b["real"]
    for j, (k, v) in enumerate(zip(keys, vals)):
        # Whole units past 10 with a unit on each cell, or «-641.7 $» no longer fits.
        item = QTableWidgetItem(chart.num(round(v) if unit and abs(v) >= 10 else v) + unit)
        item.setTextAlignment(Qt.AlignCenter)
        item.setToolTip(f"el {k} % de la distribución queda por debajo de {chart.num(v)}")
        nxt = vals[j + 1] if j + 1 < len(vals) else None
        if real is not None and v <= real and (nxt is None or real < nxt):
            item.setForeground(QColor(REAL))
            item.setBackground(QColor(T["select"]))
            item.setToolTip(item.toolTip() + f"\nel valor real ({chart.num(real)}) cae aquí")
        table.setItem(0, j, item)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.setFixedHeight(table.horizontalHeader().height() + table.rowHeight(0) + 4)
    return table


def widget(block: dict) -> QWidget:
    """One distribution, drawn and explained.

    Args:
        block: A contract `distribution` block.

    Returns:
        The framed chart, its key, the headline figures and the percentile row; with
        `series`, the samples overlaid as densities (`density.widget`) over the same row.
    """
    b = block
    if b.get("series"):
        return density.widget(b, _percentiles(b))
    lo, hi = b["band"]
    mark = b.get("mark") or "Real"
    p = "" if b["p"] is None else f" · p = {num(b['p'], 'p')}"
    key = chart.key([("box", SIM, "distribución"), ("box", chart.blend(SIM, 0.3), "banda"),
                     ("dash", MEDIAN, "mediana"), ("line", REAL, mark)])
    # Real, median and band are already in the key and the chart: only p earns a line.
    head = text(p[3:], T["text"], 14) if p else None
    parts = [head] if head else []
    return card(b, *parts, chart.Canvas(_draw(b), _tip(b)), key, _percentiles(b))
