"""«Proponer investigación»: the board the director will read, the button, and the step it is in."""

from collections.abc import Callable

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ui.desktop.blocks.card import text
from ui.desktop.research import parts
from ui.desktop.theme import T

POLL_MS = 5000
BOARD = [("#", "Puesto en el tablero."), ("Celda", "Activo, marco, dirección y familia."),
         ("Puntos", "100 × freno × (señal, hueco y pasado con sus pesos)."),
         ("Señal", "Efecto de la medida líder en múltiplos del coste; entre paréntesis, de 0 a 1."),
         ("Hueco", "Intentos de esa familia en esa celda: sin probar vale 1."),
         ("Pasado", "Tasa de supervivencia de la familia en esa clase de activo, con su "
                    "intervalo; sin corridas cerradas es plana (0,50)."),
         ("Freno", "Ideas ya gastadas en la celda: cada una baja los puntos."),
         ("Op/año", "Operaciones al año de la medida líder."), ("Avisos", "")]


class DirectView(QWidget):
    """The board, then the button with its cost, then the director's five steps."""

    proposed = Signal()

    def __init__(self, fetch: Callable[..., dict], send: Callable[[str, dict], dict],
                 sync: bool) -> None:
        """Build the table, the button and the step list."""
        super().__init__()
        self.fetch, self.send, self.sync, self.was_running = fetch, send, sync, False
        self.head = text("", T["muted"], 13)
        self.board = parts.table(BOARD)
        self.button = QPushButton("▶ Proponer investigación", objectName="primary")
        self.button.setProperty("help", "Lanza al director de investigación: elige una celda del "
                                        "tablero y trae tres ideas con su paleta. 10-30 $.")
        self.button.clicked.connect(self.press)
        self.steps = text("", T["text"], 14)
        self.said = text("", T["muted"], 13)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("EL TABLERO QUE LEE EL DIRECTOR", objectName="kicker"))
        lay.addWidget(self.head)
        lay.addWidget(self.board, 1)
        lay.addWidget(self.button)
        lay.addWidget(self.steps)
        lay.addWidget(self.said)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)

    def reload(self) -> None:
        """Read the board and the director's state."""
        parts.call(self, lambda: self.fetch("research/board"), self.paint, "research-board")
        self.poll()

    def paint(self, got: dict) -> None:
        """Fill the board, each factor's raw value beside its 0-1."""
        if "error" in got:
            self.head.setText(got["error"])
            return
        self.head.setText(f"{len(got['cells'])} celdas-familia en el tablero (prior Alta, o pasa "
                          f"los cuatro filtros, o barrido en meseta), de {got['cell_families']}. "
                          f"{got['closed_runs']} corridas cerradas en la memoria.")
        rows = []
        for c in got["cells"]:
            f, p = c["factors"], c["past"]
            warn = [f"prior {c['prior'] or 'ninguna'}", "entra por " + "+".join(c["entered_by"])]
            warn += ["«MEDIDO EN CONTRA»"] if c["evidence"] == "against" else []
            warn += ["pullback"] if c["pullback"] else []
            warn += ["costes provisionales"] if c["provisional_costs"] else []
            free = c["trades_per_year"] is None
            rows.append([c["rank"], f"{c['symbol']} {c['timeframe']} {c['direction']} {c['family']}",
                         c["points"],
                         "sin medir" if free else f"{c['multiple']}x ({f['signal']:.2f})",
                         f"{c['attempts']} ({f['gap']:.2f})",
                         f"{p['with_survivors']}/{p['closed']} · {p['rate']:.2f} "
                         f"[{p['low']:.2f}-{p['high']:.2f}]",
                         f"{c['ideas_spent']} ideas (×{f['brake']:.2f})",
                         "sin medir" if free else c["trades_per_year"],
                         ", ".join(warn) or "—"])
        parts.fill(self.board, rows)

    def press(self) -> None:
        """Show what a proposal costs; only «Sí» queues the director."""
        cost = self.fetch("research/direct").get("cost", "")
        if QMessageBox.question(self, "Proponer investigación", cost + "\n\n¿Lo lanzas?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        got = self.send("research/direct", {"confirmed": True})
        self.said.setText(got.get("error") or "; ".join(got.get("reasons", [])))
        self.poll()

    def poll(self) -> None:
        """Ask where the director is."""
        parts.call(self, lambda: self.fetch("research/direct"), self.state, "research-direct")

    def state(self, got: dict) -> None:
        """Paint the five steps, the running one marked; announce the proposal when it ends."""
        if "error" in got:
            self.said.setText(got["error"])
            return
        running, at = got["running"], (got.get("step") or {}).get("step", 0)
        self.button.setEnabled(not running)
        if running:
            self.steps.setText("<br>".join(
                f"{'✔' if n < at else '▶' if n == at else '·'} {n}. {name}"
                + (f" — {got['step'].get('note', '')}" if n == at else "")
                for n, name in enumerate(got["steps"], 1)))
            if not self.timer.isActive() and not self.sync:
                self.timer.start(POLL_MS)
        else:
            self.timer.stop()
            job = got.get("job")
            self.steps.setText("" if not job else
                               f"El director terminó: {job.get('state', '')} (rc {job.get('rc')}).")
            if self.was_running:
                self.proposed.emit()
        self.was_running = running
