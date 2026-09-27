"""Which widget draws which block kind, and the one call every view makes to draw a block."""

import traceback
from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from ui.desktop.blocks import bars, cone, distribution, grid, lines, scatter, table, verdict
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour

# One widget per contract kind (core/study/CONTRACT.md §2). A ninth kind is a new module here.
WIDGETS: dict[str, Callable[[dict], QWidget]] = {
    "distribution": distribution.widget, "cone": cone.widget, "grid": grid.widget,
    "scatter": scatter.widget, "bars": bars.widget, "lines": lines.widget,
    "table": table.widget, "verdict": verdict.widget}


def draw(block: dict) -> QWidget:
    """The widget for one block, or a red line saying why there is none.

    Args:
        block: A contract block.

    Returns:
        Its widget. An unknown kind or a block that does not draw becomes a visible red
        label rather than an exception: this is the ui boundary, and one bad block must
        not take the whole study page down with it.
    """
    kind = block.get("kind")
    if kind not in WIDGETS:
        return text(f"Bloque de tipo desconocido «{kind}» ({block.get('title', 'sin título')}): "
                    "la ventana no sabe dibujarlo.", colour("fail"), 14, True)
    try:
        return WIDGETS[kind](block)
    except Exception as e:  # noqa: BLE001 — the boundary: shown, never swallowed
        traceback.print_exc()
        return text(f"No se pudo dibujar «{block.get('title', kind)}» ({kind}): "
                    f"{type(e).__name__}: {e}", colour("fail"), 14, True)
