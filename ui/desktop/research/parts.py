"""What the four views of «Investigar» share: family colours, a filled table, a daemon call."""

import html
from collections.abc import Callable

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from ui.desktop import background
from ui.desktop.theme import T

# One hue per family, far apart on a black ground; never a meaning shared with the verdicts.
FAMILY = {"tendencia": "#4da3ff", "ruptura": "#ff9a3c", "reversion": "#3ddc84",
          "momentum": "#ff5fa2", "volatilidad": "#ffe14d", "patron": "#35d6d6",
          "sesion": "#b48cff"}
SHORT = {"tendencia": "TEND", "ruptura": "RUPT", "reversion": "REV", "momentum": "MOM",
         "volatilidad": "VOL", "patron": "PATR", "sesion": "SES"}
ARROW = {"long": "▲", "short": "▼", "both": "◆"}
SHARE = {1: 0.30, 2: 0.60, 3: 1.0}       # the three discrete intensities
GREY = "#2a2a2e"


def shade(family: str, level: int) -> str:
    """A family's colour at one of the three intensities: mixed with the terminal's black."""
    ink, ground, k = QColor(FAMILY[family]), QColor(T["bg"]), SHARE[level]
    return QColor(*(round(ground.getRgb()[i] + k * (ink.getRgb()[i] - ground.getRgb()[i]))
                    for i in range(3))).name()


def ink_on(level: int) -> str:
    """Readable text over a shaded cell: black on the full colour, white below."""
    return "#000000" if level == 3 else "#ffffff"


def table(heads: list[tuple[str, str]]) -> QTableWidget:
    """A read-only table whose header cells carry their explanation as a tooltip."""
    t = QTableWidget(0, len(heads))
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.verticalHeader().hide()
    t.setWordWrap(True)
    for i, (head, tip) in enumerate(heads):
        item = QTableWidgetItem(head)
        item.setToolTip(tip)
        t.setHorizontalHeaderItem(i, item)
    for i in range(len(heads) - 1):          # the last column takes the rest and wraps
        t.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    return t


def fill(t: QTableWidget, rows: list[list], colours: list[str | None] | None = None) -> None:
    """Put rows of text into a table; `colours` paints each row's first cell."""
    t.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            if c == 0 and colours and colours[r]:
                item.setForeground(QColor(colours[r]))
            t.setItem(r, c, item)
    t.resizeRowsToContents()


def esc(value: object) -> str:
    """Text a person or an agent wrote, safe inside a rich-text label («Close < Open»)."""
    return html.escape(str(value))


def num(value: object, digits: int = 2) -> str:
    """A number for a cell; «—» for a missing one."""
    return "—" if value is None else f"{value:.{digits}f}"


def call(owner: QWidget, work: Callable[[], dict], done: Callable[[dict], None],
         key: str) -> None:
    """Ask the daemon off the GUI thread; straight away when the view was given a fake."""
    if owner.sync:
        done(work())
    else:
        background.run(work, done, key=key, owner=owner)
