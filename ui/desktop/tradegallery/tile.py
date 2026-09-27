"""One tile of the gallery: the trade's price window and its figures, each with the sentence of what it counts."""

from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout

from ui.desktop.blocks import chart
from ui.desktop.blocks.card import text
from ui.desktop.tradegallery import price
from ui.desktop.theme import MONO, T


def _figures(t: dict) -> list[tuple[str, str, str]]:
    """(label, value, hover sentence) for every number a tile prints."""
    held = t["bars"].get("held")
    return [
        ("P&L", chart.num(t["pnl"]),
         "Beneficio o pérdida de la operación en dinero, tal como la exporta SQX (Profit/Loss)."),
        ("MAE", chart.num(t["mae"]),
         "Máxima excursión adversa: lo peor que llegó a ir la operación abierta, en dinero (MAE $)."),
        ("MFE", chart.num(t["mfe"]),
         "Máxima excursión favorable: lo mejor que llegó a ir la operación abierta, en dinero (MFE $)."),
        ("velas", "—" if held is None else str(held),
         "Velas del timeframe de la estrategia desde la vela de entrada hasta la de salida."),
        ("entrada", f"{t['open_price']}  {t['open_time']}",
         "Precio y hora de apertura de la operación (hora del feed, no UTC)."),
        ("salida", f"{t['close_price']}  {t['close_time']}",
         "Precio y hora de cierre de la operación (hora del feed, no UTC)."),
        ("cierre", t["close_type"], "Motivo de cierre tal como lo escribe SQX (Close type)."),
        ("tamaño", chart.num(t["size"]), "Lotes de la operación (Size)."),
    ]


def _numbers(t: dict) -> QFrame:
    """The figure column: label, value, hover sentence on both."""
    box = QFrame()
    grid = QGridLayout(box)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setVerticalSpacing(4)
    for r, (lab, val, why) in enumerate(_figures(t)):
        a, b = QLabel(lab), QLabel(val)
        a.setStyleSheet(f"color:{T['muted']}; font-family:{MONO}; font-size:12px;")
        size, weight = (20, 700) if lab == "P&L" else (13, 600)
        b.setStyleSheet(f"color:{T['text']}; font-family:{MONO}; font-size:{size}px;"
                        f" font-weight:{weight};")
        for w in (a, b):
            w.setToolTip(why)
        grid.addWidget(a, r, 0)
        grid.addWidget(b, r, 1)
    grid.setRowStretch(len(_figures(t)), 1)
    box.setFixedWidth(330)
    return box


def tile(t: dict) -> QFrame:
    """One trade drawn: its pick label on top, the price window left, the figures right.

    Args:
        t: One tile of `/api/tearsheet/trades`.

    Returns:
        The framed tile; a trade whose bars are missing says so where the chart would be.
    """
    frame = QFrame()
    frame.setObjectName("tile")
    frame.setStyleSheet(f"QFrame#tile {{ border-top: 1px solid {T['rule']}; }}")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(0, 10, 0, 10)
    head = text(f"{t['label']} · operación n.º {t['row'] + 1} · {t['type']}", T["text"], 14, True)
    head.setToolTip("Qué operación es: su posición en el reparto de P&L de la muestra "
                    "(o su orden entre las cinco al azar) y su número en la exportación.")
    lay.addWidget(head)
    body = QHBoxLayout()
    missing = t["bars"].get("missing")
    if missing:
        body.addWidget(text(missing, T["muted"], 13), 1)
    else:
        body.addWidget(price.canvas(t), 1)
    body.addWidget(_numbers(t))
    lay.addLayout(body)
    if not missing:
        lay.addWidget(chart.key([("box", T["faint"], "rango de cada vela"),
                                 ("line", price.REAL, "cierre"),
                                 ("box", price.ENTRY, "entrada"), ("box", price.EXIT, "salida"),
                                 ("box", chart.blend(price.ENTRY, 0.35), "tramo en mercado")]))
    return frame
