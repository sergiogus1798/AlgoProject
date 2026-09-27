"""The verdict block: the label in its state's colour, never alone, with its meaning and its parts."""

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop.blocks import chart
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour, label
from ui.desktop.theme import T

PER_ROW = 4


def _part(p: dict) -> QLabel:
    """One part of the verdict as a tile: its name, its state word and its value."""
    c = colour(p["state"])
    value = p.get("value")
    figure = label(p["state"]) if value is None else (
        f'{chart.num(value)}</span>&nbsp;<span style="color:{c}; font-size:12px;">'
        f'{label(p["state"])}')
    tile = QLabel(f'<span style="color:{T["text"]}; font-size:13px;">{p["label"]}</span><br>'
                  f'<span style="color:{c}; font-size:18px; font-weight:700;">{figure}</span>')
    tile.setStyleSheet(f"border-left: 4px solid {c}; padding: 4px 10px; "
                       f"font-family: {chart.FACE};")
    tip = f"{p['label']}: {label(p['state'])}"
    if p.get("value") is not None:
        tip += f", valor {chart.num(p['value'])}"
    tile.setToolTip(tip + (f"\n{p['note']}" if p.get("note") else ""))
    return tile


def widget(block: dict) -> QWidget:
    """The verdict: what the study decided, what that means and what it was built from.

    Args:
        block: A contract `verdict` block.

    Returns:
        The header; the label always sits beside its meaning, because a word without it
        is a word the owner has to go and look up.
    """
    b = block
    c = colour(b["state"])
    frame = QFrame()
    frame.setObjectName("verdict")
    frame.setStyleSheet(f"QFrame#verdict {{ border-left: 6px solid {c}; }}")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 8, 8, 8)
    score = "" if b.get("score") is None else (
        f'&nbsp;&nbsp;<span style="color:{T["muted"]}; font-size:16px;">nota '
        f'{chart.num(b["score"])}</span>')
    head = QLabel(f'<span style="color:{c}; font-size:26px; font-weight:800;">{b["label"]}'
                  f'</span>&nbsp;&nbsp;<span style="color:{c}; font-size:14px;">'
                  f'{label(b["state"])}</span>{score}')
    head.setStyleSheet(f"font-family: {chart.FACE};")
    head.setToolTip(f"estado del veredicto: {label(b['state'])}")
    lay.addWidget(head)
    lay.addWidget(text(b["meaning"], T["text"], 14))
    grid = QGridLayout()
    grid.setHorizontalSpacing(10)
    for k, p in enumerate(b.get("parts") or []):
        grid.addWidget(_part(p), k // PER_ROW, k % PER_ROW)
    lay.addLayout(grid)
    return frame
