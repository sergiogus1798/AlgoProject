"""The frame every block sits in: its title, its explanation, then what it draws."""

import re

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ui.desktop.theme import T

# What `initial` leaves alone: the tags and punctuation before the first word, a first word
# that is a code (`oos1`, `p_5`, `ret.dd`), a unit, or a letter outside Latin (ρ, α, θ).
LEAD = re.compile(r"^((?:<[^>]*>|[^\w<])*)(\w[^\s<]*)(.*)$", re.S)
UNITS = {"p", "pips", "ms", "s", "h", "min", "px", "x", "vs"}
LATIN = re.compile(r"[a-záéíóúñü]")


def initial(body: object) -> str:
    """A label with a capital first letter, the owner's rule for every title, label, option,
    tab name and glossary term (§1 «mayúscula inicial»). Only that letter changes.

    Args:
        body: What a study or the window wrote; rich text is allowed.

    Returns:
        The same text, its first word capitalised unless that word is a code or a unit.
    """
    body = str(body)
    m = LEAD.match(body)
    if not m:
        return body
    lead, word, rest = m.groups()
    if (not LATIN.match(word[0]) or word.lower() in UNITS
            or re.search(r"[\d_.]", word.rstrip(".:,;"))):
        return body
    return lead + word[0].upper() + word[1:] + rest


def text(body: str, colour: str, size: int = 13, bold: bool = False) -> QLabel:
    """A wrapped paragraph in one of the terminal inks.

    Args:
        body: What it says; rich text is allowed.
        colour: Hex colour.
        size: Pixel size.
        bold: True for a title.

    Returns:
        The label.
    """
    label = QLabel(body)
    label.setWordWrap(True)
    label.setStyleSheet(f"color:{colour}; font-size:{size}px;"
                        + (" font-weight:700;" if bold else ""))
    return label


def card(block: dict, *parts: QWidget) -> QFrame:
    """One block, framed: the study's own title and note above whatever the kind draws.

    Args:
        block: The contract block; its `title` and `note` are shown as written, since the
            window invents no text (CONTRACT §2).
        parts: The widgets the kind builds, top to bottom.

    Returns:
        The framed block.
    """
    frame = QFrame()
    frame.setObjectName("block")
    frame.setStyleSheet(f"QFrame#block {{ border-top: 1px solid {T['rule']}; }}")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(0, 10, 0, 14)
    lay.setSpacing(6)
    if block.get("title"):
        title = text(initial(block["title"]), T["text"], 16, True)
        if isinstance(block.get("help"), str):
            # A table's own `help` is a list parallel to its columns (CONTRACT §2, table.py
            # reads it for the column headers); only a plain string here is a title tooltip.
            title.setToolTip(block["help"])     # the uniform "?" of CONTRACT §1 (2026-09-30)
        lay.addWidget(title)
    if block.get("note"):
        lay.addWidget(text(block["note"], T["muted"]))
    for part in parts:
        lay.addWidget(part)
    return frame
