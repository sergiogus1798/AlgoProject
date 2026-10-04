"""Two helpers of the interview: empty a layout, and one message bubble."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ui.desktop.theme import C


def drop(layout: QVBoxLayout | QHBoxLayout) -> None:
    """Delete everything in a layout, however deeply nested.

    Args:
        layout: The layout to empty. It survives; its contents do not.

    A stretch is an item with neither a widget nor a layout, which is why this is a
    recursion and not a loop over widgets.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            # setParent(None) as well as deleteLater(): the deletion is deferred to the
            # event loop, and until it runs the old controls keep painting under the new.
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout():
            drop(item.layout())


def bubble(text: str, mine: bool) -> QFrame:
    """One message of the transcript, a framed label; `mine` (the reader's) sits accented."""
    f = QFrame()
    f.setStyleSheet(f"background:{C['accent'] if mine else C['raised']}; border-radius:10px;")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(13, 9, 13, 9)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("background:transparent; color:#ffffff;" if mine else "background:transparent;")
    lay.addWidget(label)
    return f
