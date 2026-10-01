"""The callout block: one coloured sentence the study wants seen, not read past."""

from PySide6.QtWidgets import QWidget

from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour


def widget(block: dict) -> QWidget:
    """One highlighted sentence, e.g. «El 39,7 % de las simulaciones rindieron peor que el
    backtest real en Profit Factor» (§1.7).

    Args:
        block: `{"kind": "callout", "text": str, "state": str}`; `state` is one of the
            contract's five words and picks the border colour (`info` for a neutral fact).

    Returns:
        The framed sentence.
    """
    b = block
    c = colour(b.get("state") or "info")
    body = text(b["text"], c, 15, True)
    body.setStyleSheet(body.styleSheet() + f" border-left: 4px solid {c}; padding: 8px 12px;")
    return body
