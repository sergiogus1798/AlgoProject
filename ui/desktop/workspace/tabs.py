"""The workspace's tab bars: the active tab as a rounded box, not an underline (encargo 22 §5)."""

from PySide6.QtWidgets import QTabBar

# The box itself is theme.py's `QFrame#term QTabBar` rule (F0); the second row of the databank
# panel only speaks a step quieter, and Qt merges this over the theme's rule.
SMALL = "QTabBar::tab { font-size: 12px; padding: 2px 10px; }"


def boxed(labels: list[str], small: bool = False) -> QTabBar:
    """A tab bar whose active tab is a rounded box.

    Args:
        labels: One tab each, in order.
        small: The second row of the databank panel, a step quieter than the first.

    Returns:
        The bar, not expanding, so a short row stays at the left like SQX's.
    """
    bar = QTabBar()
    bar.setExpanding(False)
    bar.setDrawBase(False)
    bar.setUsesScrollButtons(True)
    if small:
        bar.setStyleSheet(SMALL)
    for text in labels:
        bar.addTab(text)
    return bar


def refill(bar: QTabBar, labels: list[str]) -> None:
    """Replace every tab of a bar, silently, and select the first.

    Args:
        bar: The bar to refill.
        labels: Its new tabs.
    """
    bar.blockSignals(True)
    while bar.count():
        bar.removeTab(0)
    for text in labels:
        bar.addTab(text)
    bar.setCurrentIndex(0)
    bar.blockSignals(False)
