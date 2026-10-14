"""The databank panel's table: the columns one sub-panel shows, sortable and movable, losers in red."""

from typing import Any, cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from ui.text.columnhelp import label_for
from ui.text.glossary import label
from ui.desktop.workspace.tablemodel import Rows

# The SQX metrics every sub-panel shows beside its study, in SQX's order, IS then OOS.
BASE = (
    "Net profit",
    "# of trades",
    "Profit factor",
    "Sharpe Ratio",
    "Ret/DD Ratio",
    "Max DD %",
    "Winning Percent",
)
WIDEST = 280  # px: a long reason is cut and read on hover, not allowed to push the rest


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
    # «Cierre › Análisis conjunto» reads only the three studies' verdicts (owner, 2026-09-30:
    # quitar «Beneficio IS / OOS»): Net Profit there answers nothing the WFC/CSCV/veredicto
    # columns do not already decide.
    no_base = sub["studies"] == ["blindJoint"]
    out = []
    for i, c in enumerate(columns):
        if c["kind"] == "name":
            out.append((i, label("strategy")))
        elif c["kind"] == "metric" and c["metric"] in BASE and not no_base:
            out.append((i, f"{label(c['metric'])} {c['sample']}".strip()))
        elif (
            c["kind"] == "study" and every and c["field"] == "verdict" and not c["sub"]
        ):
            out.append((i, c["title"]))
        elif (
            c["kind"] == "study"
            and c["study"] in sub["studies"]
            and c["sub"] == (sub["split"] or "")
        ):
            head = label_for(c["study"], c["field"]) or label(c["field"])
            out.append((i, f"{c['title']} · {head}" if many else head))
    metrics = [p for p in out if columns[p[0]]["kind"] == "metric"]
    order = {m: k for k, m in enumerate(BASE)}
    metrics.sort(
        key=lambda p: (columns[p[0]]["sample"] != "IS", order[columns[p[0]]["metric"]])
    )
    return out[:1] + metrics + [p for p in out[1:] if columns[p[0]]["kind"] != "metric"]


class DataTable(QTableView):
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
        self.setModel(Rows())
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.doubleClicked.connect(lambda i: self.double(i.row()))
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setResizeContentsPrecision(
            100
        )  # rows measured for a width
        self.horizontalHeader().sectionMoved.connect(self.moved)
        self.setToolTip("Doble clic en una fila: su página en «Estrategia».")

    def paint(
        self,
        rows: list[dict],
        shown: list[dict],
        judged: list[int],
        segs: dict | None = None,
    ) -> int:
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
            How many rows the sub-panel holds, the ones a filter hides included.
        """
        if judged:
            rows = [r for r in rows if any(r["values"][i] is not None for i in judged)]
        self.rows, self.ids = rows, [c["id"] for c in shown]
        head = self.horizontalHeader()
        self.setSortingEnabled(False)
        model = cast(Rows, self.model())
        model.hidden = self.hidden
        model.fill(rows, shown, segs)
        head.blockSignals(True)  # forget a header dragged out of place
        for c in range(self.columnCount()):
            head.moveSection(head.visualIndex(c), c)
        head.blockSignals(False)
        head.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.resizeColumnsToContents()
        for c in range(self.columnCount()):
            self.setColumnWidth(c, min(self.columnWidth(c), WIDEST))
        # Only a study's text stretches: a last metric stretched carried its right-aligned
        # figures 1,000 px away from the rest once the owner kept two metrics (2026-09-28).
        head.setStretchLastSection(bool(shown) and shown[-1]["group"] == "Estudio")
        head.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.setSortingEnabled(True)
        return len(rows)

    def rowCount(self) -> int:  # noqa: N802 — the name the callers knew on QTableWidget
        """The rows on show."""
        return self.model().rowCount()

    def columnCount(self) -> int:  # noqa: N802
        """The columns, the name included."""
        return self.model().columnCount()

    def row_at(self, r: int) -> dict[str, Any]:
        """The payload's row shown at view row `r`."""
        return self.rows[cast(Rows, self.model()).order[r]]

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
        cast(Rows, self.model()).rearrange(hidden=self.hidden)

    def double(self, r: int, _c: int = 0) -> None:
        """A row was double-clicked: say which strategy."""
        row = self.row_at(r)
        self.chosen.emit(row["identity"], row["name"])

    def chosen_names(self) -> list[str]:
        """The names of the selected rows, for «correr marcados de este panel»."""
        return sorted(
            {self.row_at(i.row())["name"] for i in self.selectionModel().selectedRows()}
        )
