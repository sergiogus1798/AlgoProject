"""One asset's windows: the three segments, the MC Retest ranges and the retest universe."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui.desktop import client
from ui.desktop.assetcard import cell, fit, grid, send, val
from ui.desktop.assetforms import TextBox


class AssetSpans(QWidget):
    """Where an asset is built and tested, and against which other markets."""

    changed = Signal()

    def __init__(self) -> None:
        """Build the three tables and wire the box each one opens."""
        super().__init__()
        self.data: dict = {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        lay.addWidget(QLabel("Tramos — doble clic en una fecha para cambiarla",
                             objectName="h2"))
        self.segments = grid(["tramo", "desde", "hasta", "spread", "para qué"], 4)
        self.segments.cellDoubleClicked.connect(self.on_segment)
        lay.addWidget(self.segments)

        lay.addWidget(QLabel("MC Retest — lo que sortea cada método, en puntos y absoluto",
                             objectName="h2"))
        self.mc = grid(["rango", "min", "max", "SQX hoy"], 3)
        self.mc.cellDoubleClicked.connect(self.on_mc)
        lay.addWidget(self.mc)

        self.markets_head = QLabel(objectName="h2")
        lay.addWidget(self.markets_head)
        self.markets = grid(["categoría", "mercados"], 1)
        self.markets.cellDoubleClicked.connect(self.on_market)
        lay.addWidget(self.markets)

    def fill(self, data: dict) -> None:
        """Draw one asset's windows.

        Args:
            data: What `/api/asset/{symbol}` returned.
        """
        self.data = data
        rows = data["segments"]
        self.segments.setRowCount(len(rows))
        for i, s in enumerate(rows):
            mark = f"  ⚠️ RESERVADO para {', '.join(s['reserved_for'])}" if s["reserved_for"] else ""
            for j, item in enumerate([
                    cell(s["name"]), cell(val(s["from"])), cell(val(s["to"])),
                    cell(s["spread"], "Qué spread del activo usa este tramo. Por eso un activo "
                                      "no-forex declara dos."),
                    cell(s["purpose"] + mark, s["purpose"])]):
                self.segments.setItem(i, j, item)
        fit(self.segments)
        self.fill_mc()
        self.fill_markets()

    def fill_mc(self) -> None:
        """Draw the MC Retest ranges beside the factory ones the master still carries."""
        rows = self.data["mc_retest"]
        self.mc.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, item in enumerate([
                    cell(r["name"]), cell(val(r["min"])), cell(val(r["max"])),
                    cell(val(r["sqx_now"]), "Lo que el maestro lleva hoy. El de fábrica "
                                            "(spread 1-5) es idéntico en los 142 instrumentos "
                                            "y no significa nada fuera de forex.")]):
                self.mc.setItem(i, j, item)
        fit(self.mc)

    def fill_markets(self) -> None:
        """Draw the retest universe, or say this asset is not a declared main."""
        cats = (self.data["markets"].get("categories") or {})
        self.markets.setRowCount(len(cats))
        self.markets_head.setText(
            "Universo de retest — doble clic para editar una categoría" if cats else
            "Universo de retest — este activo no es un main declarado en _markets.yaml")
        for i, (name, feeds) in enumerate(cats.items()):
            self.markets.setItem(i, 0, cell(
                name, "family: mismo motor económico, la prueba fácil. structural: misma "
                      "estructura y ningún motor compartido, la prueba dura."))
            self.markets.setItem(i, 1, cell(", ".join(f["feed"] for f in feeds) or "(vacío)"))
        fit(self.markets)

    def on_segment(self, row: int, column: int) -> None:
        """Change one bound of one window.

        Args:
            row: Which segment.
            column: 1 for the opening bound, 2 for the closing one; the rest is not a date.
        """
        if column not in (1, 2):
            return
        seg, edge = self.data["segments"][row], "from" if column == 1 else "to"
        box = TextBox(f"{self.data['symbol']} · {seg['name']} · {edge}",
                      "Un año entero (2008) o una fecha (2026-08-30), en ambos casos con los "
                      "dos extremos INCLUIDOS. Vacío = null, sin decidir. Se escribe en "
                      "assets/_policy.yaml, donde están los 19 juntos.", str(seg[edge]), False)
        if box.exec():
            send("policy", ["segments", self.data["symbol"], seg["name"], edge], box.text())
            self.changed.emit()

    def on_mc(self, row: int, column: int) -> None:
        """Change one end of one MC Retest range.

        Args:
            row: Which range.
            column: 1 for min, 2 for max; anything else is not a decision.
        """
        if column not in (1, 2):
            return
        r, edge = self.data["mc_retest"][row], "min" if column == 1 else "max"
        box = TextBox(f"{self.data['symbol']} · MC Retest {r['name']} · {edge}",
                      "En PUNTOS y absoluto, no un múltiplo del spread real: un rango sólo "
                      "significa algo a la escala del propio instrumento.", str(r[edge]), False)
        if box.exec():
            send(self.data["symbol"], ["mc_retest", r["name"], edge], box.text())
            self.changed.emit()

    def on_market(self, row: int, _: int) -> None:
        """Rewrite one category of the retest universe, whole.

        Args:
            row: family or structural.
            _: Column; any cell of the row opens the same category.
        """
        cats = self.data["markets"]["categories"]
        name = list(cats)[row]
        text = "\n".join(f"{f['feed']} {f['data_from']}" for f in cats[name])
        box = TextBox(f"{self.data['symbol']} · {name}",
                      "Un mercado por línea: el feed de SQX, un espacio, y su primera fecha "
                      "con datos. LA LISTA SE FIJA ANTES DE MIRAR NINGÚN RESULTADO — elegirla "
                      "después convierte la prueba en una selección y sus p-valores en "
                      "decoración.", text, True)
        if box.exec():
            feeds = [{"feed": line.split()[0], "data_from": line.split()[1]}
                     for line in box.text().splitlines() if line.strip()]
            client.post("assets/market", {"symbol": self.data["symbol"], "category": name,
                                          "feeds": feeds})
            self.changed.emit()
