"""One contract tab, in one column or beside its counterpart: its note, its selectors, its blocks."""

from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop.blocks.card import text
from ui.desktop.blocks.kinds import draw
from ui.desktop.theme import T


def shown(tab: dict, chosen: dict) -> list[dict]:
    """The blocks of a tab that agree with the chosen selector values.

    Args:
        tab: One contract tab.
        chosen: {selector key: option}. A value this tab does not offer falls back to the
            tab's own default, so two runs whose options differ still both draw something.

    Returns:
        The blocks to draw: those untagged, and those whose every `select` value is chosen.
        Nothing is recomputed; the study already stored every combination (CONTRACT §1).
    """
    pick = {}
    for s in tab.get("selectors") or []:
        offered = [str(o) for o in s["options"]]
        want = str(chosen.get(s["key"]))
        pick[s["key"]] = want if want in offered else str(s["default"])
    # Compared as text: a combo hands back text, and an option may be a number in the JSON.
    return [b for b in tab["blocks"]
            if all(pick.get(k) == str(v) for k, v in (b.get("select") or {}).items())]


def pairs(left: list[dict], right: list[dict]) -> list[tuple[dict | None, dict | None]]:
    """Each block beside its counterpart: same kind and title first, else the next of its kind.

    Args:
        left, right: The blocks each side shows.

    Returns:
        (left, right) rows in the left's order, the right's leftovers at the end.
    """
    free = list(right)
    out = []
    for b in left:
        same = [r for r in free if (r["kind"], r.get("title")) == (b["kind"], b.get("title"))]
        kin = [r for r in free if r["kind"] == b["kind"]]
        twin = (same or kin or [None])[0]
        if twin is not None:
            free.remove(twin)
        out.append((b, twin))
    return out + [(None, r) for r in free]


class TabPage(QWidget):
    """The page of one tab. Holds the combos' wiring; what to draw is `shown` and `pairs`."""

    def __init__(self, tabs: list[dict | None], chosen: dict) -> None:
        """Build the note, the selectors and the first drawing.

        Args:
            tabs: The same tab from each result being shown, None where a side lacks it.
            chosen: The selector values to start from, remembered by the caller.
        """
        super().__init__()
        self.tabs = tabs
        first = next(t for t in tabs if t is not None)
        self.chosen = {s["key"]: chosen.get(s["key"], s["default"])
                       for s in first.get("selectors") or []}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 10, 4, 4)
        notes = {t.get("note") for t in tabs if t is not None and t.get("note")}
        for note in notes:
            lay.addWidget(text(note, T["text"], 14))
        row = QHBoxLayout()
        for s in first.get("selectors") or []:
            row.addWidget(QLabel(s["label"]))
            combo = QComboBox()
            combo.addItems([str(o) for o in s["options"]])
            combo.setCurrentText(str(self.chosen[s["key"]]))
            combo.setToolTip("Cambia qué combinación se dibuja. No recalcula nada: el estudio "
                             "guardó todas.")
            combo.currentTextChanged.connect(lambda v, k=s["key"]: self.choose(k, v))
            row.addWidget(combo)
        row.addStretch(1)
        lay.addLayout(row)
        self.body = QWidget()
        lay.addWidget(self.body)
        lay.addStretch(1)
        self.redraw()

    def choose(self, key: str, value: str) -> None:
        """Change one selector and redraw from the stored blocks.

        Args:
            key: The selector's key.
            value: The option chosen, as the combo printed it.
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
        sides = [shown(t, self.chosen) if t is not None else [] for t in self.tabs]
        rows = [(b,) for b in sides[0]] if len(sides) == 1 else pairs(*sides)
        for i, row in enumerate(rows):
            for j, b in enumerate(row):
                grid.addWidget(draw(b) if b is not None else
                               text("(sin equivalente en este lado)", T["faint"]), i, j)
        for j in range(len(sides)):
            grid.setColumnStretch(j, 1)
        if not rows:
            grid.addWidget(text("Esta combinación no tiene bloques.", T["faint"]), 0, 0)
        self.layout().replaceWidget(old, self.body)
        old.hide()          # deleteLater waits for the event loop; until then it would paint over
        old.deleteLater()
