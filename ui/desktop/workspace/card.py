"""One project's card in the Proyectos gallery."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ui.desktop.theme import C, T
from ui.text.glossary import label
from ui.text.numbers import num

CARD_MIN = 300    # px a card needs for its longest line; the row holds as many as fit, up to 4
STATE_INK = {"corriendo": C["accent"], "terminado": C["promising"], "construido": C["weak"],
             "parado": C["dead"], "ausente": C["faint"]}
STATE_HELP = {"corriendo": "SQX lo está corriendo ahora (leído con action=status).",
              "terminado": "La última tarea terminó: «Project finished» en el log de SQX.",
              "construido": "El proyecto existe pero ninguna tarea ha corrido todavía.",
              "parado": "Se paró antes de terminar su tarea.",
              "ausente": "Ya no está en ningún install; quedan sus informes."}


def line(text: str, name: str, css: str = "") -> QLabel:
    """One line of a card in a term style, with extra css when it needs it."""
    got = QLabel(text)
    got.setObjectName(name)
    got.setStyleSheet(css)
    return got


class Card(QFrame):
    """One project. A click anywhere on it emits `opened(name)`."""

    opened = Signal(str)

    def __init__(self, p: dict) -> None:
        """Build the card from one `/api/projects/all` row."""
        super().__init__()
        self.name = p["name"]
        ink = STATE_INK[p["state"]]
        where = p.get("install_label") or p["install"]
        self.setObjectName("card")
        self.setStyleSheet(f"QFrame#card {{ border: 1px solid {T['rule']}; border-radius: 6px; }}"
                           f"QFrame#card:hover {{ border-color: {C['accent']}; }}")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("\n".join(x for x in (p["name"], p.get("why") or STATE_HELP[p["state"]],
                                              p.get("purpose"), f"Install: {where}") if x))
        self.setMinimumHeight(170)
        self.setMinimumWidth(CARD_MIN - 40)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(4)
        lay.addWidget(line(f"{p['symbol'] or '—'}  ·  {p['timeframe'] or '—'}", "figure",
                           "font-size: 22px;"))
        lay.addWidget(line(p["name"], "dim"))
        lay.addSpacing(6)
        lay.addWidget(line(f"{label('estrategias')}  {num(p['strategies'])}", "mono",
                           "font-size: 14px;"))
        lay.addWidget(line(f"{label('plantilla')}  {p['template'] or 'sin plantilla registrada'}",
                           "mono"))
        live = p.get("live")
        if live:
            lay.addWidget(line(f"{label('procesadas')}  {num(live['generated'])}  ·  "
                               f"{live['running']}", "dim"))
        lay.addStretch(1)
        lay.addWidget(line(f"● {p['state'].capitalize()}", "mono", f"color: {ink};"))
        lay.addWidget(line(f"en el {where}", "dim"))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Open the project.

        Args:
            event: Qt's mouse event, unused.
        """
        self.opened.emit(self.name)
