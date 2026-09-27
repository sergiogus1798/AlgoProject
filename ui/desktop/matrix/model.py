"""The matrix as a Qt model: strategies × studies, filtered and sorted in Python, painted by the view."""

from collections import Counter

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from ui.desktop.blocks.states import label

# The two fixed columns before the studies.
FIXED = ("estrategia", "identidad")
# Sort order of a study column: what decides first, then what only informs, then the holes.
RANK = {"fail": 0, "watch": 1, "pass": 2, "info": 3, "none": 4, "missing": 5}
# This machine has no font with ⛔ or 👁: the header paints both marks, text uses these two.
ROLE_MARK = {"gate": "⊘", "describe": "◉"}
ROLE_HELP = {
    "gate": "⊘ ELIMINA: su verdict.csv está hecho para sacar estrategias del databank con /curate.",
    "describe": "◉ DESCRIBE: informa sobre la estrategia; no saca a nadie del databank.",
}
CELL = Qt.UserRole + 1


def headline(entry: dict) -> str:
    """The tooltip of one study column: what it is, its step, what its role means, what a click does.

    Args:
        entry: The study's row of `/api/catalogue`.

    Returns:
        Spanish text.
    """
    step = f"paso {entry['step']} del workflow" if entry["step"] else "lectura sin paso fijo"
    return (f"{entry['title']} ({entry['key']}) · {step}\n{ROLE_HELP[entry['role']]}\n"
            "Debajo: cuántas de las filas visibles caen en cada estado.\n"
            "Clic: abre el resultado de la población. Clic derecho: ordenar y filtrar.")


def cell_tip(name: str, entry: dict, cell: dict | None) -> str:
    """The tooltip of one cell.

    Args:
        name: Strategy name.
        entry: The study's catalogue row.
        cell: `{state, label, stale, day}` or None when the study never judged it.

    Returns:
        Spanish text saying what the study said, when, and whether today's config would still sign it.
    """
    if cell is None:
        return f"{name} · {entry['title']}: no corrido en este databank."
    stale = {True: "CADUCADO: la configuración de hoy firmaría otro hash; conviene volver a correrlo.",
             False: "Vigente: la configuración de hoy firma lo mismo.",
             None: "No se sabe si caducó: la corrida no guardó su hash."}[cell["stale"]]
    return (f"{name} · {entry['title']}\n{label(cell['state'])}: «{cell['label']}» "
            f"({cell['day']})\n{stale}\nClic: abre el estudio de esta estrategia.")


class MatrixModel(QAbstractTableModel):
    """One databank's matrix. Holds only what the daemon sent; `rows` is the visible order."""

    def __init__(self) -> None:
        """Start empty."""
        super().__init__()
        self.strategies: list[dict] = []
        self.cells: dict = {}
        self.columns: list[dict] = []
        self.rows: list[int] = []
        self.text = ""
        self.wanted: dict[str, set[str]] = {}
        self.counts: list[Counter] = []
        self.order: tuple[str, Qt.SortOrder] | None = None

    def load(self, data: dict, columns: list[dict]) -> None:
        """Take a new `/api/matrix` answer and the catalogue rows to show as columns.

        Args:
            data: The route's JSON.
            columns: Catalogue entries, in column order.
        """
        self.beginResetModel()
        self.strategies, self.cells, self.columns = data["strategies"], data["cells"], columns
        self.wanted = {k: v for k, v in self.wanted.items() if k in {c["key"] for c in columns}}
        self._refilter()
        self.endResetModel()

    def state(self, row: int, key: str) -> str:
        """The state of one strategy in one study, `missing` when never run."""
        cell = self.cells.get(self.strategies[row]["identity"], {}).get(key)
        return cell["state"] if cell else "missing"

    def _refilter(self) -> None:
        """Recompute the visible rows from the text and the per-column state filters, and the counts."""
        needle = self.text.lower()
        self.rows = [i for i, s in enumerate(self.strategies)
                     if needle in s["strategy"].lower()
                     and all(self.state(i, k) in ok for k, ok in self.wanted.items())]
        self.counts = [Counter(self.state(i, c["key"]) for i in self.rows) for c in self.columns]
        if self.order and self.order[0] in {"strategy", "identity"} | {
                c["key"] for c in self.columns}:
            self._sort_rows(*self.order)

    def refilter(self, text: str | None = None) -> None:
        """Apply a new name filter, or reapply the current filters after `wanted` changed.

        Args:
            text: Case-insensitive fragment of the name; None keeps the current one.
        """
        self.beginResetModel()
        if text is not None:
            self.text = text
        self._refilter()
        self.endResetModel()

    def _sort_rows(self, field: str, order: Qt.SortOrder) -> None:
        """Sort the visible rows in place by a fixed field or a study key; the name breaks ties."""
        if field in ("strategy", "identity"):
            key = lambda i: self.strategies[i][field]  # noqa: E731
        else:
            key = lambda i: (RANK.get(self.state(i, field), 4),  # noqa: E731
                             self.strategies[i]["strategy"])
        self.rows.sort(key=key, reverse=order == Qt.DescendingOrder)

    def field(self, column: int) -> str:
        """What one model column holds: "strategy", "identity" or a study key."""
        return ("strategy", "identity")[column] if column < len(FIXED) else \
            self.columns[column - len(FIXED)]["key"]

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Sort by one column and keep that order through later filters and column changes.

        Args:
            column: Model column.
            order: Qt's order.
        """
        self.layoutAboutToBeChanged.emit()
        self.order = (self.field(column), order)
        self._sort_rows(*self.order)
        self.layoutChanged.emit()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Visible rows."""
        return len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Name, identity and one per shown study."""
        return len(FIXED) + len(self.columns)

    def strategy(self, view_row: int) -> dict:
        """The `{strategy, identity}` behind one visible row."""
        return self.strategies[self.rows[view_row]]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> object:
        """Text for the fixed columns; the cell dict (CELL role) and tooltip for the studies."""
        s = self.strategies[self.rows[index.row()]]
        col = index.column()
        if col < len(FIXED):
            if role == Qt.DisplayRole:
                return s["strategy"] if col == 0 else s["identity"][:10]
            if role == Qt.ToolTipRole:
                return f"{s['strategy']}\nidentidad {s['identity']}"
            return None
        entry = self.columns[col - len(FIXED)]
        cell = self.cells.get(s["identity"], {}).get(entry["key"])
        if role == CELL:
            return cell
        if role == Qt.ToolTipRole:
            return cell_tip(s["strategy"], entry, cell)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.DisplayRole) -> object:
        """Column titles with their role mark, and the tooltip that explains them."""
        if orientation != Qt.Horizontal:
            return None
        if section < len(FIXED):
            tips = ("El nombre tal y como SQX lo escribió. Clic derecho: ordenar.",
                    "SHA-256 del XML normalizado: lo que empareja los estudios, no el nombre.")
            return {Qt.DisplayRole: FIXED[section], Qt.ToolTipRole: tips[section]}.get(role)
        entry = self.columns[section - len(FIXED)]
        if role == Qt.DisplayRole:
            return entry["title"]
        if role == Qt.ToolTipRole:
            counts = self.counts[section - len(FIXED)]
            said = " · ".join(f"{label(k)} {n:,}" for k, n in counts.most_common())
            return f"{headline(entry)}\nFilas visibles: {said or 'ninguna'}."
        return None
