"""Proyectos: one card per project — symbol, timeframe, strategies, template, state (22 §3)."""

import threading

import httpx
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QFrame, QGridLayout, QLabel, QMessageBox, QScrollArea,
                               QVBoxLayout, QWidget)

from ui.desktop import client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.selection import SELECTION
from ui.desktop.theme import C, T
from ui.desktop.workspace.newproject import NewProject

CARD_MIN = 300    # px a card needs for its longest line; the row holds as many as fit, up to 4
PER_ROW = 4
STATE_INK = {"corriendo": C["accent"], "terminado": C["promising"], "construido": C["weak"],
             "parado": C["dead"], "ausente": C["faint"]}
STATE_HELP = {"corriendo": "SQX lo está corriendo ahora (leído con action=status).",
              "terminado": "La última tarea terminó: «Project finished» en el log de SQX.",
              "construido": "El proyecto existe pero ninguna tarea ha corrido todavía.",
              "parado": "Se paró antes de terminar su tarea.",
              "ausente": "Ya no está en ningún install; quedan sus informes."}
NOTE = ("Una tarjeta por proyecto de cualquier install, tenga informes o no. Las estrategias son "
        "el total entre todos sus databanks. Clic en una tarjeta para abrir el proyecto entero.")


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
        lay.addWidget(line(f"● {p['state'].upper()}", "mono", f"color: {ink};"))
        lay.addWidget(line(f"en el {where}", "dim"))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Open the project.

        Args:
            event: Qt's mouse event, unused.
        """
        self.opened.emit(self.name)


class Gallery(QFrame):
    """The gallery: a kicker, one line on what a card counts, the cards in rows of four.

    `opened(name)` on a card click. The window calls `load`,
    which asks the daemon off the GUI thread (the first answer of a daemon hashes every
    strategy of every install, 12-25 s) and fills it when the answer lands."""

    opened = Signal(str)
    arrived = Signal(dict)

    def __init__(self) -> None:
        """Build it empty; `fill` or `load` brings the cards."""
        super().__init__()
        self.setObjectName("term")
        self.rows: dict[str, dict] = {}
        self.cards: list[Card] = []
        self.columns = 0
        kicker = QLabel(label("PROYECTOS"))
        kicker.setObjectName("kicker")
        self.note = QLabel(NOTE)
        self.note.setObjectName("dim")
        self.note.setWordWrap(True)
        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        holder = QWidget()
        inner = QVBoxLayout(holder)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.addLayout(self.grid)
        inner.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        self.area = scroll
        scroll.viewport().installEventFilter(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.addWidget(kicker)
        lay.addWidget(self.note)
        lay.addWidget(NewProject(lambda _name: self.load()))   # owner, 2026-09-28
        lay.addSpacing(10)
        lay.addWidget(scroll, 1)
        self.arrived.connect(self.landed)

    def fill(self, projects: list[dict]) -> None:
        """Lay out one card per project.

        Args:
            projects: `/api/projects/all` rows.
        """
        self.rows = {p["name"]: p for p in projects}
        while self.grid.count():
            self.grid.takeAt(0).widget().deleteLater()
        self.cards = [Card(p) for p in projects]
        for card in self.cards:
            card.opened.connect(self.opened)
        self.columns = 0
        self.lay_out()

    def lay_out(self) -> None:
        """Put the cards in as many columns as the viewport holds (1 to 4), only when it changes."""
        columns = max(1, min(PER_ROW, self.area.viewport().width() // CARD_MIN))
        if columns == self.columns:
            return
        self.columns = columns
        for i, card in enumerate(self.cards):
            self.grid.addWidget(card, i // columns, i % columns)
        for col in range(PER_ROW):
            self.grid.setColumnStretch(col, 1 if col < columns else 0)

    def eventFilter(self, obj: QObject, ev: QEvent) -> bool:
        """Re-flow the cards when the scroll viewport is resized."""
        if ev.type() == QEvent.Resize:
            self.lay_out()
        return False

    def load(self) -> None:
        """Ask the daemon for every project in a thread; `landed` paints the answer."""
        self.note.setText(f"{NOTE}\nLeyendo los proyectos de los installs…")
        threading.Thread(target=self.ask, daemon=True).start()

    def ask(self) -> None:
        """The request itself, off the GUI thread; the signal crosses back to it."""
        try:
            # The first answer of a fresh daemon hashes every strategy of every install: 25 s
            # on 2026-09-29, past the client's 20 s, and the gallery came up empty.
            got = client.get("projects/all", wait=180)
        except httpx.HTTPError as e:
            got = {"projects": [], "error": f"El demonio no respondió: {e}"}
        self.arrived.emit(got)

    def landed(self, got: dict) -> None:
        """Paint the daemon's answer, or say why there is none."""
        self.fill(got["projects"])
        self.note.setText(NOTE + (f"\n{got['error']}" if got.get("error") else ""))

    def choose(self, name: str) -> str:
        """Make one project the global selection and, if the owner confirms, load its databanks.

        Args:
            name: The project, as a card or the palette names it.

        Returns:
            One sentence for the status bar. Confirmed: every databank with strategies is
            loaded (`POST /api/load`: metrics off the files, trades and cosecha as
            `orderstocsv` on the conductor, one at a time) and the first of them becomes the
            selected databank. Cancelled: only the project is selected — not a databank either,
            since choosing one loads it (the load bar).
        """
        p = self.rows.get(name)
        if p is None:
            return f"{name}: la galería aún no tiene sus datos; ábrelo desde Proyectos."
        full = [d for d, n in p.get("databanks", {}).items() if n]
        if not full or not self.confirm(name, full):
            SELECTION.choose(project=name, asset=p["symbol"])
            return f"{name}: elegido sin cargar" + ("" if full else " (ninguna databank tiene "
                                                                    "estrategias)")
        failed = []
        for databank in full:
            try:
                client.post("load", {"project": name, "databank": databank})
            except httpx.HTTPError:
                failed.append(databank)
        SELECTION.choose(project=name, asset=p["symbol"], databank=full[0])
        said = f"{name}: carga pedida para {len(full) - len(failed)} de {len(full)} databanks"
        return said + (f" · el demonio no aceptó {', '.join(failed)}" if failed else "")

    def confirm(self, name: str, databanks: list[str]) -> bool:
        """Ask before queuing the loads: they run SQX on the conductor, one export at a time."""
        listed = "\n".join(f"  · {d} ({num(self.rows[name]['databanks'][d])} estrategias)"
                           for d in databanks)
        text = (f"Abrir {name} y cargar sus {len(databanks)} databanks con estrategias:\n\n"
                f"{listed}\n\nLas métricas se leen de los ficheros, sin SQX. Las operaciones y "
                "la cosecha se exportan con orderstocsv en el conductor, un trabajo detrás de "
                "otro (la franja de trabajos de abajo los muestra).\n\n"
                "«No» abre el proyecto sin cargar nada.")
        return QMessageBox.question(self, "Cargar el proyecto", text) == QMessageBox.Yes
