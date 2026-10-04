"""The library's front page: what has been tried by family and timeframe, and where to go from a cell."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui.desktop import client, names
from ui.desktop.coveragecells import ACTIONS, LEVELS, MARK, fill_tiles, level, swatch
from ui.desktop.studypage.net import fetch
from ui.desktop.theme import C, verdict_label

AXIS_LABEL = {"archetype": "Familia", "symbol": "Activo", "template": "Plantilla"}
ROW_PX = 56          # three lines of a cell: the runs, where, and the board's count


class Matrix(QWidget):
    """The grid of runs, the director's proposal above it and the chosen cell's actions below."""

    picked = Signal(str)             # a template to open
    go = Signal(str, dict)           # an action of `ACTIONS` (or «proposal») and the cell it is for

    def __init__(self) -> None:
        """Build the header, the proposal line, the table, its legend and the cell's actions."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        head = QHBoxLayout()
        head.addWidget(QLabel("Cobertura", objectName="h1"))
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

        box = QFrame(objectName="panel")
        row = QHBoxLayout(box)
        row.setContentsMargins(14, 8, 14, 8)
        self.proposal = QLabel()
        self.proposal.setStyleSheet("font-size:15px;")
        row.addWidget(self.proposal, 1)
        self.see = QPushButton("Ver propuesta", objectName="primary")
        self.see.setToolTip("Abre Investigar en la propuesta del director: sus tres ideas, que "
                            "sólo tienes que vetar, o el tablero para pedirle una.")
        self.see.clicked.connect(lambda: self.go.emit("proposal", {}))
        row.addWidget(self.see)
        lay.addWidget(box)

        self.table = QTableWidget()
        self.table.setShowGrid(True)
        self.table.verticalHeader().setDefaultSectionSize(ROW_PX)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)   # it is as tall as its rows
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setStyleSheet(f"QTableWidget {{ font-size:14px; }} QHeaderView::section "
                                 f"{{ font-size:15px; font-weight:700; color:{C['text']}; }}")
        self.table.cellClicked.connect(self.on_click)
        self.table.cellDoubleClicked.connect(lambda *_: self.act("templates"))
        self.table.verticalHeader().sectionClicked.connect(self.on_row)
        lay.addWidget(self.table)

        self.legend = QLabel(wordWrap=True)      # a one-line legend set the window's width
        self.legend.setToolTip("El fondo dice cuánto se ha probado en la celda, en cuatro "
                               "escalones. La marca es el MEJOR veredicto que hay dentro: "
                               "✔ algún run prometedor, ~ el mejor quedó flojo, ✘ todos "
                               "muertos; sin marca, sin veredicto escrito. «Tablero» es el número de activos en que el director "
                               "de investigación admite esa familia en ese marco (prior Alta o "
                               "medida que pasa los filtros); sólo trabaja de M15 a H4.")
        lay.addWidget(self.legend)

        box = QFrame(objectName="panel")
        low = QVBoxLayout(box)
        low.setContentsMargins(14, 10, 14, 12)
        low.setSpacing(6)
        self.cell_title = QLabel(objectName="h2")
        low.addWidget(self.cell_title)
        self.cell_text = QLabel(wordWrap=True)
        low.addWidget(self.cell_text)
        buttons = QHBoxLayout()
        self.buttons = {}
        for key, label, tip in ACTIONS:
            b = QPushButton(label, toolTip=tip)
            b.clicked.connect(lambda _, k=key: self.act(k))
            buttons.addWidget(b)
            self.buttons[key] = b
        buttons.addStretch()
        low.addLayout(buttons)
        lay.addWidget(box)
        lay.addStretch()

        self.data: dict = {}
        self.templates: list[dict] = []
        self.board: dict[str, list[dict]] = {}
        self.cell: dict = {}

    def reload(self) -> None:
        """Fetch the matrix, the counts, the director's board and its proposal, and repaint."""
        axis = self.axis.currentData()
        self.data = client.get("coverage", row_axis=axis)
        got = client.get("templates")
        self.templates = got["templates"]
        fill_tiles(self.tiles, got["totals"])
        self.board = {}
        for c in fetch("research/board").get("cells", []):
            row = c["symbol"] if axis == "symbol" else names.spelt(c["family"], names.REGISTRY)
            self.board.setdefault(f"{row}|{c['timeframe']}", []).append(c)
        self.fill_proposal(fetch("research/proposal"))
        self.fill_table()
        self.legend.setText(" &nbsp; ".join(swatch(colour, text) for _, text, colour, _ in LEVELS)
                            + " &nbsp;·&nbsp; ✔ alguna prometedora &nbsp; ~ la mejor, floja &nbsp; "
                              "✘ todas muertas &nbsp;·&nbsp; tablero N: activos (o familias) que "
                              "el director admite ahí")
        self.choose({})

    def fill_proposal(self, p: dict) -> None:
        """The director's newest proposal in one line, or that there is none.

        Args:
            p: `/api/research/proposal`: a proposal, `{"none": ...}` or `{"error": ...}`.
        """
        cell = p.get("cell")
        self.see.setText("Ver propuesta" if cell else "Proponer investigación")
        self.proposal.setText(
            f"<b>El director propone</b> &nbsp; {cell['symbol']} · {cell['timeframe']} · "
            f"{cell['direction']} · <b>{names.family(cell['family'])}</b> &nbsp; — "
            f"{len(p['ideas'])} ideas, {p['created'][:10]}. Tú sólo vetas."
            if cell else "<b>El director no tiene propuesta.</b> Pídele una: elige la mejor celda "
                         "del tablero y trae tres ideas.")

    def row_label(self, row: str) -> str:
        """A row's header: a family by its shown name and how many templates it has."""
        if self.axis.currentData() != "archetype":
            return row
        n = sum(t.get("archetype") == row and not t["orphan"] for t in self.templates)
        return f"{names.family(row)}  ·  {n} plantilla{'' if n == 1 else 's'}"

    def fill_table(self) -> None:
        """Paint one cell per (row, timeframe): how much was tried, where, and the board's count."""
        rows, cols, cells = self.data["rows"], self.data["columns"], self.data["cells"]
        by_symbol = self.axis.currentData() == "symbol"
        self.table.clear()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setVerticalHeaderLabels([self.row_label(r) for r in rows])
        for r, row in enumerate(rows):
            self.table.verticalHeaderItem(r).setToolTip(
                "Clic: las plantillas de esta familia." if self.axis.currentData() == "archetype"
                else "Clic: esta plantilla." if self.axis.currentData() == "template" else "")
            for c, col in enumerate(cols):
                cell = cells.get(f"{row}|{col}")
                board = self.board.get(f"{row}|{col}", [])
                wide = len({b["family"] if by_symbol else b["symbol"] for b in board})
                _, _, ground, ink = level(cell["count"] if cell else 0)
                lines = []
                if cell:
                    n = cell["count"]
                    lines += [MARK.get(cell["verdict"], "")
                              + f"{n} run{'' if n == 1 else 's'}",
                              ", ".join(cell["templates"] if by_symbol else cell["symbols"])]
                if wide:
                    lines.append(f"tablero {wide}")
                item = QTableWidgetItem("\n".join(lines))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QBrush(QColor(ink)))
                item.setBackground(QBrush(QColor(ground)))
                item.setToolTip("\n".join(
                    [f"{self.row_label(row)} · {col}"
                     + (f" — {verdict_label(cell['verdict'])}" if cell else ": sin probar.")]
                    + [f"{x['template']} · {x['symbol']} · {x['date']} · "
                       f"{x['strategies_kept'] or '?'}/{x['strategies_built'] or '?'} "
                       f"estrategias" for x in (cell or {}).get("runs", [])]))
                self.table.setItem(r, c, item)
        self.table.setFixedHeight(self.table.horizontalHeader().sizeHint().height()
                                  + ROW_PX * len(rows) + 4)

    def choose(self, cell: dict) -> None:
        """Make one cell the subject of the action buttons, and say what is in it.

        Args:
            cell: `family` (registry spelling, "" when the row is not a family), `symbol`,
                `timeframe`, `template` (the first one in the cell, or ""), `row` and `text`;
                `{}` for no cell chosen.
        """
        self.cell = cell
        self.cell_title.setText(f"{cell['row']} · {cell['timeframe']}" if cell else
                                "Pulsa una celda, o el nombre de una familia")
        self.cell_text.setText(cell.get("text", "Una celda lleva a sus plantillas, a la paleta "
                                                "de su familia, a una plantilla nueva o a lo "
                                                "que el director mide ahí. El nombre de una "
                                                "familia, a sus plantillas."))
        for key, b in self.buttons.items():
            b.setEnabled(bool(cell) and (key in ("new", "research") or bool(cell["family"])
                                         or (key == "templates" and bool(cell["template"]))))

    def on_click(self, r: int, c: int) -> None:
        """Choose the cell clicked.

        Args:
            r, c: The cell clicked.
        """
        axis = self.axis.currentData()
        row, tf = self.data["rows"][r], self.data["columns"][c]
        cell = self.data["cells"].get(f"{row}|{tf}")
        template = cell["templates"][0] if cell else row if axis == "template" else ""
        family = row if axis == "archetype" else next(
            (t.get("archetype", "") for t in self.templates if t["name"] == template), "")
        board = sorted(self.board.get(f"{row}|{tf}", []), key=lambda b: b["rank"])
        symbol = row if axis == "symbol" else board[0]["symbol"] if board else ""
        tried = (f"{cell['count']} run(s): " + "; ".join(
            f"{x['template']} en {x['symbol']} ({verdict_label(x['verdict'])})"
            for x in cell["runs"]) + "." if cell else "Sin probar.")
        said = (f" Tablero del director: {len(board)} celda(s); la primera, {board[0]['symbol']} "
                f"{board[0]['direction']} · {names.family(board[0]['family'])} (puesto "
                f"{board[0]['rank']})." if board else
                " El tablero del director no tiene nada aquí.")
        self.choose({"family": names.spelt(family, names.REGISTRY) or "", "symbol": symbol,
                     "timeframe": tf, "template": template,
                     "row": self.row_label(row).split("  ·  ")[0], "text": tried + said})

    def on_row(self, r: int) -> None:
        """A row's name was clicked: a family leads to its templates, a template to its page.

        Args:
            r: The row.
        """
        row, axis = self.data["rows"][r], self.axis.currentData()
        if axis == "archetype":
            self.go.emit("templates", {"family": row, "template": ""})
        elif axis == "template":
            self.picked.emit(row)

    def act(self, key: str) -> None:
        """One of the cell's buttons: hand the cell to the shell, which opens the other view.

        Args:
            key: An action of `ACTIONS`.
        """
        if self.cell and self.buttons[key].isEnabled():
            self.go.emit(key, self.cell)
