"""The bottom strip of a project: the databank panel, SQX-style, with two rows of tabs."""

import httpx
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

from ui.desktop import client
from ui.text.numbers import num
from ui.desktop.theme import C
from ui.desktop.workspace.aggregate import Aggregate, ask
from ui.desktop.workspace.table import DataTable, pick
from ui.desktop.workspace.tabs import boxed, refill

class Panel(QFrame):
    """Header with the panel's own buttons, the two tab rows, then the sortable table beside
    the databank's aggregate equity. Double-clicking a row emits `strategy_chosen(identity)`;
    `run_tab(tab, databank, names)` asks the rail to run this tab. `live` is True once a
    project has been filled, which the filters strip and «Continuar» wait for."""

    strategy_chosen = Signal(str)
    folded = Signal(bool)
    run_tab = Signal(str, str, list)

    def __init__(self) -> None:
        """Build the header and the empty body; `fill` brings the tabs."""
        super().__init__()
        self.setObjectName("term")
        self.project, self.tabs, self.live, self.cache = "", [], False, {}
        head = QHBoxLayout()
        self.fold = QPushButton("▾ Plegar")
        self.fold.clicked.connect(self.toggle)
        kicker = QLabel("DATABANKS")
        kicker.setObjectName("kicker")
        head.addWidget(self.fold)
        head.addWidget(kicker)
        # The seal's sentence alone is ~3,000 px: wrapped and of ignored width, or it sets the
        # window's minimum width (3,867 px seen on 2026-09-28).
        self.said = QLabel("")
        self.said.setObjectName("dim")
        self.said.setWordWrap(True)
        self.said.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        head.addStretch(1)
        reload_, run = QPushButton("↻ Recargar databank"), QPushButton("▶ Correr marcados de "
                                                                        "este panel")
        reload_.setToolTip("Vuelve a leer del disco qué estrategias tiene el databank y pide lo "
                           "que le falte cargar (métricas, operaciones, cosecha).")
        reload_.clicked.connect(self.reload)
        run.clicked.connect(lambda: self.run_tab.emit(self.tab(), self.sub_spec().get(
            "databank", ""), self.table.chosen_names()))
        head.addWidget(reload_)
        head.addWidget(run)
        self.top, self.sub = boxed([]), boxed([], small=True)
        self.top.currentChanged.connect(self.open_top)
        self.sub.currentChanged.connect(self.open_sub)
        self.table = DataTable()
        self.table.chosen.connect(self.choose)
        self.body = QWidget()
        body = QHBoxLayout(self.body)
        body.setContentsMargins(0, 0, 0, 0)
        self.lock = QLabel("")
        self.lock.setObjectName("mono")
        self.lock.setWordWrap(True)
        self.lock.setAlignment(Qt.AlignTop)
        self.lock.setStyleSheet(f"color: {C['dead']}; font-size: 14px; padding: 16px;")
        self.side = Aggregate()
        body.addWidget(self.lock, 1)
        body.addWidget(self.table, 1)
        body.addWidget(self.side)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 8)
        lay.setSpacing(3)
        lay.addLayout(head)
        lay.addWidget(self.said)
        lay.addWidget(self.top)
        lay.addWidget(self.sub)
        lay.addWidget(self.body, 1)

    def fill(self, project: str) -> None:
        """Load one project's tabs from the daemon and open the first.

        Args:
            project: The project's name.
        """
        self.project, self.live, self.cache = project, True, {}
        got = ask("databank/panels", project=project)
        self.tabs = got.get("tabs", [])
        self.said.setText(got.get("error", ""))
        refill(self.top, [t["tab"] for t in self.tabs])
        self.open_top(0)
        # Fixed height, taken once they hold tabs: in a short strip the layout squeezed both
        # bars to 0 px and the table kept its rows. The table is what shrinks.
        for bar in (self.top, self.sub):
            bar.setFixedHeight(bar.sizeHint().height())

    def tab(self) -> str:
        """The top tab on screen."""
        return self.top.tabText(self.top.currentIndex())

    def sub_spec(self) -> dict:
        """The sub-panel on screen, as the daemon described it."""
        if not self.tabs:
            return {}
        return self.tabs[self.top.currentIndex()]["subs"][max(self.sub.currentIndex(), 0)]

    def select(self, tab: str, sub: str = "") -> None:
        """Bring one top tab forward, and one of its sub-panels — what a rail card asks for.

        Args:
            tab: The top tab; one the panel does not have is ignored.
            sub: The sub-panel, or '' (or one it does not have) for the tab's first.
        """
        names = [t["tab"] for t in self.tabs]
        if tab not in names:
            return
        self.top.setCurrentIndex(names.index(tab))
        subs = [s["sub"] for s in self.tabs[names.index(tab)]["subs"]]
        self.sub.setCurrentIndex(subs.index(sub) if sub in subs else 0)
        if self.fold.text().startswith("▸"):
            self.toggle()

    def open_top(self, index: int) -> None:
        """Show a top tab's sub-panels as the second row, and its first one."""
        if 0 <= index < len(self.tabs):
            refill(self.sub, [s["sub"] for s in self.tabs[index]["subs"]])
            self.open_sub(0)

    def payload(self, databank: str) -> dict:
        """A databank's table, read once per open project (↻ reads it again)."""
        if databank not in self.cache:
            self.cache[databank] = ask("databank/table", project=self.project,
                                       databank=databank)
        return self.cache[databank]

    def open_sub(self, index: int) -> None:
        """Fill the table and the aggregate for the chosen sub-panel."""
        if not self.tabs or index < 0:
            return
        spec = self.sub_spec()
        if spec["blocked"]:
            self.show_lock(f"BLOQUEADO — {spec['blocked']}\n\nEste panel no se lee ni se pinta "
                           "hasta entonces: ni tabla, ni curva, ni cifras.")
            return
        table = self.payload(spec["databank"])
        if "error" in table:
            self.show_lock(table["error"])
            return
        self.show_table(table, spec)
        self.side.load(self.project, spec["databank"], table["rows"], self.table.hidden)

    def show_lock(self, text: str) -> None:
        """Paint only a reason: a locked sub-panel, or a databank the daemon could not read."""
        self.lock.setText(text)
        self.said.setText("")
        for w, on in ((self.lock, True), (self.table, False), (self.side, False)):
            w.setVisible(on)

    def show_table(self, table: dict, spec: dict) -> None:
        """Paint the table of one sub-panel; the aggregate beside it is filled apart."""
        for w, on in ((self.lock, False), (self.table, True), (self.side, True)):
            w.setVisible(on)
        shown = pick(table["columns"], spec)
        n = self.table.paint(table["columns"], table["rows"], shown,
                             spec["studies"] != ["*"])
        notes = [f"{num(n)} estrategias en {spec.get('databank') or '—'}"]
        if table.get("rows_from") == "informes":
            notes.append("el databank ya no está en ningún install: filas de la cosecha y los "
                         "informes")
        if table.get("sealed"):
            notes.append("WFC, CSCV, WFM y paso 20 sellados por el ledger (el motivo, en el raíl "
                         "y en su pestaña)")
        if n == 0 and spec["studies"] != ["*"]:
            notes.append("ningún resultado de este estudio todavía")
        self.said.setText("  ·  ".join(notes))

    def choose(self, identity: object, name: str) -> None:
        """A row was double-clicked: its identity for the shell."""
        if identity:
            self.strategy_chosen.emit(identity)

    def refresh(self, _study: str = "", databank: str = "") -> None:
        """A study the rail ran has finished: read its databank again (every one when the rail
        does not say which) and repaint the sub-panel on screen."""
        same = databank.replace(" ", "_")
        self.cache = {k: v for k, v in self.cache.items()
                      if databank and k.replace(" ", "_") != same}
        self.side.forget()
        self.open_sub(self.sub.currentIndex())

    def set_hidden(self, identities: set[str]) -> None:
        """Hide these strategies' rows in every sub-panel — what a filter set aside (F6) — and
        aggregate only the visible ones."""
        self.table.set_hidden(identities)
        spec = self.sub_spec()
        if self.live and spec and spec["databank"] in self.cache and not spec["blocked"]:
            self.side.load(self.project, spec["databank"], self.cache[spec["databank"]]["rows"],
                           self.table.hidden)

    def reload(self) -> None:
        """«Recargar databank»: the daemon lists the folder again and loads what is missing."""
        bank = self.sub_spec().get("databank", "")
        if not bank:
            self.said.setText("Este panel no tiene databank que recargar.")
            return
        try:
            got = client.post("databank/reload", {"project": self.project, "databank": bank})
        except httpx.HTTPError as failed:
            self.said.setText(f"El demonio no respondió: {failed}")
            return
        self.cache.pop(bank, None)
        self.side.forget()
        self.open_sub(self.sub.currentIndex())
        queued = got["load"].get("queued") or []
        held = (f"{num(got['strategies'])} estrategias en disco" if got["strategies"] else
                f"{bank} no está en ningún install: las filas siguen siendo las de la cosecha "
                "y los informes")
        self.said.setText(f"Releído: {held}" + (f" · cargando {', '.join(queued)}" if queued
                                                 else ""))

    def toggle(self) -> None:
        """Fold the panel to its header, or unfold it; the zone gives the height back."""
        folding = self.body.isVisible()
        for w in (self.top, self.sub, self.body):
            w.setVisible(not folding)
        self.fold.setText("▸ Desplegar" if folding else "▾ Plegar")
        self.folded.emit(folding)
