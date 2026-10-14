"""Proyectos: one card per project — symbol, timeframe, strategies, template, state (22 §3)."""

import httpx
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.desktop import background, client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.selection import SELECTION
from ui.desktop.workspace.card import CARD_MIN, Card
from ui.desktop.workspace.newproject import NewProject

PER_ROW = 4
NOTE = (
    "Una tarjeta por proyecto de cualquier install, tenga informes o no. Las estrategias son "
    "el total entre todos sus databanks. Clic en una tarjeta para abrir el proyecto entero."
)
# The three filters (owner, 2026-10-04): card field → what its combo says when it filters nothing.
FILTERS = {
    "symbol": "Todos los activos",
    "timeframe": "Todas las temporalidades",
    "install_label": "Todas las instalaciones",
}


RETIRED = "retirados"  # the daemon's `install_label` of a retired project


def passes(p: dict, chosen: dict[str, str]) -> bool:
    """Whether a card meets every filter that is set; an unset filter ("") lets all through.

    A retired project (only its reports remain) shows only when the install filter asks for it.
    """
    if p.get("install_label") == RETIRED and chosen.get("install_label") != RETIRED:
        return False
    return all(
        not want or (p.get(field) or "—") == want for field, want in chosen.items()
    )


class Gallery(QFrame):
    """The gallery: a kicker, one line on what a card counts, the cards in rows of four.

    `opened(name)` on a card click. The window calls `load`,
    which asks the daemon off the GUI thread (the first answer of a daemon hashes every
    strategy of every install, 12-25 s on 09-27/29, 0.13 s on 10-04) and fills it when the
    answer lands."""

    opened = Signal(str)

    def __init__(self) -> None:
        """Build it empty; `fill` or `load` brings the cards."""
        super().__init__()
        self.setObjectName("term")
        self.rows: dict[str, dict] = {}
        self.cards: list[Card] = []
        self.columns = 0
        kicker = QLabel(label("Proyectos"))
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
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        self.area = scroll
        scroll.viewport().installEventFilter(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 18, 24, 18)
        lay.addWidget(kicker)
        lay.addWidget(self.note)
        lay.addWidget(NewProject(lambda _name: self.load()))  # owner, 2026-09-28
        bar = QHBoxLayout()
        self.filters: dict[str, QComboBox] = {}
        for field, every in FILTERS.items():
            combo = QComboBox()
            combo.addItem(every, "")
            combo.setToolTip(
                "Se combina con los otros dos filtros: la galería enseña los "
                "proyectos que cumplen los tres a la vez."
            )
            combo.currentIndexChanged.connect(self.refilter)
            self.filters[field] = combo
            bar.addWidget(combo)
        self.shown = QLabel("")
        self.shown.setObjectName("dim")
        bar.addWidget(self.shown)
        bar.addStretch(1)
        lay.addLayout(bar)
        lay.addSpacing(10)
        lay.addWidget(scroll, 1)

    def fill(self, projects: list[dict]) -> None:
        """Lay out one card per project.

        Args:
            projects: `/api/projects/all` rows.
        """
        self.rows = {p["name"]: p for p in projects}
        for (
            field,
            combo,
        ) in self.filters.items():  # keep what was chosen across a reload
            kept = combo.currentData()
            combo.blockSignals(True)
            while combo.count() > 1:
                combo.removeItem(1)
            for value in sorted({p.get(field) or "—" for p in projects}):
                combo.addItem(value, value)
            combo.setCurrentIndex(max(0, combo.findData(kept)))
            combo.blockSignals(False)
        self.refilter()

    def refilter(self) -> None:
        """Lay out the cards of the projects that meet the three filters at once."""
        chosen = {field: combo.currentData() for field, combo in self.filters.items()}
        projects = [p for p in self.rows.values() if passes(p, chosen)]
        retired = sum(p.get("install_label") == RETIRED for p in self.rows.values())
        if chosen["install_label"] == RETIRED:
            self.shown.setText(
                f"{len(projects)} de {retired} proyectos retirados con informes"
            )
        else:
            self.shown.setText(
                f"{len(projects)} de {len(self.rows) - retired} proyectos"
                + (
                    f" · {retired} retirados con informes (filtro de instalación)"
                    if retired
                    else ""
                )
            )
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
        if ev.type() == QEvent.Type.Resize:
            self.lay_out()
        return False

    def load(self) -> None:
        """Ask the daemon for every project off the GUI thread; `landed` paints the answer."""
        self.note.setText(f"{NOTE}\nLeyendo los proyectos de los installs…")
        # The first answer of a fresh daemon hashes every strategy of every install: 25 s on
        # 2026-09-29, past the client's 20 s, and the gallery came up empty.
        background.get("projects/all", self.landed, key="gallery", wait=180)  # pyright: ignore[reportArgumentType]  # background.get/client.get type **params as str but forward wait to float

    def landed(self, got: dict) -> None:
        """Paint the daemon's answer, or say why there is none."""
        self.fill(got.get("projects", []))
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
            return f"{name}: elegido sin cargar" + (
                "" if full else " (ninguna databank tiene estrategias)"
            )
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
        listed = "\n".join(
            f"  · {d} ({num(self.rows[name]['databanks'][d])} estrategias)"
            for d in databanks
        )
        text = (
            f"Abrir {name} y cargar sus {len(databanks)} databanks con estrategias:\n\n"
            f"{listed}\n\nLas métricas se leen de los ficheros, sin SQX. Las operaciones y "
            "la cosecha se exportan con orderstocsv en el conductor, un trabajo detrás de "
            "otro (la franja de trabajos de abajo los muestra).\n\n"
            "«No» abre el proyecto sin cargar nada."
        )
        return (
            QMessageBox.question(self, "Cargar el proyecto", text)  # pyright: ignore[reportCallIssue]  # PySide6 stub wants button0/button1 for the 3-arg form
            == QMessageBox.StandardButton.Yes
        )
