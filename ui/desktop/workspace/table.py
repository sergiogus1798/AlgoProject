"""The databank panel's table: the columns one sub-panel shows, sortable and movable, losers in red."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C
from ui.desktop.workspace.columns import DASH, note, unprofitable, value

# The SQX metrics every sub-panel shows beside its study, in SQX's order, IS then OOS.
BASE = ("Net profit", "# of trades", "Profit factor", "Sharpe Ratio", "Ret/DD Ratio",
        "Max DD %", "Winning Percent")
STATE_INK = {"pass": C["promising"], "fail": C["dead"], "watch": C["weak"]}
WIDEST = 280            # px: a long reason is cut and read on hover, not allowed to push the rest


class Cell(QTableWidgetItem):
    """One cell: shown through `numbers.num`, sorted on its value (a number as a number)."""

    def __init__(self, value: object, ink: str = "", blank: str = "", tip: str = "") -> None:
        """Hold the value in `ink` (the dead colour for a figure that says the strategy loses,
        `columns.unprofitable`); `blank` is what a missing value reads («–» for a metric with
        no data), `tip` why."""
        super().__init__(num(value) if value is not None else blank)
        self.value = value
        if value is None and blank:
            self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setForeground(QColor(C["muted"]))
            self.setToolTip(tip)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if ink:
            self.setForeground(QColor(ink))
        if isinstance(value, str) and len(value) > 30:
            self.setToolTip(value)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        """Figures before words, each among its own kind in order, and a blank or «–» last
        whichever way the column is sorted: Qt sorts descending by asking `other < self`, so
        a blank is the largest going up and the smallest going down."""
        table = self.tableWidget()
        down = table is not None and \
            table.horizontalHeader().sortIndicatorOrder() == Qt.DescendingOrder

        def key(v: object) -> tuple:
            """A sort key that never compares a number with a text."""
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return (0, v, "")
            return (1, 0, str(v)) if v is not None else (-1 if down else 2, 0, "")
        return key(self.value) < key(getattr(other, "value", None))


def pick(columns: list[dict], sub: dict) -> list[tuple[int, str]]:
    """The columns one sub-panel shows, as (index in the payload, header).

    Args:
        columns: GET /api/databank/table's `columns`.
        sub: The sub-panel from GET /api/databank/panels: `studies` (`*` for every study's
            verdict) and `split` (the task, market, timeframe or composition, or None).

    Returns:
        The name first, then the base metrics present, then the study's own columns. Several
        studies in one sub-panel carry their title in the header.
    """
    every = sub["studies"] == ["*"]
    many = every or len(sub["studies"]) > 1
    out = []
    for i, c in enumerate(columns):
        if c["kind"] == "name":
            out.append((i, label("strategy")))
        elif c["kind"] == "metric" and c["metric"] in BASE:
            out.append((i, f"{label(c['metric'])} {c['sample']}".strip()))
        elif c["kind"] == "study" and every and c["field"] == "verdict" and not c["sub"]:
            out.append((i, c["title"]))
        elif (c["kind"] == "study" and c["study"] in sub["studies"]
              and c["sub"] == (sub["split"] or "")):
            head = label(c["field"])
            out.append((i, f"{c['title']} · {head}" if many else head))
    metrics = [p for p in out if columns[p[0]]["kind"] == "metric"]
    order = {m: k for k, m in enumerate(BASE)}
    metrics.sort(key=lambda p: (columns[p[0]]["sample"] != "IS",
                                order[columns[p[0]]["metric"]]))
    return out[:1] + metrics + [p for p in out[1:] if columns[p[0]]["kind"] != "metric"]


class DataTable(QTableWidget):
    """The rows of one databank under one sub-panel's columns. Double click emits the row's
    identity (None for a row only a report without identity names) and its name."""

    chosen = Signal(object, str)
    reordered = Signal(list)

    def __init__(self) -> None:
        """Rows are selected whole and never edited."""
        super().__init__()
        self.rows: list[dict] = []
        self.ids: list[str] = []
        self.hidden: set[str] = set()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.cellDoubleClicked.connect(self.double)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().sectionMoved.connect(self.moved)
        self.setToolTip("Doble clic en una fila: su página en «Estrategia».")

    def paint(self, rows: list[dict], shown: list[dict], judged: list[int],
              segs: dict | None = None) -> int:
        """Fill the table.

        Args:
            rows: The payload's rows.
            shown: The chosen columns after the name (`columns.resolve`), in order.
            judged: Payload indices of the sub-panel's own study columns: when given, only
                the rows one of them said something of are kept — a batch study speaks of its
                mothers only, and 197 blank rows would hide the three. Hiding those columns
                does not change which rows the sub-panel holds.
            segs: GET /api/databank/segments, for the IS+OOS1 columns.

        Returns:
            How many rows are in the table.
        """
        if judged:
            rows = [r for r in rows if any(r["values"][i] is not None for i in judged)]
        self.rows, self.ids = rows, [c["id"] for c in shown]
        self.setSortingEnabled(False)
        self.clear()
        self.setColumnCount(0)          # also forgets a header dragged out of place
        self.setColumnCount(len(shown) + 1)
        self.setRowCount(len(rows))
        self.setHorizontalHeaderLabels([label("strategy")] + [c["header"] for c in shown])
        for c, choice in enumerate(shown, 1):
            tip = choice["why"] or ""
            self.horizontalHeaderItem(c).setToolTip(f"Sin datos: {tip}" if tip else "")
        for r, row in enumerate(rows):
            name = Cell(row["name"])
            name.setData(Qt.UserRole, r)
            font = name.font()
            font.setBold(True)
            name.setFont(font)
            self.setItem(r, 0, name)
            for c, choice in enumerate(shown, 1):
                study = choice["group"] == "Estudio"
                state = row["states"].get(choice["id"]) if study else None
                got = value(choice, row, segs)
                tip = note(choice, row, segs) if got is None and not study else ""
                ink = STATE_INK.get(state) or (C["dead"] if unprofitable(choice["id"], got)
                                               else "")
                self.setItem(r, c, Cell(got, ink, "" if study else DASH, tip))
        head = self.horizontalHeader()
        head.setSectionResizeMode(QHeaderView.Interactive)
        self.resizeColumnsToContents()
        for c in range(self.columnCount()):
            self.setColumnWidth(c, min(self.columnWidth(c), WIDEST))
        # Only a study's text stretches: a last metric stretched carried its right-aligned
        # figures 1,000 px away from the rest once the owner kept two metrics (2026-09-28).
        head.setStretchLastSection(bool(shown) and shown[-1]["group"] == "Estudio")
        self.setSortingEnabled(True)
        self.set_hidden(self.hidden)
        return len(rows)

    def moved(self, *_moved: int) -> None:
        """A header was dragged: the ids in their new order for the panel to keep. The name
        column is put back in front first, which moves again and lands here once more."""
        head = self.horizontalHeader()
        if head.visualIndex(0) != 0:
            head.moveSection(head.visualIndex(0), 0)
            return
        order = sorted(range(1, self.columnCount()), key=head.visualIndex)
        self.reordered.emit([self.ids[c - 1] for c in order])

    def set_hidden(self, identities: set[str]) -> None:
        """Hide the rows of these strategies — what a filter set aside (F6), still in SQX."""
        self.hidden = set(identities)
        for r in range(self.rowCount()):
            row = self.rows[self.item(r, 0).data(Qt.UserRole)]
            self.setRowHidden(r, row["identity"] in self.hidden)

    def double(self, r: int, _c: int) -> None:
        """A row was double-clicked: say which strategy."""
        row = self.rows[self.item(r, 0).data(Qt.UserRole)]
        self.chosen.emit(row["identity"], row["name"])

    def chosen_names(self) -> list[str]:
        """The names of the selected rows, for «correr marcados de este panel»."""
        return sorted({self.rows[self.item(i.row(), 0).data(Qt.UserRole)]["name"]
                       for i in self.selectionModel().selectedRows()})
