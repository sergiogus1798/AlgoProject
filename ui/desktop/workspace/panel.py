"""The Databanks zone's panel: one project's databanks, SQX-style, with two rows of tabs."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QSplitter, QVBoxLayout, QWidget)

from ui.desktop import background
from ui.text.numbers import num
from ui.desktop.theme import C
from ui.desktop.workspace import columnsview, panelreload
from ui.desktop.workspace.texts import CHOOSER, TABLE_ONLY, informes
from ui.desktop.workspace.aggregate import Aggregate
from ui.desktop.workspace.table import DataTable
from ui.desktop.workspace.tabs import boxed, refill

SIDE = 0.5          # the equity's share of the split the first time it is shown


class Panel(QFrame):
    """Header with the panel's own buttons, the two tab rows, then the sortable table and the
    databank's aggregate equity on the two sides of a splitter the owner drags. Double-clicking
    a row emits `strategy_chosen(identity)`; `run_tab(tab, databank, names)` asks the rail to
    run this tab. `live` is True once a project has been filled (the filters strip and
    «Continuar» wait for it)."""

    strategy_chosen = Signal(str)
    run_tab = Signal(str, str, list)

    def __init__(self) -> None:
        """Build the header and the empty body; `fill` brings the tabs."""
        super().__init__()
        self.setObjectName("term")
        self.project, self.tabs, self.live, self.cache = "", [], False, {}
        self.dragged = False
        self.columns = columnsview.Views(self)
        head = QHBoxLayout()
        kicker = QLabel("DATABANKS", objectName="kicker")
        head.addWidget(kicker)
        # The seal's sentence alone is ~3,000 px: wrapped and of ignored width, or it sets the
        # window's minimum width (3,867 px seen on 2026-09-28).
        self.said = QLabel("", objectName="dim")
        self.said.setWordWrap(True)
        self.said.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        head.addStretch(1)
        reload_, run = QPushButton("↻ Recargar databank"), QPushButton("▶ Correr marcados de "
                                                                        "este panel")
        reload_.setToolTip("Relee del disco qué estrategias tiene el databank y pide lo que le "
                           "falte cargar (métricas, operaciones, cosecha).")
        reload_.clicked.connect(self.reload)
        pick = QPushButton("⚙ Métricas")     # a gear, as the owner asked (2026-09-28)
        pick.setToolTip(CHOOSER)                # the «?» reads it too: no registry entry
        pick.clicked.connect(lambda: self.say(self.columns.choose()))
        head.addWidget(pick)
        run.clicked.connect(lambda: self.run_tab.emit(self.tab(), self.sub_spec().get(
            "databank", ""), self.table.chosen_names()))
        head.addWidget(reload_)
        head.addWidget(run)
        self.top, self.sub = boxed([]), boxed([], small=True)
        self.top.currentChanged.connect(self.open_top)
        self.sub.currentChanged.connect(self.open_sub)
        self.table = DataTable()
        self.table.chosen.connect(self.choose)
        self.table.reordered.connect(lambda ids: self.say(self.columns.keep(ids)))
        left = QWidget()
        body = QVBoxLayout(left)
        body.setContentsMargins(0, 0, 0, 0)
        self.lock = QLabel("", objectName="mono")
        self.lock.setWordWrap(True)
        self.lock.setAlignment(Qt.AlignTop)
        self.lock.setStyleSheet(f"color: {C['dead']}; font-size: 14px; padding: 16px;")
        self.side = Aggregate()
        body.addWidget(self.lock, 1)
        body.addWidget(self.table, 1)
        left.setMinimumWidth(360)
        # Dragged both ways. Until the owner drags it, `resizeEvent` gives the equity SIDE of
        # the width; after, Qt keeps his split for the window's session.
        self.body = QSplitter(Qt.Horizontal)
        self.body.setChildrenCollapsible(False)
        self.body.setHandleWidth(7)
        self.body.addWidget(left)
        self.body.addWidget(self.side)
        self.body.splitterMoved.connect(lambda *_: setattr(self, "dragged", True))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 8)
        lay.setSpacing(3)
        lay.addLayout(head)
        lay.addWidget(self.said)
        lay.addWidget(self.top)
        lay.addWidget(self.sub)
        lay.addWidget(self.body, 1)

    def fill(self, project: str) -> None:
        """Load one project's tabs from the daemon, off the GUI thread, and open the first.

        Args:
            project: The project's name.
        """
        self.project, self.live, self.cache = project, True, {}
        self.columns.reset()
        background.get("databank/panels", lambda got: self.filled(project, got),
                       key=f"tabs:{id(self)}", owner=self, project=project)

    def filled(self, project: str, got: dict) -> None:
        """The project's tabs arrived: lay out both rows and open the first sub-panel."""
        if project != self.project:
            return
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

    def open_top(self, index: int) -> None:
        """Show a top tab's sub-panels as the second row, and its first one."""
        if 0 <= index < len(self.tabs):
            refill(self.sub, [s["sub"] for s in self.tabs[index]["subs"]])
            self.open_sub(0)

    def open_sub(self, index: int) -> None:
        """Fill the table and the aggregate for the chosen sub-panel: at once from the cache
        (one read per databank per open project, ↻ reads it again), else off the GUI thread."""
        if not self.tabs or index < 0:
            return
        spec = self.sub_spec()
        if spec["blocked"]:
            self.show_lock(f"BLOQUEADO — {spec['blocked']}\n\nEste panel no se lee ni se pinta "
                           "hasta entonces: ni tabla, ni curva, ni cifras.")
            return
        bank, project = spec["databank"], self.project
        if bank in self.cache:
            self.show_payload(spec, self.cache[bank])
            return
        self.said.setText(f"Leyendo {bank}…")
        background.get("databank/table", lambda got: self.landed(project, spec, got),
                       key=f"panel:{id(self)}", owner=self, project=project, databank=bank)

    def landed(self, project: str, spec: dict, table: dict) -> None:
        """A databank's table arrived: keep it (not a failure) and paint it if still on screen."""
        if project != self.project:
            return
        if "error" not in table:
            self.cache[spec["databank"]] = table
        if self.sub_spec() is spec:
            self.show_payload(spec, table)

    def show_payload(self, spec: dict, table: dict) -> None:
        """Paint one sub-panel's table and its aggregate, or the reason there is none."""
        if "error" in table:
            self.show_lock(table["error"])
            return
        if not table.get("rows"):   # an empty databank, or an export with nothing in it
            self.show_lock(f"Sin datos — «{spec.get('databank') or '—'}» no tiene ninguna "
                           "estrategia (vacío en el worker, o su export sin columnas). Elige "
                           "otro databank arriba.", error=False)
            return
        self.show_table(table, spec)
        if self.tab() not in TABLE_ONLY:
            self.side.load(self.project, spec["databank"], table["rows"], self.table.hidden)

    def show_lock(self, text: str, error: bool = True) -> None:
        """Paint only a reason: a locked sub-panel, a databank the daemon could not read, or
        (`error` False, not in red) an empty one. The tab rows stay: another is one click."""
        self.lock.setStyleSheet(f"color: {C['dead'] if error else C['muted']}; "
                                "font-size: 14px; padding: 16px;")
        self.lock.setText(text)
        self.said.setText("")
        for w, on in ((self.lock, True), (self.table, False), (self.side, False)):
            w.setVisible(on)

    def show_table(self, table: dict, spec: dict) -> None:
        """Paint the table of one sub-panel; the aggregate beside it is filled apart."""
        for w, on in ((self.lock, False), (self.table, True), (self.side, self.tab() not in TABLE_ONLY)):
            w.setVisible(on)
        n = self.table.paint(table["rows"], *self.columns.view(table, spec))
        notes = [f"{num(n)} estrategias en {spec.get('databank') or '—'}"]
        if table.get("rows_from") == "informes":
            notes.append(informes(table))
        if table.get("sealed"):
            notes.append("WFC, CSCV, WFM y paso 20 sellados por el ledger (el motivo, en el raíl "
                         "y en su pestaña)")
        if n == 0 and spec["studies"] != ["*"]:
            notes.append("ningún resultado de este estudio todavía")
        self.said.setText("  ·  ".join(notes))

    def resizeEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Until the owner drags the splitter, the equity keeps SIDE of the width."""
        super().resizeEvent(event)
        if not self.dragged:
            w = self.body.width()
            self.body.setSizes([round(w * (1 - SIDE)), round(w * SIDE)])

    def say(self, text: str) -> None:
        """A line under the header, when there is something to say."""
        self.said.setText(text or self.said.text())

    def choose(self, identity: object, name: str) -> None:
        """A row was double-clicked: its identity for the shell."""
        identity and self.strategy_chosen.emit(identity)

    def refresh(self, _study: str = "", databank: str = "") -> None:
        """A study the rail ran has finished: read its databank again (every one when the rail
        does not say which) and repaint the sub-panel on screen."""
        same = databank.replace(" ", "_")
        self.cache = {k: v for k, v in self.cache.items()
                      if databank and k.replace(" ", "_") != same}
        self.columns.forget()
        self.side.forget()
        self.open_sub(self.sub.currentIndex())

    def set_hidden(self, identities: set[str]) -> None:
        """Hide these strategies' rows in every sub-panel — what a filter set aside (F6) — and
        aggregate only the visible ones."""
        self.table.set_hidden(identities)
        spec = self.sub_spec()
        if (self.live and spec and spec["databank"] in self.cache and not spec["blocked"]
                and self.tab() not in TABLE_ONLY):
            self.side.load(self.project, spec["databank"], self.cache[spec["databank"]]["rows"],
                           self.table.hidden)

    def reload(self) -> None:
        """«Recargar databank» (`panelreload`): the daemon lists the folder again, off the GUI
        thread, and the sub-panel is read again when it answers."""
        panelreload.ask(self)
