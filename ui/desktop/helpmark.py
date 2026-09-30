"""The «?» beside every button: one application-wide event filter that, the first time a button
is shown, puts a small round mark after it whose tooltip says what the button does.

Where the mark goes: in a horizontal box it is a widget of the box, right after the button, so
the row makes room for it. Anywhere else (a vertical box, a grid, a form) it floats: a child of
the button's parent outside every layout, seated just right of the button when that strip is
free, else over the button's own right edge when the button has that much spare width, else
hidden — the button keeps its tooltip. It never widens a button and never takes a grid cell, so
the owner's layouts stay exactly as their code built them (a cell claimed for the mark would
collide with a widget the code puts there later). The mark follows its button — shown, hidden,
moved, resized, reparented, destroyed — through its own event filter on it.
"""

import sys

from PySide6.QtCore import QEvent, QObject, QRect, Qt
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QBoxLayout, QCalendarWidget,
                               QComboBox, QDialogButtonBox, QLabel, QLayout, QLineEdit,
                               QPushButton, QScrollBar, QTabBar, QToolButton, QToolTip,
                               QWidget)

from ui.text.buttonhelp import help_for, merge

SIZE, GAP = 17, 4                 # the mark's diameter; its distance from the button, px
SKIP_NAMES = {"nav", "helpmark"}  # the sidebar's zone buttons are navigation, not actions
# Qt's own buttons inside other controls, and the breadcrumbs: navigation, not actions.
SKIP_PARENTS = (QTabBar, QComboBox, QDialogButtonBox, QAbstractSpinBox, QLineEdit, QScrollBar,
                QCalendarWidget)
SKIP_CLASSES = {"ContextBar"}
SHOWN = {QEvent.Show, QEvent.ShowToParent}
FOLLOWED = {QEvent.ShowToParent, QEvent.HideToParent, QEvent.Move, QEvent.Resize,
            QEvent.ParentChange}


def guarded(method: object) -> object:
    """Wrap a Python override of a Qt virtual: an exception is reported, never let into Qt."""
    def run(*args: object) -> object:
        """Call the override; on an exception report it and answer «not handled»."""
        try:
            return method(*args)
        except Exception:  # noqa: BLE001 — the window's boundary: a «?» must not take it down
            sys.excepthook(*sys.exc_info())
            return False
    run.__doc__ = method.__doc__
    return run


def scopes(button: QWidget) -> list[str]:
    """The class names of the widgets holding the button, nearest first."""
    return [type(p).__name__ for p in ancestors(button)]


def text_of(button: QWidget) -> str:
    """What the mark says: the button's `help` property, else the registry by its text, merged
    with the button's own tooltip (which often says why it is off now)."""
    said = button.property("help") or help_for(button.text(), scopes(button))
    return merge(said, button.toolTip())


def skipped(button: QWidget) -> bool:
    """True for a button that gets no mark: navigation, Qt internals, flat section heads, or one
    whose `helpmark` property is False."""
    if button.objectName() in SKIP_NAMES or button.property("helpmark") is False:
        return True
    if isinstance(button, QPushButton) and button.isFlat():
        return True
    return any(isinstance(p, SKIP_PARENTS) or type(p).__name__ in SKIP_CLASSES
               for p in ancestors(button))


def ancestors(widget: QWidget) -> list[QWidget]:
    """The widget's parents, nearest first."""
    found, parent = [], widget.parentWidget()
    while parent is not None:
        found.append(parent)
        parent = parent.parentWidget()
    return found


def holder(layout: QLayout | None, widget: QWidget) -> QLayout | None:
    """The layout, at any depth under `layout`, that holds `widget` directly."""
    if layout is None:
        return None
    if layout.indexOf(widget) >= 0:
        return layout
    for i in range(layout.count()):
        found = holder(layout.itemAt(i).layout(), widget)
        if found is not None:
            return found
    return None


