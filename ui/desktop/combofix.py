"""Every QComboBox in the app shows all the options that fit on screen, application-wide, one filter."""

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QComboBox, QWidget

# §1 «Desplegables: mostrar todas las opciones que quepan» (2026-09-30, again 2026-10-01): the
# rows a popup shows are bounded by the screen, never by a count. The other half of the fix is
# `combobox-popup: 0` in `theme.QSS`: Qt's menu-style popup reserved two scroller arrows inside
# the rows' own height, so 2 options got 30 px for 48 and 4 got 78 for 96 (measured offscreen).
MAX_VISIBLE = 1000


def _fit(popup: QWidget, combo: QComboBox) -> None:
    """Grow an open popup to every row the screen can hold, upwards when the space under the
    combo ran out first; it stays on screen and the view scrolls beyond.

    Args:
        popup: The combo's popup window, just shown.
        combo: Its combo.
    """
    view = combo.view()
    need = sum(view.sizeHintForRow(i) for i in range(combo.count())) \
        + popup.height() - view.viewport().height()
    room = popup.screen().availableGeometry()
    height = min(need, room.height())
    if popup.height() >= height:
        return
    top = max(room.top(), min(popup.y(), room.bottom() + 1 - height))
    popup.setGeometry(popup.x(), top, popup.width(), height)


class ComboFix(QObject):
    """Lifts every combo's visible-rows cap and fits each popup to the screen as it opens."""

    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        """On a combo's first show lift its cap; on its popup's show fit it to the screen.

        Args:
            obj: Any widget the application dispatches events to.
            e: The event.

        Returns:
            False always: this only sizes widgets, it never consumes the event.
        """
        if e.type() != QEvent.Show:
            return False
        if isinstance(obj, QComboBox) and obj.maxVisibleItems() < MAX_VISIBLE:
            obj.setMaxVisibleItems(MAX_VISIBLE)
        elif isinstance(obj, QWidget) and obj.isWindow() and isinstance(obj.parent(), QComboBox):
            _fit(obj, obj.parent())
        return False


def install(app: QApplication) -> None:
    """Install `ComboFix` once on the application; a second call does nothing.

    Args:
        app: The Qt application.
    """
    if getattr(app, "combofix", None) is None:
        app.combofix = ComboFix(app)
        app.installEventFilter(app.combofix)
