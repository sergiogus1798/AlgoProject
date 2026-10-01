"""One contract tab, in one column or beside its counterpart: its note, its selectors, its blocks."""

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel, QSizePolicy,
                               QVBoxLayout, QWidget)

from ui.desktop.blocks import markets
from ui.desktop.blocks.card import initial, text
from ui.desktop.blocks.kinds import draw
from ui.desktop.blocks.pick import pairs, selectors, shown
from ui.desktop.theme import T

__all__ = ["Slot", "TabPage", "pairs", "shown"]    # shown and pairs live in pick; kept here for callers


class Slot(QWidget):
    """A tab's slot in the `QTabWidget`. `QTabWidget.sizeHint` is the largest of every page's
    hint whatever its size policy, so a short tab sat on the blank height of the longest one
    opened before it (§1, measured 933 px of content in 8288 px); a hidden slot — every tab but
    the current one — asks for nothing. `heightForWidth` too: the scroll area sizes the page by
    it, and the stack answers the largest of its pages there as well."""

    def sizeHint(self) -> QSize:  # noqa: N802 — Qt's name
        """Its page's hint while it is the current tab, nothing otherwise."""
        return QSize(0, 0) if self.isHidden() else super().sizeHint()

    def minimumSizeHint(self) -> QSize:  # noqa: N802 — Qt's name
        """As `sizeHint`: a hidden tab holds no minimum either."""
        return QSize(0, 0) if self.isHidden() else super().minimumSizeHint()

    def heightForWidth(self, width: int) -> int:  # noqa: N802 — Qt's name
        """As `sizeHint`, for the height the scroll area lays the page out at."""
        return 0 if self.isHidden() else super().heightForWidth(width)


class TabPage(QWidget):
    """The page of one tab. Holds the combos' wiring; what to draw is `shown` and `pairs`."""

    def __init__(self, tabs: list[dict | None], chosen: dict, pool: list[dict] | None = None) -> None:
        """Build the note, the selectors and the first drawing.

        Args:
            tabs: The same tab from each result being shown, None where a side lacks it.
            chosen: The selector values to start from, remembered by the caller.
            pool: Every block of the result, for a lone result whose per-market grids are
                laid side by side with the consensus grid of another tab (`markets`).
        """
        super().__init__()
        # Left at Qt's default (Expanding), this widget's sizeHint stretches to whatever its
        # QStackedWidget parent is given, which pushed a blank gap below a short tab's blocks
        # instead of leaving that space to the page's own trailing stretch (§1 «hueco enorme»).
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.tabs, self.pool = tabs, pool or []
        first = next(t for t in tabs if t is not None)
        self.chosen = {s["key"]: chosen.get(s["key"], s["default"]) for s in selectors(first)}
        # Side by side only on a lone result: a comparison already uses the width for two runs.
        self.grouped = len(tabs) == 1 and markets.grouped(first)
        if self.grouped:
            self.chosen[markets.CHOSEN] = chosen.get(markets.CHOSEN) or markets.first(first)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 10, 4, 4)
        notes = {t.get("note") for t in tabs if t is not None and t.get("note")}
        for note in notes:
            lay.addWidget(text(note, T["text"], 14))
        row = QHBoxLayout()
        for s in selectors(first):
            if self.grouped and s["key"] == markets.KEY:
                continue
            head = QLabel(initial(s["label"]))
            if s.get("help"):
                head.setToolTip(s["help"])   # the uniform "?" of CONTRACT §1 (2026-09-30)
            row.addWidget(head)
            combo = QComboBox()
            for o in s["options"]:       # shown capitalised, chosen by the study's own text
                combo.addItem(initial(o), str(o))
            combo.setCurrentIndex(max(0, combo.findData(str(self.chosen[s["key"]]))))
            combo.setToolTip("Cambia qué combinación se dibuja. No recalcula nada: el estudio "
                             "guardó todas.")
            combo.currentIndexChanged.connect(
                lambda _, k=s["key"], c=combo: self.choose(k, c.currentData()))
            row.addWidget(combo)
        row.addStretch(1)
        lay.addLayout(row)
        if self.grouped:
            lay.addWidget(markets.picker(first, self.chosen[markets.CHOSEN],
                                         lambda on: self.choose(markets.CHOSEN, on)))
        self.body = QWidget()
        lay.addWidget(self.body)
        lay.addStretch(1)
        self.redraw()

    def choose(self, key: str, value: str | list[str]) -> None:
        """Change one selector and redraw from the stored blocks.

        Args:
            key: The selector's key, or `markets.CHOSEN`.
            value: The option chosen, as the combo printed it; the markets on screen for
                `markets.CHOSEN`.
        """
        self.chosen[key] = value
        self.redraw()

    def redraw(self) -> None:
        """Replace the drawn blocks with those the selectors now pick."""
        old = self.body
        self.body = QWidget()
        grid = QGridLayout(self.body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        if self.grouped:
            plain, maps, consensus = markets.split(self.tabs[0], self.chosen, self.pool)
            sides = [plain]
        else:
            sides = [shown(t, self.chosen) if t is not None else [] for t in self.tabs]
        rows = [(b,) for b in sides[0]] if len(sides) == 1 else pairs(*sides)
        for i, row in enumerate(rows):
            for j, b in enumerate(row):
                grid.addWidget(draw(b) if b is not None else
                               text("(Sin equivalente en este lado)", T["faint"]), i, j)
        if self.grouped and maps:
            grid.addWidget(markets.row(maps, consensus), len(rows), 0)
            rows.append(maps)
        for j in range(len(sides)):
            grid.setColumnStretch(j, 1)
        if not rows:
            grid.addWidget(text("Esta combinación no tiene bloques.", T["faint"]), 0, 0)
        self.layout().replaceWidget(old, self.body)
        old.hide()          # deleteLater waits for the event loop; until then it would paint over
        old.deleteLater()
