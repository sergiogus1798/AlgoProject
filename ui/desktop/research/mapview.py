"""The map: assets × timeframes, colour = dominant family, intensity = effect; click for the measures."""

from collections.abc import Callable

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.desktop.blocks.card import text
from ui.desktop.research import parts
from ui.desktop.theme import T

INTRO = ("Cada casilla es un activo en un marco temporal, medido sólo en build. El color es la "
         "familia que mejor paga entre las que pasan los cuatro filtros (significativa, paga el "
         "doble del coste, estable por años y con operaciones suficientes al año); la intensidad, cuánto paga. Gris: ninguna pasa, y "
         "el director no propone ahí. Pulsa una casilla para ver sus medidas.")
FAMILIES = [("Dir.", "Largo o corto: se miden por separado."),
            ("Familia", "La familia de comportamiento."),
            ("Punt.", "0 a 100: lo lejos que están sus medidas del azar. El ruido da unos 8."),
            ("Medida líder", "La medida que habla por la familia."),
            ("p corr.", "p de la líder corregida por las ~4.000 pruebas. Menos de 0,05: significativa."),
            ("× coste", "Ganancia media por operación entre el coste de ida y vuelta. Hace falta 2."),
            ("Años", "Años de build con el signo a favor, del total."),
            ("Op/año", "Operaciones al año de la líder. El cuarto filtro pide 40 (35 a lo sumo "
                       "para un activo que el dueño nombre)."),
            ("Pasa", "Los cuatro filtros a la vez.")]
MEASURES = [("Dir.", ""), ("Familia", ""), ("Medida", ""),
            ("z", "Desviaciones respecto a 1.000 series barajadas."),
            ("p corr.", "p corregida (Benjamini-Hochberg)."),
            ("× coste", "Ganancia media por operación entre el coste."),
            ("Años", "Años con el signo a favor."),
            ("Op/año", "Operaciones al año: el cuarto filtro pide 40."),
            ("Pasa", "Los cuatro filtros."), ("Qué mide", "")]


