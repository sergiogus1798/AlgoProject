"""The table of one databank's strategies: the name and the handful of metrics that rank them."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from ui.desktop.theme import C

HELP = {
    "Net profit": "Beneficio neto en la moneda de la cuenta, tras los costes de la tarea.",
    "# of trades": "Operaciones cerradas. Por debajo de ~100 casi ningún test tiene potencia.",
    "Profit factor": "Beneficio bruto entre pérdida bruta. 1 es el empate.",
    "Sharpe Ratio": "Retorno medio entre su desviación, anualizado como lo hace SQX.",
    "Ret/DD Ratio": "Beneficio neto entre el peor drawdown. Cuántas veces se recuperó lo peor.",
    "Max DD %": "El peor drawdown, en porcentaje del capital.",
}


def cell(value: object) -> QTableWidgetItem:
    """One cell, right-aligned when it holds a number.

    Args:
        value: What the daemon sent: a name, a float, an int or None.

    Returns:
        The item, negative figures in the dead colour so a losing column is seen at once.
    """
    if value is None:
        item = QTableWidgetItem("·")
        item.setForeground(Qt.GlobalColor.gray)
    elif isinstance(value, (int, float)):
        item = QTableWidgetItem(f"{value:,.0f}" if abs(value) >= 1000 else f"{value:g}")
        if value < 0:
            item.setForeground(Qt.GlobalColor.red)
    else:
        item = QTableWidgetItem(str(value))
    if isinstance(value, (int, float)):
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    return item


class StrategyTable(QTableWidget):
    """The strategies of the open databank, one row each, sortable by any column."""

    picked = Signal(str)

    def __init__(self) -> None:
        """Build an empty table that announces the selected strategy's name."""
        super().__init__()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.itemSelectionChanged.connect(self.announce)

    def fill(self, columns: list[str], rows: list[list]) -> None:
        """Replace the whole table.

        Args:
            columns: Header labels; the first is the strategy name.
            rows: One list per strategy, in the export's order.
        """
        self.setSortingEnabled(False)
        self.clear()
        self.setColumnCount(len(columns))
        self.setRowCount(len(rows))
        self.setHorizontalHeaderLabels(columns)
        for j, label in enumerate(columns):
            metric = label.split(" · ")[0]
            self.horizontalHeaderItem(j).setToolTip(HELP.get(metric, "El nombre tal y como "
                                                              "SQX lo escribió."))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.setItem(i, j, cell(value))
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # The name is the one column the reader must be able to read whole: it gets its
        # width first and can be dragged; the figures take what they need.
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        self.setColumnWidth(0, 190)
        self.setSortingEnabled(True)

    def announce(self) -> None:
        """Say which strategy is now selected."""
        rows = self.selectionModel().selectedRows()
        if rows:
            self.picked.emit(self.item(rows[0].row(), 0).text())

    def filter(self, text: str) -> None:
        """Hide the rows whose name does not contain the text.

        Args:
            text: Case-insensitive fragment; empty shows all.
        """
        needle = text.lower()
        for i in range(self.rowCount()):
            self.setRowHidden(i, needle not in self.item(i, 0).text().lower())
