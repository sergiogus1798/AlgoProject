"""The frame every block sits in: its title, its explanation, then what it draws."""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ui.desktop.theme import T


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
        lay.addWidget(text(block["title"], T["text"], 16, True))
    if block.get("note"):
        lay.addWidget(text(block["note"], T["muted"]))
    for part in parts:
        lay.addWidget(part)
    return frame
