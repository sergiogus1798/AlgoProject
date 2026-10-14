"""The scatter block: points by group, the quadrants through zero and the fitted line if any."""

from typing import Any
import random
from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import axis, chart
from ui.desktop.blocks.card import card
from ui.desktop.blocks.states import SERIES
from ui.desktop.theme import T


MOST = 400  # points drawn; the fit and r in the block were computed on all of them


def _sample(b: dict) -> dict[str, Any]:
    """The block with at most MOST points (seeded, so a redraw shows the same ones); the axes
    keep the range of all of them."""
    pts = b["points"]
    xs, ys = [p["x"] for p in pts], [p["y"] for p in pts]
    kept = pts if len(pts) <= MOST else random.Random(0).sample(pts, MOST)
    return {
        **b,
        "points": kept,
        "n_all": len(pts),
        "span": ((min(xs), max(xs)), (min(ys), max(ys))),
    }


def _maps(
    b: dict, box: QRectF
) -> tuple[Callable, Callable, tuple[float, float], tuple[float, float]]:
    """The two data-to-pixel maps and the two data ranges."""
    sx, sy = b["span"]
    return (
        axis.scale(sx[0], sx[1], box.left(), box.right()),
        axis.scale(sy[0], sy[1], box.bottom(), box.top()),
        sx,
        sy,
    )


def _groups(b: dict) -> list[str]:
    """The groups in a fixed order, so a colour follows its group."""
    return sorted({p["group"] for p in b["points"]})


def _draw(b: dict) -> Callable:
    """The painter of one scatter."""
    groups = _groups(b)

    def draw(p: QPainter, rect: QRectF, hover: QPointF | None) -> None:
        """Paint into the canvas; `hover` is the pointer, for a guide line."""
        box = chart.area(rect)
        x, y, sx, sy = _maps(b, box)
        chart.axes(
            p,
            box,
            [(x(v), chart.num(v)) for v in axis.ticks(*sx)],
            [(y(v), chart.num(v)) for v in axis.ticks(sy[0], sy[1], 5)],
        )
        chart.titles(p, box, rect, b["x_label"], b["y_label"])
        if b["quadrants"]:
            p.setPen(QPen(QColor(T["muted"]), 1.2))
            if sx[0] < 0 < sx[1]:
                p.drawLine(QPointF(x(0), box.top()), QPointF(x(0), box.bottom()))
            if sy[0] < 0 < sy[1]:
                p.drawLine(QPointF(box.left(), y(0)), QPointF(box.right(), y(0)))
        p.setPen(QPen(QColor(T["bg"]), 1.5))
        for pt in b["points"]:
            p.setBrush(QColor(SERIES[groups.index(pt["group"]) % len(SERIES)]))
            p.drawEllipse(QPointF(x(pt["x"]), y(pt["y"])), 5, 5)
        if b["fit"]:
            f = b["fit"]
            p.setPen(QPen(QColor(T["text"]), 1.5, Qt.PenStyle.DashLine))
            p.drawLine(
                QPointF(x(sx[0]), y(f["intercept"] + f["slope"] * sx[0])),
                QPointF(x(sx[1]), y(f["intercept"] + f["slope"] * sx[1])),
            )

    return draw


def _tip(b: dict) -> Callable:
    """The point nearest the pointer, within a few pixels."""

    def tip(pos: QPointF, rect: QRectF) -> str | None:
        """The sentence for what lies under `pos`, None over empty ground."""
        x, y, _, _ = _maps(b, chart.area(rect))

        def gap(p: dict) -> float:
            """Squared pixel distance from the pointer to a point."""
            return (x(p["x"]) - pos.x()) ** 2 + (y(p["y"]) - pos.y()) ** 2

        near = min(b["points"], key=gap)
        if gap(near) > 64:
            return None
        return (
            f"{near['label']} · {near['group']}\n{b['x_label']}: {chart.num(near['x'])}\n"
            f"{b['y_label']}: {chart.num(near['y'])}"
        )

    return tip


def widget(block: dict) -> QWidget:
    """One scatter, drawn and explained.

    Args:
        block: A contract `scatter` block.

    Returns:
        The framed chart and its key.
    """
    b = _sample(block)
    items = [("box", SERIES[i % len(SERIES)], g) for i, g in enumerate(_groups(b))]
    if b["fit"]:
        f = b["fit"]
        # The WFC's line is Spearman's (a coefficient from -1 to 1, never a percentage), not a fit.
        rank = "Spearman" in (b.get("note") or "")
        items.append(
            (
                "dash",
                T["text"],
                f"recta de Spearman, pendiente {chart.num(f['slope'])}, "
                f"ρ = {f['r']:.3f}"
                if rank
                else f"recta ajustada, pendiente {chart.num(f['slope'])}, "
                f"r = {f['r']:.3f}",
            )
        )
    if b["n_all"] > MOST:
        items.append(
            (
                "box",
                T["faint"],
                f"muestra de {MOST} de {b['n_all']} puntos"
                + ("; la recta usa los " + str(b["n_all"]) if b["fit"] else ""),
            )
        )
    return card(b, chart.Canvas(_draw(b), _tip(b)), chart.key(items))
