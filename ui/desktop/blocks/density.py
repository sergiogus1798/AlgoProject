"""A distribution with several samples: each one a density on the same bins, a toggle per sample, the shift beside."""

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout, QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card, text
from ui.desktop.blocks.states import REAL, SERIES
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import T


def _span(b: dict) -> tuple[float, float]:
    """The x range: the bins, stretched to reach a real value that falls outside."""
    marks = [v for v in (b["real"], *(s["median"] for s in b["series"]),
                        *(s.get("real") for s in b["series"])) if v is not None]
    return min(b["bins"][0], *marks), max(b["bins"][-1], *marks)


def _draw(b: dict, hidden: set[int]) -> Callable:
    """The painter: each visible sample as a filled step outline, its median dashed in its colour."""
    edges = b["bins"]
    top = max(c for s in b["series"] for c in s["counts"]) or 1

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, unused."""
        box = chart.area(rect)
        x = axis.scale(*_span(b), box.left(), box.right())
        y = axis.scale(0, top * 1.08, box.bottom(), box.top())
        chart.axes(p, box, [(x(v), chart.num(v)) for v in axis.ticks(*_span(b))],
                   [(y(v), chart.num(v)) for v in axis.ticks(0, top * 1.08, 4)])
        for k, s in enumerate(b["series"]):
            if k in hidden:
                continue
            colour = QColor(SERIES[k % len(SERIES)])
            path = QPainterPath(QPointF(x(edges[0]), y(0)))
            for a, z, c in zip(edges, edges[1:], s["counts"]):
                path.lineTo(x(a), y(c))
                path.lineTo(x(z), y(c))
            path.lineTo(x(edges[-1]), y(0))
            fill = QColor(colour)
            fill.setAlphaF(0.22)
            p.fillPath(path, fill)
            p.setPen(QPen(colour, 2.5))
            p.drawPath(path)
            chart.vline(p, x(s["median"]), box, colour.name(), 1.5, Qt.DashLine)
            if s.get("real") is not None:
                chart.vline(p, x(s["real"]), box, colour.name(), 3)
        if b["real"] is not None:
            chart.vline(p, x(b["real"]), box, REAL, 3)

    return draw


def _tip(b: dict, hidden: set[int]) -> Callable:
    """Under the pointer: the bin, and each visible sample's density and share there."""
    edges = b["bins"]

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        box = chart.area(rect)
        x = axis.scale(*_span(b), box.left(), box.right())
        for k, s in enumerate(b["series"]):
            if k in hidden:
                continue
            if s.get("real") is not None and abs(pos.x() - x(s["real"])) < 5:
                return f"real de {s['label']}: {chart.num(s['real'], b['unit'])}"
            if abs(pos.x() - x(s["median"])) < 5:
                return f"mediana de {s['label']}: {chart.num(s['median'], b['unit'])}"
        for i, (a, z) in enumerate(zip(edges, edges[1:])):
            if x(a) <= pos.x() < x(z):
                rows = [f"{s['label']}: densidad {chart.num(s['counts'][i])} · "
                        f"{num(100 * s['counts'][i] * (z - a))} % de sus operaciones"
                        for k, s in enumerate(b["series"]) if k not in hidden]
                return "\n".join([f"de {chart.num(a, b['unit'])} a {chart.num(z, b['unit'])}", *rows])
        return None

    return tip


def _side(b: dict) -> QWidget:
    """Beside the plot: each sample's n and median, then the median shift and the KS p."""
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(12, 0, 0, 0)
    for k, s in enumerate(b["series"]):
        real = f" · real {chart.num(s['real'], b['unit'])}" if s.get("real") is not None else ""
        lay.addWidget(text(f'<span style="color:{SERIES[k % len(SERIES)]}">■</span> '
                           f"<b>{s['label']}</b><br>n {num(s['n'])} · mediana "
                           f"{chart.num(s['median'], b['unit'])}{real}", T["text"], 13))
    shift = b.get("shift")
    if shift:
        first, last = b["series"][0]["label"], b["series"][-1]["label"]
        move = text(f"{label('density.shift')}<br><b>{chart.num(shift['median'], b['unit'])}</b> "
                    f"({last} − {first})", T["text"], 14)
        move.setToolTip("Cuánto se movió la operación típica de una muestra a la otra, en la "
                        "unidad del gráfico.")
        ks = text(f"{label('density.ks')}<br><b>{num(shift['ks_p'], 'p')}</b>", T["text"], 14)
        ks.setToolTip("Prueba de Kolmogorov-Smirnov de dos muestras: la probabilidad de ver una "
                      "diferencia de forma así de grande si las dos muestras vinieran de la misma "
                      "distribución. Pequeño = las operaciones cambiaron de verdad.")
        lay.addWidget(move)
        lay.addWidget(ks)
    lay.addStretch(1)
    box.setFixedWidth(250)
    return box


def widget(b: dict, percentiles: QWidget) -> QWidget:
    """Several samples of one per-trade metric, overlaid as densities.

    Args:
        b: A contract `distribution` block with `series` (CONTRACT §2, encargo 24 E3).
        percentiles: The percentile row of the union, drawn under the plot as the base drawing.

    Returns:
        The framed plot with a toggle per sample, the shift beside it and the percentiles under.
    """
    hidden: set[int] = set()
    canvas = chart.Canvas(_draw(b, hidden), _tip(b, hidden))

    def flip(k: int, on: bool) -> None:
        """Show or hide sample `k` and repaint."""
        (hidden.discard if on else hidden.add)(k)
        canvas.update()

    toggles = QHBoxLayout()
    toggles.addWidget(text(label("density.show"), T["muted"], 12))
    for k, s in enumerate(b["series"]):
        box = QCheckBox(f"{s['label']} (n {num(s['n'])})")
        box.setChecked(True)
        box.setStyleSheet(f"color:{SERIES[k % len(SERIES)]}; font-weight:700;")
        box.setToolTip("Enseña u oculta esta muestra. Cada una está normalizada como densidad "
                       "(su área vale 1): muestras de distinta longitud se comparan por su forma.")
        box.toggled.connect(lambda on, k=k: flip(k, on))
        toggles.addWidget(box)
    toggles.addStretch(1)
    row = QWidget()
    across = QHBoxLayout(row)
    across.setContentsMargins(0, 0, 0, 0)
    across.addWidget(canvas, 1)
    across.addWidget(_side(b))
    bar = QWidget()
    bar.setLayout(toggles)
    under = text(label("density.union"), T["muted"], 12)
    return card(b, bar, row, under, percentiles)
