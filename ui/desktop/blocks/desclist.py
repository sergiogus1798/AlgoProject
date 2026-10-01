"""The list block: a title in bold and a short description under it, one item after another."""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.desktop.blocks.card import card, text
from ui.desktop.theme import T


def widget(block: dict) -> QWidget:
    """A description list, e.g. «¿Qué hace cada modelo?» (§1.10): one entry per model, its
    name in bold and one line under it, no table and no extra column.

    Args:
        block: `{"kind": "list", "title": str, "note": str, "items": [{"title", "text"}, ...]}`.

    Returns:
        The framed list.
    """
    b = block
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)
    for item in b["items"]:
        lay.addWidget(text(f"<b>{item['title']}</b><br>{item['text']}", T["text"], 13))
    return card(b, box)
