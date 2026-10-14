"""The databank table's model: one sub-panel's cells read off the payload, sorted and filtered."""

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor, QFont

from ui.text.glossary import label
from ui.text.verdictwords import verdict_word
from ui.text.numbers import num
from ui.desktop.theme import C
from ui.desktop.workspace.columns import DASH, note, unprofitable, value

STATE_INK = {"pass": C["promising"], "fail": C["dead"], "watch": C["weak"]}
RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
# Looked up once: reading a role off `Qt` on every call was most of `data`'s cost (🔬 2026-10-04,
# 224,000 calls in 4.9 s while Qt measured the columns).
SHOW, ALIGN, INK, FONT, TIP = (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.TextAlignmentRole, Qt.ItemDataRole.ForegroundRole,
                               Qt.ItemDataRole.FontRole, Qt.ItemDataRole.ToolTipRole)
ROLES = {SHOW, ALIGN, INK, FONT, TIP}


def number(v: object) -> bool:
    """A figure, not a flag."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class Rows(QAbstractTableModel):
    """The table's cells, read off the payload when Qt asks for one: nothing is built per cell.
    🔬 2026-10-04: one `QTableWidgetItem` per cell froze the window 6.5–13 s on a 10,000-row
    databank (280,000 items); a model costs the cells on screen."""

    def __init__(self) -> None:
        """Empty until `fill`."""
        super().__init__()
        self.rows, self.shown, self.segs = [], [], None
        self.hidden: set[str] = set()
        self.order: list[int] = []          # view row → index in `rows`, the hidden left out
        self.by: tuple | None = None        # (column, descending) once a header was clicked
        self.bold = QFont()
        self.bold.setBold(True)

    def fill(self, rows: list[dict], shown: list[dict], segs: dict | None) -> None:
        """Take another sub-panel's rows and columns, unsorted."""
        self.beginResetModel()
        self.rows, self.shown, self.segs, self.by = rows, shown, segs, None
        self.arrange()
        self.endResetModel()

    def got(self, raw: int, c: int) -> object:
        """One cell's value: the name in column 0, else what `columns.value` reads."""
        row = self.rows[raw]
        return row["name"] if c == 0 else value(self.shown[c - 1], row, self.segs)

    def arrange(self) -> None:
        """Rebuild `order`: the rows no filter hid, sorted as the header says — figures before
        words, each among its own kind, and a blank or «–» last whichever way."""
        self.order = [i for i, r in enumerate(self.rows) if r["identity"] not in self.hidden]
        if self.by is None:
            return
        c, down = self.by

        def key(raw: int) -> tuple:
            """A sort key that never compares a number with a text."""
            v = self.got(raw, c)
            if number(v):
                return (0, v, "")
            return (1, 0, str(v)) if v is not None else (-1 if down else 2, 0, "")
        self.order.sort(key=key, reverse=down)

    def rearrange(self, hidden: set[str] | None = None, by: tuple | None = None) -> None:
        """Hide rows or sort, the selection following its strategies. A layout change, never
        a reset: `modelReset` is what the filters strip reads as «another table painted»."""
        self.layoutAboutToBeChanged.emit()
        old = self.persistentIndexList()
        was = [self.order[i.row()] for i in old]
        self.hidden = self.hidden if hidden is None else hidden
        self.by = by or self.by
        self.arrange()
        at = {raw: r for r, raw in enumerate(self.order)}
        self.changePersistentIndexList(old, [
            self.index(at[w], i.column()) if w in at else QModelIndex() for w, i in zip(was, old)])
        self.layoutChanged.emit()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """A header click."""
        if 0 <= column < self.columnCount():
            self.rearrange(by=(column, order == Qt.SortOrder.DescendingOrder))

    def rowCount(self, _parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802,B008 — Qt name, immutable default
        """The rows on show."""
        return len(self.order)

    def columnCount(self, _parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802,B008 immutable default
        """The name and the chosen columns."""
        return len(self.shown) + 1 if self.rows or self.shown else 0

    def headerData(self, c: int, way: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> object:  # noqa: N802
        """A header and its tooltip; a column that explains itself carries a visible «(?)»
        (owner, 2026-10-01)."""
        if way == Qt.Orientation.Horizontal and role == ALIGN and c and self.shown[c - 1]["group"] == "Estudio":
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter   # over its words, also when it stretches
        if way != Qt.Orientation.Horizontal or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return None
        if c == 0:
            return label("strategy") if role == Qt.ItemDataRole.DisplayRole else None
        choice = self.shown[c - 1]
        if role == Qt.ItemDataRole.DisplayRole:
            return choice["header"] + (" (?)" if choice.get("help") else "")
        tip = choice["why"] or ""
        return "\n\n".join(t for t in (choice.get("help") or "",
                                       f"Sin datos: {tip}" if tip else "") if t)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        """One cell: shown through `numbers.num`; a missing metric a grey «–» with why on hover
        (a missing study value stays blank); a study's pass/fail in its colour and bold (owner,
        2026-09-30), and in the dead colour a figure that says the strategy loses."""
        if role not in ROLES:
            return None
        raw, c = self.order[index.row()], index.column()
        row, got = self.rows[raw], self.got(raw, c)
        choice: Any = self.shown[c - 1] if c else None
        study = bool(c) and choice["group"] == "Estudio"
        dash = got is None and c and not study
        state: Any = row["states"].get(choice["id"]) if study else None
        if role == SHOW:
            return num(verdict_word(got) if study else got) if got is not None else (
                DASH if dash else "")
        if role == ALIGN:
            return RIGHT if dash or number(got) else None
        if role == INK:
            ink = STATE_INK.get(state) or (C["dead"] if c and unprofitable(choice["id"], got)
                                           else C["muted"] if dash else "")
            return QColor(ink) if ink else None
        if role == FONT:
            return self.bold if c == 0 or state in ("pass", "fail") else None
        if role == TIP:
            if dash:
                return note(choice, row, self.segs)
            return got if isinstance(got, str) and len(got) > 30 else None
        return None
