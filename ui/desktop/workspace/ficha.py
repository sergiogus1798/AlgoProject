"""Estrategia: the fixed basic panel, the family tabs and the metadata of one strategy (22 §5)."""

import threading

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout,
                               QWidget)

from ui.desktop.selection import SELECTION
from ui.desktop.studypage.net import fetch, send
from ui.desktop.studypage.views import StrategyPage
from ui.desktop.theme import C, T
from ui.desktop.workspace import fichaarchive
from ui.desktop.workspace.fichacurves import CostCurves
from ui.desktop.workspace.fichajobs import Compute
from ui.desktop.workspace.fichameta import Meta
from ui.desktop.workspace.fichastats import Stats
from ui.desktop.workspace.texts import FAMILIES as SHORT

# Which family tab opens first, by the databank panel the page was opened from.
ORIGIN_FAMILY = {"Puerta IS/OOS": "Cribado", "Cross Market": "Transferencia",
                 "Cross Timeframe": "Transferencia", "MC Retest": "Rotura", "SPP": "Optimización",
                 "WFC": "Optimización", "CSCV": "Optimización", "Market Surfaces": "Optimización",
                 "WFM": "Cierre", "Cierre": "Cierre"}


class Ficha(QFrame):
    """The strategy page. The top panel is the same in every databank and folds; below it,
    the study page's family tabs, opened on the family of the databank panel it came from,
    and the metadata column. `arrived` carries the daemon's answers back to the GUI thread."""

    arrived = Signal(dict)
    archived = Signal(dict)

    def __init__(self) -> None:
        """Build the empty page; `fill` loads a strategy."""
        super().__init__()
        self.setObjectName("term")
        self.where: dict = {}
        self.data: dict = {}
        self.opened_from = ""
        self.page = None                      # the studypage, built on the first real strategy
        self.compute = Compute()
        self.compute.said.connect(self.say)
        self.compute.done.connect(self.reload)
        self.arrived.connect(self.paint)
        self.archived.connect(self.after_archive)
        self.title = QLabel("", objectName="h1")
        self.title.setStyleSheet("font-size: 20px;")
        self.origin = QLabel("", objectName="dim")
        self.said = QLabel("", objectName="dim")
        self.said.setStyleSheet(f"color: {C['accent']};")
        self.keep = QPushButton("Archivar")
        self.keep.setToolTip(fichaarchive.WHAT)
        self.keep.clicked.connect(self.archive)
        self.fold = QPushButton("▾ plegar panel básico")
        self.fold.clicked.connect(self.toggle)
        head = QHBoxLayout()
        for w in (self.title, self.origin):
            head.addWidget(w)
        head.addStretch(1)
        for w in (self.said, self.keep, self.fold):
            head.addWidget(w)
        self.curves, self.stats = CostCurves(self.compute), Stats(self.compute)
        self.basic = QFrame(objectName="basic")
        self.basic.setStyleSheet(f"QFrame#basic {{ border-bottom: 1px solid {T['rule']}; }}")
        row = QHBoxLayout(self.basic)
        row.setContentsMargins(0, 4, 0, 8)
        row.addWidget(self.curves, 4)
        row.addSpacing(16)
        row.addWidget(self.stats, 5)
        self.short = QLabel("", objectName="mono")
        self.short.setStyleSheet("font-size: 13px;")
        self.family = QVBoxLayout()
        self.family.addWidget(self.short)
        self.family.addStretch(0)            # the page, once built, takes it all
        self.meta = Meta()
        lower = QWidget()
        low = QHBoxLayout(lower)
        low.setContentsMargins(0, 6, 0, 0)
        low.addLayout(self.family, 3)
        low.addWidget(self.meta, 1)
        self.split = QSplitter(Qt.Vertical)
        self.split.addWidget(self.basic)
        self.split.addWidget(lower)
        self.split.setSizes([520, 480])
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.addLayout(head)
        lay.addWidget(self.split, 1)

    def fill(self, project: str, name: str, databank: str) -> None:
        """Load one strategy from the daemon, off the GUI thread.

        Args:
            project: Its project.
            name: Its name in the databank.
            databank: The panel it was opened from, which chooses the family tab.
        """
        now = SELECTION.now
        self.opened_from = databank
        self.where = {"project": project, "strategy": name, "databank": now["databank"] or "",
                      "identity": now["identity"] or "", "asset": now["asset"] or ""}
        self.compute.where = self.where
        self.title.setText(name)
        self.origin.setText(f"   abierta desde {databank}   ·   {project}"
                            + (f"   ·   {self.where['databank']}" if self.where["databank"] else ""))
        self.lower(True, ORIGIN_FAMILY.get(databank, "Ficha"))
        self.say("leyendo la estrategia…")
        threading.Thread(target=self.ask, args=(dict(self.where),), daemon=True).start()

    def ask(self, where: dict) -> None:
        """Off the GUI thread: the three reads of the page, then `arrived`."""
        q = {k: where[k] for k in ("project", "databank", "identity")}
        self.arrived.emit({"key": (where["project"], where["strategy"]),
                           "curve": fetch("strategy/costcurve", **q),
                           "stats": fetch("strategy/stats", **q),
                           "meta": fetch("strategy/meta", **q)})

    def paint(self, got: dict) -> None:
        """Paint what `ask` brought, unless another strategy was chosen since."""
        if got["key"] != (self.where["project"], self.where["strategy"]):
            return
        self.data = got
        if not self.where["asset"]:
            self.where["asset"] = got["curve"].get("asset") or ""
        self.curves.fill(got["curve"])
        self.stats.fill(got["stats"])
        self.meta.fill(got["meta"])
        self.say("")

    def lower(self, live: bool, family: str) -> None:
        """Below the panel: the study page, opened on the origin's family.

        Args:
            live: False in a subclass that shows no study tabs (PORTFOLIOS' archived page
                overrides this method); the live ficha always passes True.
            family: The family tab to open.
        """
        if live and self.page is None:
            self.page = StrategyPage()
            self.page.families.currentChanged.connect(self.describe)
            self.family.addWidget(self.page, 1)
        if self.page is not None:
            self.page.setVisible(live)
            if live:
                self.page.open_family(family)
        self.describe()

    def describe(self, *_: object) -> None:
        """The chosen family's one-line description, above its tabs."""
        if self.page is not None:
            bar = self.page.families
            family = bar.tabText(bar.currentIndex())
            self.short.setText(f"{family}: {SHORT[family]}" if family in SHORT else "")

    def reload(self) -> None:
        """A «calcular» ended: read the page again."""
        self.fill(self.where["project"], self.where["strategy"], self.opened_from)

    def say(self, text: str) -> None:
        """The line at the top right: what the page is doing or what came of a button."""
        self.said.setText(text)

    def archive(self) -> None:
        """Ask the note and the step, then freeze the strategy off the GUI thread."""
        asked = fichaarchive.ask(self, self.where["strategy"])
        if asked is None:
            return self.say("archivo cancelado")
        if "error" in asked:
            return self.say(asked["error"])
        self.say("archivando…")
        body = {k: self.where[k] for k in ("project", "databank", "identity")} | asked
        threading.Thread(target=lambda: self.archived.emit(send("strategy/archive", body)),
                         daemon=True).start()

    def after_archive(self, got: dict) -> None:
        """Say where the version went, or why it did not."""
        self.say(got["error"] if "error" in got else
                 f"archivada: versión {got['version']} ({got['origin']})")

    def toggle(self) -> None:
        """Fold the basic panel away, or bring it back."""
        folding = self.basic.isVisible()
        self.basic.setVisible(not folding)
        self.fold.setText("▸ desplegar panel básico" if folding else "▾ plegar panel básico")