class Mark(QLabel):
    """The round «?». Its tooltip is read from the button on every hover, so a button whose text
    changes («Aplicar (3)») keeps the right sentence; a click shows it too and never reaches the
    button. `floating` marks seat themselves (`seat`); boxed ones ride the row's layout."""

    def __init__(self, button: QWidget, floating: bool) -> None:
        """Build the mark for `button`, as a child of the button's parent."""
        super().__init__("?", button.parentWidget(), objectName="helpmark")
        self.button, self.floating = button, floating
        self.setFixedSize(SIZE, SIZE)
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_Hover)
        self.setCursor(Qt.WhatsThisCursor)
        self.setToolTip(text_of(button))
        button.installEventFilter(self)
        button.destroyed.connect(self.orphan)   # a bound slot: Qt drops it if the mark dies first

    def orphan(self, *_: object) -> None:
        """The button is gone: forget it at once (it must never be read again), then go."""
        self.button = None
        self.deleteLater()

    @guarded
    def event(self, e: QEvent) -> bool:
        """Refresh the tooltip from the button right before Qt shows it."""
        if e.type() == QEvent.ToolTip and self.button is not None:
            self.setToolTip(text_of(self.button))
        return super().event(e)

    @guarded
    def mousePressEvent(self, e: object) -> None:
        """Show the sentence on a click as well, and keep the click from the button."""
        QToolTip.showText(e.globalPosition().toPoint(), self.toolTip(), self)
        e.accept()

    @guarded
    def mouseReleaseEvent(self, e: object) -> None:
        """Swallow the release."""
        e.accept()

    @guarded
    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        """Follow the button: its visibility, its place, and a move to another parent."""
        if self.button is None or e.type() not in FOLLOWED:
            return False
        if e.type() == QEvent.ParentChange:
            obj.removeEventFilter(self)
            obj.setProperty("helpmarked", False)   # the Watcher places a new one on next show
            self.orphan()
            if obj.parentWidget() is not None and obj.isVisible():
                attach(obj)
        elif self.floating:
            self.seat()
        else:
            self.setVisible(not obj.isHidden())
        return False

    def seat(self) -> None:
        """Put a floating mark right of its button, or over its spare right edge, or hide it."""
        b, parent = self.button, self.parentWidget()
        g = b.geometry()
        top = g.top() + (g.height() - SIZE) // 2
        beside = QRect(g.right() + 1 + GAP, top, SIZE, SIZE)
        inside = QRect(g.right() - GAP - SIZE, top, SIZE, SIZE)
        others = [w.geometry() for w in parent.findChildren(QWidget,
                                                            options=Qt.FindDirectChildrenOnly)
                  if not w.isHidden() and w is not b and not isinstance(w, Mark)]
        free = parent.rect().contains(beside) and not any(o.intersects(beside) for o in others)
        spare = b.width() - b.sizeHint().width() >= 2 * (SIZE + GAP)
        spot = beside if free else inside if spare else None
        self.setVisible(spot is not None and not b.isHidden())
        if spot is not None:
            self.move(spot.topLeft())
            self.raise_()


def attach(button: QWidget) -> None:
    """Mark a button: in its row when a horizontal box holds it, floating anywhere else."""
    box = holder(button.parentWidget().layout(), button)
    boxed = isinstance(box, QBoxLayout) and box.direction() in (QBoxLayout.LeftToRight,
                                                                QBoxLayout.RightToLeft)
    mark = Mark(button, floating=not boxed)
    button.setProperty("helpmarked", True)
    if boxed:
        box.insertWidget(box.indexOf(button) + 1, mark, 0, Qt.AlignVCenter)
        mark.setVisible(not button.isHidden())
    else:
        mark.seat()


def cursor(button: QWidget) -> None:
    """The hand over a button that can be pressed, the arrow over one that cannot."""
    button.setCursor(Qt.PointingHandCursor if button.isEnabled() else Qt.ArrowCursor)


class Watcher(QObject):
    """The application-wide filter: every button shown gets its cursor, and its mark once."""

    @guarded
    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        """Mark a button on its first show; keep its cursor in step with its state."""
        kind = e.type()
        if kind not in SHOWN and kind != QEvent.EnabledChange:
            return False
        if not isinstance(obj, (QPushButton, QToolButton)):
            return False
        cursor(obj)
        if kind in SHOWN and not obj.property("helpmarked") and obj.parentWidget() is not None \
                and not skipped(obj) and text_of(obj):
            attach(obj)
        return False


def install(app: QApplication) -> None:
    """Install the filter once on the application; a second call does nothing."""
    if getattr(app, "helpmark", None) is None:
        app.helpmark = Watcher(app)
        app.installEventFilter(app.helpmark)
