"""One 0-100 % bar in the terminal look, shared by the jobs strip and «En marcha»."""

from PySide6.QtWidgets import QProgressBar

from ui.desktop.theme import C, T


def bar(percent: int | None, width: int = 90, colour: str = "") -> QProgressBar:
    """A thin progress bar.

    Args:
        percent: 0-100, or None when nothing says how far: the bar then runs as a busy
            indicator rather than inventing a figure.
        width: Pixels.
        colour: The fill; the accent when empty.

    Returns:
        The bar, its text the percentage («…» when unknown).
    """
    b = QProgressBar()
    b.setFixedWidth(width)
    b.setFixedHeight(14)
    b.setTextVisible(True)
    if percent is None:
        b.setRange(0, 0)
    else:
        b.setRange(0, 100)
        b.setValue(max(0, min(100, int(percent))))
        b.setFormat("%p %")
    fill = colour or C["accent"]
    b.setStyleSheet(f"QProgressBar {{ background: {T['panel']}; border: 1px solid {T['rule']}; "
                    f"border-radius: 3px; color: {T['text']}; font-size: 10px; "
                    f"text-align: center; }} QProgressBar::chunk {{ background: {fill}; "
                    "border-radius: 2px; }")
    return b
