"""One asset's costs: what it applies, what SQX carries, and what leaving it undecided costs."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QVBoxLayout, QWidget

from ui.desktop import client
from ui.desktop.assetforms import CostBox, word
from ui.desktop.assettable import cell, fit, grid, val
from ui.desktop.theme import C, chip

# What each complaint of the preflight means and what it actually does, in the order the
# owner acts on them: what stops the run, then what blocks authoring, then what only
# stains the result. A figure nobody can define is a figure nobody should act on.
TROUBLE = {
    "broken": (
        "Esquema roto",
        C["dead"],
        "La preflight sale con 3: el fichero no cuadra con su clase, o pide datos que "
        "SQX no tiene.",
    ),
    "pending": (
        "Bloquea la autoría",
        C["dead"],
        "La preflight sale con 2 (regla dura 5): sin ese coste pactado no se escribe "
        "ninguna plantilla ni proyecto para este activo.",
    ),
    "segments": (
        "Tramos sin fechas",
        C["weak"],
        "No bloquea, pero `window()` se niega a inventar una ventana, así que una "
        "tarea sobre ese tramo falla al configurarse.",
    ),
    "past_data": (
        "Ventana por delante de los datos",
        C["weak"],
        "Aviso solo: la ventana es correcta y los datos aún no están sincronizados. "
        "Es el estado normal del tramo más nuevo.",
    ),
    "mc": (
        "Rangos MC Retest sin decidir",
        C["weak"],
        "No bloquea: sólo vuelve ininterpretable esa tarea del MC Retest.",
    ),
    "provisional": (
        "Costes provisionales",
        C["weak"],
        "Hay cifra y no bloquea, pero no está pactada con el bróker: TODO "
        "resultado con coste producido con ella arrastra esa advertencia.",
    ),
}


class AssetCard(QWidget):
    """The head of one asset's page: who it is, what blocks it, and what it costs to trade."""

    changed = Signal()

    def __init__(self) -> None:
        """Build the title, the chips, the complaints strip and the cost table."""
        super().__init__()
        self.data: dict = {}
        # The name, the chips and the complaints span the page; the page places `top` itself
        # and this widget keeps only the cost table, one column among three (owner, 2026-10-02).
        self.top = QWidget()
        top = QVBoxLayout(self.top)
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(4)
        self.title = QLabel(objectName="h1")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.bar = QHBoxLayout()  # the page puts its buttons here, beside the name
        self.bar.addWidget(self.title)
        self.bar.addStretch()
        top.addLayout(self.bar)
        self.chips = QLabel()
        self.chips.setWordWrap(True)
        self.trouble = QLabel()
        self.trouble.setWordWrap(True)
        for w in (self.chips, self.trouble):
            top.addWidget(w)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        head = QLabel("Costes (doble clic para cambiar)", objectName="h2")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        head.setToolTip("El ratón encima de una fila dice por qué vale lo que vale.")
        lay.addWidget(head)
        # The `why` is a paragraph: a column for it would take half a page that sits beside
        # another one, so it rides on every cell of its row and in the box that edits it.
        self.costs = grid(["field", "use", "unit"])
        self.costs.cellDoubleClicked.connect(self.on_cost)
        lay.addWidget(self.costs)
        self.footer = QLabel(objectName="muted")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.footer.setWordWrap(True)
        lay.addWidget(self.footer)

    def fill(self, data: dict) -> None:
        """Draw one asset.

        Args:
            data: What `/api/asset/{symbol}` returned.
        """
        self.data = data
        self.title.setText(data["symbol"])
        feed = data["data"]
        self.chips.setText(
            "  ".join(
                [
                    chip(word(data["class"]), C["accent"], 15),
                    chip(data["broker"], C["muted"]),
                    chip(data["sqx_symbol"], C["muted"]),
                    chip(
                        f"Sesión {data['session'] or 'sin decidir'}",
                        C["muted"] if data["session"] else C["dead"],
                    ),
                    chip(
                        f"Datos {feed['from']} → {feed['to']}"
                        if feed
                        else "SQX no tiene este feed",
                        C["muted"] if feed else C["dead"],
                    ),
                ]
            )
        )
        self.trouble.setText(self.complaints())
        # The why of each warning is a tooltip, not a sentence on the page (owner, 2026-09-30).
        self.trouble.setToolTip(
            "\n".join(
                f"{TROUBLE[k][0]}: {TROUBLE[k][2]}"
                for k, v in data["problems"].items()
                if v
            )
        )
        self.fill_costs()
        self.footer.setText("")  # owner, 2026-09-30: no «proyectos que lo usan» line

    def complaints(self) -> str:
        """Everything the preflight would say about this asset.

        Returns:
            One line per complaint, naming the fields and what it does, or the clean line.
            Rich text, so a chip sits inline with the sentence that explains it.
        """
        bad = [(k, v) for k, v in self.data["problems"].items() if v]
        if not bad:
            return chip("al día", C["promising"], 15)
        return "<br>".join(
            chip(TROUBLE[k][0], TROUBLE[k][1])
            + (
                ""
                if k == "mc"
                # the chip says it all
                else f"  <span style='color:{C['muted']}'>{', '.join(word(x) for x in v)}</span>"
            )
            for k, v in bad
        )

    def fill_costs(self) -> None:
        """Draw the cost table, in red what stops a project from being written."""
        rows = self.data["costs"]
        self.costs.setRowCount(len(rows))
        for i, c in enumerate(rows):
            use = cell(
                "Sin decidir" if c["use"] is None else val(c["use"]),
                "Lo que se aplica de verdad, en la unidad de su clase.",
            )
            if c["use"] is None and c["required"]:
                use.setForeground(Qt.GlobalColor.red)
            for j, item in enumerate(
                [cell(word(c["field"])), use, cell(word(c["unit"]))]
            ):
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
            QMessageBox.information(
                self,
                "Por tramo",
                "Este coste va por tramo (build, oos1 y "
                "oos2): se edita en «Fichero entero».",
            )
            return
        box = CostBox(self.data["symbol"], self.data["costs"][row])
        if box.exec():
            client.post(f"asset/{self.data['symbol']}/cost", box.payload())
            self.changed.emit()
