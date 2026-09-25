"""The coverage matrix: the first thing the window shows, and the one that names the gaps."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.theme import (C, VERDICT_COLOUR, VERDICT_LABEL, chip, verdict_colour,
                              verdict_label)

AXIS_LABEL = {"archetype": "Arquetipo", "symbol": "Activo", "template": "Plantilla"}
TILE_HELP = {
    "templates": "Filas de registry.csv que no están archivadas. Una plantilla es una idea, "
                 "no una estrategia y no un mercado.",
    "build_confirmed": "Cuántas han pasado de 'el XML resuelve' a 'una construcción real sacó "
                       "estrategias que llevan su bloque'. Es el único estado que prueba algo.",
    "runs": "Filas de runs.csv: cada una es una plantilla probada en un activo y un timeframe.",
    "symbols": "Activos distintos tocados por alguna corrida.",
    "timeframes": "Timeframes distintos tocados por alguna corrida.",
    "archetypes_used": "Arquetipos con al menos una plantilla, sobre los que el catálogo conoce. "
                       "La distancia entre los dos números es de lo que tienes poco.",
    "drafts": "Briefs que el chat ha redactado y que nadie ha autorado todavía. No cuentan "
              "como plantillas: no tienen .sqx.",
}


def tile(title: str, value: str, help_key: str) -> QFrame:
    """One headline count, with the sentence that says what it counts.

    Args:
        title: The label under the number.
        value: The number, already formatted.
        help_key: Key into `TILE_HELP` for the tooltip.

    Returns:
        A framed widget. Every number in this window explains itself on hover; a count
        nobody can define is a count nobody should act on.
    """
    f = QFrame(objectName="tile")
    f.setToolTip(TILE_HELP[help_key])
    lay = QVBoxLayout(f)
    lay.setContentsMargins(14, 10, 14, 10)
    lay.setSpacing(1)
    big = QLabel(value)
    big.setStyleSheet("font-size:22px; font-weight:600;")
    lay.addWidget(big)
    lay.addWidget(QLabel(title, objectName="faint"))
    return f


class Matrix(QWidget):
    """The grid of runs, with the axis down the side chosen by the reader."""

    picked = Signal(str)

    def __init__(self) -> None:
        """Build the header, the axis selector, the legend and the empty table."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        head = QHBoxLayout()
        title = QLabel("Cobertura", objectName="h1")
        head.addWidget(title)
        head.addStretch()
        head.addWidget(QLabel("Filas:", objectName="muted"))
        self.axis = QComboBox()
        for key, label in AXIS_LABEL.items():
            self.axis.addItem(label, key)
        self.axis.currentIndexChanged.connect(self.reload)
        head.addWidget(self.axis)
        lay.addLayout(head)

        self.tiles = QHBoxLayout()
        self.tiles.setSpacing(10)
        lay.addLayout(self.tiles)

        self.table = QTableWidget()
        self.table.setShowGrid(True)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self.on_click)
        lay.addWidget(self.table)
        lay.addStretch()

        legend = QLabel(" · ".join(
            chip(VERDICT_LABEL[v], c) for v, c in VERDICT_COLOUR.items())
            + f' · <span style="color:{C["faint"]}">celda vacía = sin probar</span>')
        legend.setToolTip("El color de una celda es el MEJOR veredicto que hay dentro: "
                          "una celda es una invitación a mirar, no un resumen estadístico.")
        lay.addWidget(legend)

        self.data: dict = {}

    def reload(self) -> None:
        """Fetch the matrix and the counts for the axis now selected, and repaint."""
        axis = self.axis.currentData()
        self.data = client.get("coverage", row_axis=axis)
        totals = client.get("templates")["totals"]
        self.fill_tiles(totals)
        self.fill_table()

    def fill_tiles(self, totals: dict) -> None:
        """Redraw the headline counts.

        Args:
            totals: The dict `coverage.totals` returned.
        """
        while self.tiles.count():
            # The last item of the row is the stretch, and a spacer has no widget: asking
            # it for one and deleting it is what made the second reload crash.
            item = self.tiles.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        shown = [("Plantillas", str(totals["templates"]), "templates"),
                 ("Confirmadas", str(totals["build_confirmed"]), "build_confirmed"),
                 ("Corridas", str(totals["runs"]), "runs"),
                 ("Activos", str(totals["symbols"]), "symbols"),
                 ("Timeframes", str(totals["timeframes"]), "timeframes"),
                 ("Arquetipos cubiertos",
                  f"{totals['archetypes_used']}/{totals['archetypes_total']}", "archetypes_used"),
                 ("Borradores", str(totals["drafts"]), "drafts")]
        for title, value, key in shown:
            self.tiles.addWidget(tile(title, value, key))
        self.tiles.addStretch()

    def fill_table(self) -> None:
        """Paint one cell per (row, timeframe), coloured by the best verdict inside it."""
        rows, cols, cells = self.data["rows"], self.data["columns"], self.data["cells"]
        self.table.clear()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setVerticalHeaderLabels(rows)
        for r, row in enumerate(rows):
            for c, col in enumerate(cols):
                cell = cells.get(f"{row}|{col}")
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                if cell:
                    item.setText(f"{cell['count']} · {', '.join(cell['symbols'])}"
                                 if self.axis.currentData() != "symbol"
                                 else f"{cell['count']} · {', '.join(cell['templates'])}")
                    item.setForeground(QBrush(QColor(verdict_colour(cell["verdict"]))))
                    item.setBackground(QBrush(QColor(C["raised"])))
                    item.setToolTip("\n".join(
                        [f"{row} · {col} — {verdict_label(cell['verdict'])}"]
                        + [f"{x['template']} · {x['symbol']} · {x['date']} · "
                           f"{x['strategies_kept'] or '?'}/{x['strategies_built'] or '?'} "
                           f"estrategias" for x in cell["runs"]]
                        + ["", "Clic para abrir la plantilla."]))
                    item.setData(Qt.UserRole, cell["templates"][0])
                else:
                    item.setBackground(QBrush(QColor(C["untried"])))
                    item.setToolTip(f"{row} · {col}: sin probar.")
                self.table.setItem(r, c, item)
        self.table.setFixedHeight(40 + 46 * len(rows))

    def on_click(self, r: int, c: int) -> None:
        """Open the template behind a cell.

        Args:
            r, c: The cell clicked.
        """
        name = self.table.item(r, c).data(Qt.UserRole)
        if name:
            self.picked.emit(name)