class MapView(QWidget):
    """The grid on the left, the chosen cell's families and measures on the right."""

    def __init__(self, fetch: Callable[..., dict], sync: bool) -> None:
        """Build the empty grid and the detail tables."""
        super().__init__()
        self.fetch, self.sync, self.cells = fetch, sync, {}
        self.grid = QGridLayout()
        self.grid.setSpacing(3)
        self.legend = text("", T["muted"], 13)
        left = QVBoxLayout()
        left.addWidget(text(INTRO, T["muted"], 13))
        left.addLayout(self.grid)
        left.addWidget(self.legend)
        left.addStretch(1)
        self.title = QLabel("Pulsa una casilla", objectName="h2")
        self.context = text("", T["muted"], 13)
        self.families = parts.table(FAMILIES)
        self.measures = parts.table(MEASURES)
        right = QVBoxLayout()
        right.addWidget(self.title)
        right.addWidget(self.context)
        right.addWidget(QLabel("FAMILIAS", objectName="kicker"))
        right.addWidget(self.families, 2)
        right.addWidget(QLabel("MEDIDAS, CADA UNA CON LO QUE MIDE", objectName="kicker"))
        right.addWidget(self.measures, 3)
        lay = QHBoxLayout(self)
        lay.addLayout(left, 2)
        lay.addLayout(right, 3)

    def reload(self) -> None:
        """Read the map again."""
        parts.call(self, lambda: self.fetch("research/map"), self.paint, "research-map")

    def paint(self, got: dict) -> None:
        """Draw the grid: one button per asset × timeframe."""
        if "error" in got:
            self.legend.setText(got["error"])
            return
        while self.grid.count():
            self.grid.takeAt(0).widget().deleteLater()
        for c, tf in enumerate(got["timeframes"], 1):
            self.grid.addWidget(QLabel(tf, objectName="kicker"), 0, c)
        for r, symbol in enumerate(got["symbols"], 1):
            mark = " *" if symbol in got["provisional"] else ""
            self.grid.addWidget(QLabel(symbol + mark, objectName="mono"), r, 0)
            for c, tf in enumerate(got["timeframes"], 1):
                self.grid.addWidget(self.button(symbol, tf, got["cells"].get(f"{symbol}|{tf}")),
                                    r, c)
        keys = "   ".join(f"<span style='color:{parts.FAMILY[f]}'>■</span> {f}"
                          for f in got["families"])
        levels = " · ".join(lv["label"] for lv in reversed(got["levels"]))
        self.legend.setText(f"{keys}<br>Intensidad (tres escalones): {levels}.<br>▲ largo · ▼ "
                            "corto · el número es el efecto medido en múltiplos del coste; «prior»: "
                            "la celda está en el tablero sólo por tu prior.<br>* costes "
                            "provisionales.")

    def button(self, symbol: str, tf: str, cell: dict | None) -> QPushButton:
        """One cell: family, direction and effect in words as well as in colour."""
        best = (cell or {}).get("passing") or []
        measured = bool(best) and best[0]["trades_per_year"] is not None
        b = QPushButton("—" if not best else
                        f"{parts.SHORT[best[0]['family']]} {parts.ARROW[best[0]['direction']]} "
                        + (f"{best[0]['multiple']:.0f}x" if measured else "prior"))
        b.setProperty("helpmark", False)
        b.setMinimumSize(96, 30)
        ground = parts.shade(best[0]["family"], best[0]["level"]) if best else parts.GREY
        ink = parts.ink_on(best[0]["level"]) if best else T["faint"]
        b.setStyleSheet(f"QPushButton {{ background: {ground}; color: {ink}; border: 1px solid "
                        f"{T['line']}; border-radius: 3px; font-weight: 700; font-size: 13px; }}"
                        f"QPushButton:hover {{ border: 2px solid {T['text']}; }}")
        b.setToolTip("Ninguna familia está en el tablero (ni prior Alta ni lo medido la admite)" + (
            f"; la de más puntuación: {cell['best']['family']} {cell['best']['direction']} "
            f"({cell['best']['score']})" if cell else "") if not best else "\n".join(
            f"{p['family']} {p['direction']}: prior {p['prior'] or 'ninguna'}, entra por "
            f"{'+'.join(p['entered_by'])}; {p['state']}; " + (
                f"{p['multiple']}x el coste, {p['trades_per_year']} op/año"
                if p["trades_per_year"] is not None else "efecto y frecuencia sin medir")
            for p in best))
        b.clicked.connect(lambda: self.open(symbol, tf))
        return b

    def open(self, symbol: str, tf: str) -> None:
        """Read one cell's measures."""
        self.title.setText(f"{symbol} · {tf}")
        parts.call(self, lambda: self.fetch("research/cell", symbol=symbol, timeframe=tf),
                   self.detail, "research-cell")

    def detail(self, got: dict) -> None:
        """Fill the two tables and the context line, every figure with its explanation."""
        if "error" in got:
            self.context.setText(got["error"])
            return
        yes = lambda v: "SÍ" if v else "no"  # noqa: E731
        years = lambda r: f"{parts.num(r['years_with_sign'], 0)}/{parts.num(r['years'], 0)}"  # noqa: E731
        parts.fill(self.families, [
            [parts.ARROW[f["direction"]], f["family"], parts.num(f["score"], 1), f["lead"],
             parts.num(f["p"], 3), parts.num(f["multiple"], 1), years(f),
             parts.num(f["trades_per_year"], 1), yes(f["passes"])] for f in got["families"]],
            [parts.FAMILY[f["family"]] if f["passes"] else None for f in got["families"]])
        parts.fill(self.measures, [
            [parts.ARROW[m["direction"]], m["family"], m["measure"], parts.num(m["z"], 1),
             parts.num(m["q"], 3), parts.num(m["multiple"], 1), years(m),
             parts.num(m["trades_per_year"], 1), yes(m["passes"]), m["explanation"]]
            for m in got["measures"]],
            [parts.FAMILY[m["family"]] if m["passes"] else None for m in got["measures"]])
        c, tips = got["context"], got["context_help"]
        self.context.setText("<br>".join(
            f"<b>{parts.num(c.get(k), 3)}</b> — {tip}" for k, tip in tips.items()))
