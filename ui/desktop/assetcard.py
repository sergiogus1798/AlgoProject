"""One asset's costs: what it applies, what SQX carries, and what leaving it undecided costs."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLayout,
                               QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.assetforms import CostBox, now, word
from ui.text.numbers import num
from ui.desktop.theme import C, chip

# What each complaint of the preflight means and what it actually does, in the order the
# owner acts on them: what stops the run, then what blocks authoring, then what only
# stains the result. A figure nobody can define is a figure nobody should act on.
TROUBLE = {
    "broken": ("ESQUEMA ROTO", C["dead"],
               "La preflight sale con 3: el fichero no cuadra con su clase, o pide datos que "
               "SQX no tiene."),
    "pending": ("BLOQUEA LA AUTORÍA", C["dead"],
                "La preflight sale con 2 (regla dura 5): sin ese coste pactado no se escribe "
                "ninguna plantilla ni proyecto para este activo."),
    "segments": ("TRAMOS SIN FECHAS", C["weak"],
                 "No bloquea, pero `window()` se niega a inventar una ventana, así que una "
                 "tarea sobre ese tramo falla al configurarse."),
    "past_data": ("VENTANA POR DELANTE DE LOS DATOS", C["weak"],
                  "Aviso solo: la ventana es correcta y los datos aún no están sincronizados. "
                  "Es el estado normal del tramo más nuevo."),
    "mc": ("RANGOS MC RETEST SIN DECIDIR", C["weak"],
           "No bloquea: sólo vuelve ininterpretable esa tarea del MC Retest."),
    "provisional": ("COSTES PROVISIONALES", C["weak"],
                    "Hay cifra y no bloquea, pero no está pactada con el bróker: TODO "
                    "resultado con coste producido con ella arrastra esa advertencia."),
}


def grid(headers: list[str], stretch: int) -> QTableWidget:
    """An empty table in the house style.

    Args:
        headers: Column keys, shown through the glossary.
        stretch: Which column takes the leftover width.

    Returns:
        A read-only table: every write in this zone goes through a box, never a cell, so a
        stray keystroke cannot change what an instrument costs.
    """
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels([word(h) for h in headers])
    t.verticalHeader().setVisible(False)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.horizontalHeader().setSectionResizeMode(stretch, QHeaderView.Stretch)
    return t


def cell(text: str, tip: str = "") -> QTableWidgetItem:
    """One cell of text, explaining itself on hover.

    Args:
        text: What it says.
        tip: What it means, defaulting to the text itself so a truncated cell is readable.

    Returns:
        The item.
    """
    item = QTableWidgetItem(text)
    item.setToolTip(tip or text)
    return item


def val(value: object) -> str:
    """One value as the tables print it.

    Args:
        value: Anything the daemon sent.

    Returns:
        «sin decidir» for an undecided value (`null` in the file), the figure through
        `numbers.num` otherwise. A per-segment commission (OPEN #27, 2026-09-29: `{build:
        {method, value}, oos1: …}`) reads as one figure when the three agree, else the three;
        it made the whole window fail to open, since Activos is built at start.
    """
    if isinstance(value, dict):
        legs = {seg: (v.get("value"), v.get("method")) for seg, v in value.items()
                if isinstance(v, dict)}
        if not legs:
            return str(value)
        shown = {f"{val(v)}{' %' if m == 'PercentageBased' else ''}" for v, m in legs.values()}
        return (shown.pop() if len(shown) == 1 else
                " · ".join(f"{seg} {val(v)}{' %' if m == 'PercentageBased' else ''}"
                           for seg, (v, m) in legs.items()))
    return "sin decidir" if value is None else num(value)


def derived(value: float, source: str) -> QTableWidgetItem:
    """A bound the file leaves empty and `core.assets` fills: muted, with where it comes from."""
    item = cell(val(value), f"El fichero lo deja vacío; el MC Retest usa este: {source}. "
                            "Doble clic para declarar otro.")
    item.setForeground(QBrush(QColor(C["muted"])))
    return item


def fit(table: QTableWidget) -> None:
    """Give a table exactly the height its rows need.

    Args:
        table: The table, already filled.

    Returns:
        Nothing. These tables live inside one scroll, so a table with its own scrollbar
        would hide rows behind a second one — and the number of rows is small and known.
    """
    table.resizeColumnsToContents()
    # The header, the rows, and the frame's own two borders plus a hair: short by those and
    # the widget below is drawn over the last row.
    height = table.horizontalHeader().height() + 2 * table.frameWidth() + 4
    table.setFixedHeight(height + sum(table.rowHeight(i) for i in range(table.rowCount())))


def clear(layout: QLayout) -> None:
    """Empty a layout of every widget and sub-layout it holds, before drawing it again."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


def send(name: str, path: list, text: str) -> None:
    """Write one value of one assets/ file through the daemon.

    Args:
        name: The file: an asset name, or one of the shared four.
        path: The keys leading to the value.
        text: What was typed. Empty means `null`, which is «sin decidir».
    """
    client.post("assets/value", {"name": name, "path": [str(k) for k in path],
                                 "text": text, "kind": "scalar"})


class AssetCard(QWidget):
    """The head of one asset's page: who it is, what blocks it, and what it costs to trade."""

    changed = Signal()

    def __init__(self) -> None:
        """Build the title, the chips, the complaints strip and the cost table."""
        super().__init__()
        self.data: dict = {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.title = QLabel(objectName="h1")
        self.actions = QHBoxLayout()   # the page puts its buttons here, beside the name
        self.actions.addWidget(self.title)
        self.actions.addStretch()
        lay.addLayout(self.actions)
        self.chips = QLabel()
        self.chips.setWordWrap(True)
        self.trouble = QLabel()
        self.trouble.setWordWrap(True)
        for w in (self.chips, self.trouble):
            lay.addWidget(w)

        head = QLabel("Costes — doble clic para cambiar", objectName="h2")
        head.setToolTip("El ratón encima de una fila dice por qué vale lo que vale.")
        lay.addWidget(head)
        # The `why` is a paragraph: a column for it would take half a page that sits beside
        # another one, so it rides on every cell of its row and in the box that edits it.
        self.costs = grid(["field", "use", "unit", "sqx_now"], 3)
        self.costs.cellDoubleClicked.connect(self.on_cost)
        lay.addWidget(self.costs)
        self.footer = QLabel(objectName="muted")
        self.footer.setWordWrap(True)
        lay.addWidget(self.footer)

    def fill(self, data: dict) -> None:
        """Draw one asset.

        Args:
            data: What `/api/asset/{symbol}` returned.
        """
        self.data = data
        self.title.setText(data["symbol"])
        span = data["data"]
        self.chips.setText("  ".join([
            chip(word(data["class"]), C["accent"]), chip(data["broker"], C["muted"]),
            chip(data["sqx_symbol"], C["muted"]),
            chip(f"Sesión {data['session'] or 'SIN DECIDIR'}",
                 C["muted"] if data["session"] else C["dead"]),
            chip(f"Datos {span['from']} → {span['to']}" if span else "SQX no tiene este feed",
                 C["muted"] if span else C["dead"])]))
        self.trouble.setText(self.complaints())
        self.fill_costs()
        self.footer.setText(
            f"assets/symbols/{data['symbol']}.yaml · sus tramos viven en assets/_policy.yaml · "
            f"proyectos del maestro que lo usan: {', '.join(data['projects']) or 'ninguno'}")

    def complaints(self) -> str:
        """Everything the preflight would say about this asset.

        Returns:
            One line per complaint, naming the fields and what it does, or the clean line.
            Rich text, so a chip sits inline with the sentence that explains it.
        """
        bad = [(k, v) for k, v in self.data["problems"].items() if v]
        if not bad:
            return chip("al día", C["promising"]) + "  Nada sin decidir y nada provisional."
        return "<br>".join(
            f"{chip(TROUBLE[k][0], TROUBLE[k][1])}  "
            f"<span style='color:{C['muted']}'>{', '.join(word(x) for x in v)} — "
            f"{TROUBLE[k][2]}</span>" for k, v in bad)

    def fill_costs(self) -> None:
        """Draw the cost table, in red what stops a project from being written."""
        rows = self.data["costs"]
        self.costs.setRowCount(len(rows))
        for i, c in enumerate(rows):
            use = cell("SIN DECIDIR" if c["use"] is None else val(c["use"]),
                       "Lo que se aplica de verdad, en la unidad de su clase.")
            if c["use"] is None and c["required"]:
                use.setForeground(Qt.GlobalColor.red)
            for j, item in enumerate([
                    cell(word(c["field"])), use, cell(word(c["unit"])),
                    cell(now(c["sqx_now"]), "Lo que el maestro lleva HOY, en SU unidad, que no "
                                            "siempre es la de «Usar».")]):
                item.setToolTip(f"{item.toolTip()}\n\nPor qué: {c['why']}")
                self.costs.setItem(i, j, item)
        fit(self.costs)

    def on_cost(self, row: int, _: int) -> None:
        """Open the cost box on one field and write what it says.

        Args:
            row: Which cost field.
            _: Column; any cell of the row opens the same field.
        """
        if isinstance(self.data["costs"][row]["use"], dict):
            QMessageBox.information(self, "Por tramo", "Este coste va por tramo (build, oos1 y "
                                    "oos2): se edita en «Fichero entero».")
            return
        box = CostBox(self.data["symbol"], self.data["costs"][row])
        if box.exec():
            client.post(f"asset/{self.data['symbol']}/cost", box.payload())
            self.changed.emit()
