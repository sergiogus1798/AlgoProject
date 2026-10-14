"""«Tablero»: the board the director reads, one row per cell-family. No launcher: the director has none."""

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui.desktop import names
from ui.desktop.blocks.card import text
from ui.desktop.research import parts
from ui.desktop.theme import T

BOARD = [
    ("#", "Puesto en el tablero."),
    ("Celda", "Activo, marco, dirección y familia."),
    ("Puntos", "100 × freno × (señal, hueco y pasado con sus pesos)."),
    (
        "Señal",
        "Efecto de la medida líder en múltiplos del coste; entre paréntesis, de 0 a 1.",
    ),
    ("Hueco", "Intentos de esa familia en esa celda: sin probar vale 1."),
    (
        "Pasado",
        "Tasa de supervivencia de la familia en esa clase de activo, con su "
        "intervalo; sin corridas cerradas es plana (0,50).",
    ),
    ("Freno", "Ideas ya gastadas en la celda: cada una baja los puntos."),
    ("Op/año", "Operaciones al año de la medida líder."),
    ("Avisos", ""),
]


class DirectView(QWidget):
    """The board, read-only."""

    def __init__(self, fetch: Callable[..., dict], sync: bool) -> None:
        """Build the table."""
        super().__init__()
        self.fetch, self.sync = fetch, sync
        self.head = text("", T["muted"], 13)
        self.board = parts.table(BOARD)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("El tablero que lee el director", objectName="kicker"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        lay.addWidget(self.head)
        lay.addWidget(self.board, 1)

    def reload(self) -> None:
        """Read the board."""
        parts.call(
            self, lambda: self.fetch("research/board"), self.paint, "research-board"
        )

    def paint(self, got: dict) -> None:
        """Fill the board, each factor's raw value beside its 0-1."""
        if "error" in got:
            self.head.setText(got["error"])
            return
        self.head.setText(
            f"{len(got['cells'])} celdas-familia en el tablero (prior Alta, o pasa "
            f"los cuatro filtros, o barrido en meseta), de {got['cell_families']}. "
            f"{got['closed_runs']} corridas cerradas en la memoria."
        )
        rows = []
        for c in got["cells"]:
            f, p = c["factors"], c["past"]
            warn = [
                f"prior {c['prior'] or 'ninguna'}",
                "entra por " + "+".join(c["entered_by"]),
            ]
            warn += ["«Medido en contra»"] if c["evidence"] == "against" else []
            warn += ["pullback"] if c["pullback"] else []
            warn += ["costes provisionales"] if c["provisional_costs"] else []
            free = c["trades_per_year"] is None
            rows.append(
                [
                    c["rank"],
                    f"{c['symbol']} {c['timeframe']} {c['direction']} · {names.family(c['family'])}",
                    c["points"],
                    "sin medir" if free else f"{c['multiple']}x ({f['signal']:.2f})",
                    f"{c['attempts']} ({f['gap']:.2f})",
                    f"{p['with_survivors']}/{p['closed']} · {p['rate']:.2f} "
                    f"[{p['low']:.2f}-{p['high']:.2f}]",
                    f"{c['ideas_spent']} ideas (×{f['brake']:.2f})",
                    "sin medir" if free else c["trades_per_year"],
                    ", ".join(warn) or "—",
                ]
            )
        parts.fill(self.board, rows)
