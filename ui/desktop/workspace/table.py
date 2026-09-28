"""The databank panel's table: the columns one sub-panel shows, sortable, negatives in red."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C

# The SQX metrics every sub-panel shows beside its study, in SQX's order, IS then OOS.
BASE = ("Net profit", "# of trades", "Profit factor", "Sharpe Ratio", "Ret/DD Ratio",
        "Max DD %", "Winning Percent")
STATE_INK = {"pass": C["promising"], "fail": C["dead"], "watch": C["weak"]}
WIDEST = 280            # px: a long reason is cut and read on hover, not allowed to push the rest


class Cell(QTableWidgetItem):
    """One cell: shown through `numbers.num`, sorted on its value (a number as a number)."""

    def __init__(self, value: object, ink: str = "") -> None:
        """Hold the value; a negative figure in the dead colour, as the Net Profit is today."""
        super().__init__(num(value) if value is not None else "")
        self.value = value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ink = ink or (C["dead"] if value < 0 else "")
        if ink:
            self.setForeground(QColor(ink))
        if isinstance(value, str) and len(value) > 30:
            self.setToolTip(value)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        """Figures before words before blanks, each among its own kind in order."""
        def key(v: object) -> tuple:
            """A sort key that never compares a number with a text."""
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return (0, v, "")
            return (1, 0, str(v)) if v is not None else (2, 0, "")
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

    def __init__(self) -> None:
        """Rows are selected whole and never edited."""
        super().__init__()
        self.rows: list[dict] = []
        self.hidden: set[str] = set()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.cellDoubleClicked.connect(self.double)
        self.setToolTip("Doble clic en una fila: su página en «Estrategia».")

    def paint(self, columns: list[dict], rows: list[dict], shown: list[tuple[int, str]],
              only_judged: bool) -> int:
        """Fill the table.

        Args:
            columns: The payload's columns.
            rows: The payload's rows.
            shown: What `pick` chose.
            only_judged: Keep only the rows a shown study said something of — a batch study
                speaks of its mothers only, and 197 blank rows would hide the three.

        Returns:
            How many rows are in the table.
        """
        judged = [i for i, _ in shown if columns[i]["kind"] == "study"]
        if only_judged:
            rows = [r for r in rows if any(r["values"][i] is not None for i in judged)]
        self.rows = rows
        self.setSortingEnabled(False)
        self.clear()
        self.setColumnCount(len(shown))
        self.setRowCount(len(rows))
        self.setHorizontalHeaderLabels([h for _, h in shown])
        for r, row in enumerate(rows):
            for c, (i, _) in enumerate(shown):
                state = row["states"].get(columns[i]["key"]) if columns[i]["kind"] == "study" \
                    else None
                cell = Cell(row["values"][i], STATE_INK.get(state, ""))
                cell.setData(Qt.UserRole, r)
                if c == 0:
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                self.setItem(r, c, cell)
        head = self.horizontalHeader()
        head.setSectionResizeMode(QHeaderView.Interactive)
        self.resizeColumnsToContents()
        for c in range(self.columnCount()):
            self.setColumnWidth(c, min(self.columnWidth(c), WIDEST))
        head.setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.set_hidden(self.hidden)
        return len(rows)

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
