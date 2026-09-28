"""The top of a result: its verdict, the line saying when and under what it was computed, the stale banner."""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.desktop.blocks import chart, verdict
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.theme import T


def stamp(result: dict) -> str:
    """The line saying what was computed, when, under which configuration and how fast."""
    parts = [result.get("strategy") or "población", f"calculado {result.get('computed_at', '—')}",
             f"config {result.get('config_hash', '—')}"]
    if result.get("wall_s") is not None:
        parts.append(f"{chart.num(result['wall_s'])} s")
    return " · ".join(parts)


def head(result: dict, title: str | None) -> QWidget:
    """One side's header: its title in a comparison, its verdict and its stamp."""
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    if title:
        lay.addWidget(text(title, T["text"], 17, True))
    if result.get("verdict"):
        lay.addWidget(verdict.widget(result["verdict"]))
    elif result.get("only"):
        lay.addWidget(text("Sin veredicto: el veredicto sale del análisis entero, no de una "
                           f"subprueba («{result['only']}») corrida sola.", T["muted"], 14))
    else:
        lay.addWidget(text("Este estudio describe y no juzga: no hay veredicto.", T["muted"], 14))
    lay.addWidget(text(stamp(result), T["faint"], 12))
    return box


def stale(meta: dict) -> QWidget:
    """The red banner of a result computed under another configuration than the drawer's."""
    banner = text(f"CADUCADO — este resultado se calculó con la configuración "
                  f"{meta.get('config_hash', '—')} y la de ahora firma "
                  f"{meta.get('current_hash', '—')}. Responde a otra pregunta: vuelve a "
                  f"correrlo antes de leerlo como respuesta.", colour("fail"), 14, True)
    banner.setStyleSheet(banner.styleSheet() + f" border: 2px solid {colour('fail')}; "
                         "padding: 8px;")
    return banner
