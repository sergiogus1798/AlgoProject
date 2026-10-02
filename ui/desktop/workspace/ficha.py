"""Estrategia: the fixed basic panel and the family tabs of one strategy (22 §5); its metadata on a button."""

import threading

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSplitter,
                               QVBoxLayout, QWidget)

from ui.desktop.selection import SELECTION
from ui.desktop.studypage.net import fetch, send
from ui.desktop.studypage.offer import OFF
from ui.desktop.studypage.views import StrategyPage
from ui.desktop.theme import C, T
from ui.desktop.workspace import fichaarchive
from ui.desktop.workspace.fichacurves import CostCurves
from ui.desktop.workspace.fichajobs import Compute
from ui.desktop.workspace.fichameta import MetaWindow
from ui.desktop.workspace.fichaorigin import ORIGIN_FAMILY, default_study
from ui.desktop.workspace.fichastats import Stats
from ui.desktop.workspace.texts import FAMILIES as SHORT


class Ficha(QFrame):
    """The strategy page. The top panel is the same in every databank and folds; below it,
    the study page's family tabs, opened on the family of the databank panel it came from, on
    the whole width — the metadata open in their own window from «ⓘ metadatos» (owner,
    2026-09-30). `arrived` carries the daemon's answers back to the GUI thread."""

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
        self.info = QPushButton("metadatos")
        self.info.setProperty("help", "Abre en una ventana aparte lo que el .sqx dice de la "
                              "estrategia: condiciones, órdenes, money management, activo y los "
                              "costes de su último test.")
        self.info.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.info.clicked.connect(self.show_meta)
        self.metawin = MetaWindow(self)
        head = QHBoxLayout()
        for w in (self.title, self.origin):
            head.addWidget(w)
        head.addStretch(1)
        for w in (self.said, self.keep, self.fold, self.info):
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
        lower = QWidget()
        low = QHBoxLayout(lower)
        low.setContentsMargins(0, 6, 0, 0)
        low.addLayout(self.family, 1)
        # Each side scrolls: unwrapped they asked 549 + 550 px and the window grew to 1,239 px,
        # past a 1080-px screen (2026-09-28). Wrapped, the splitter takes height from either.
        self.split = QSplitter(Qt.Vertical)
        for part in (self.basic, lower):
            area = QScrollArea(widgetResizable=True, frameShape=QFrame.NoFrame)
            area.setWidget(part)
            self.split.addWidget(area)
        self.split.setSizes([520, 480])
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.addLayout(head)
        lay.addWidget(self.split, 1)

    def fill(self, project: str, name: str, databank: str, sub: str = "") -> None:
        """Load one strategy from the daemon, off the GUI thread.

        Args:
            project: Its project.
            name: Its name in the databank.
            databank: The panel it was opened from, which chooses the family tab.
            sub: The panel's open sub-panel, which can choose the study tab too (§4.3/§9.4:
                a Cross Market strategy opens on Cross Market, not Cross Timeframe; a Mapa
                condicional one opens on the conditional map, not Exposición).
        """
        now = SELECTION.now
        self.opened_from = databank
        self.where = {"project": project, "strategy": name, "databank": now["databank"] or "",
                      "identity": now["identity"] or "", "asset": now["asset"] or ""}
        self.compute.where = self.where
        self.title.setText(name)
        self.origin.setText(f"   abierta desde {databank}   ·   {project}"
                            + (f"   ·   {self.where['databank']}" if self.where["databank"] else ""))
        self.lower(True, ORIGIN_FAMILY.get(databank, "Ficha"), default_study(databank, sub))
        self.say("leyendo la estrategia…")
        threading.Thread(target=self.ask, args=(dict(self.where),), daemon=True).start()

    def ask(self, where: dict) -> None:
        """Off the GUI thread: the three reads of the page, then `arrived`."""
        q = {k: where[k] for k in ("project", "databank", "identity")}
        # The name pairs a databank with no cosecha (MCR_All, an ingest) to the project's own.
        named = q | {"strategy": where["strategy"]}
        self.arrived.emit({"key": (where["project"], where["strategy"]),
                           "curve": fetch("strategy/costcurve", **named),
                           "stats": fetch("strategy/stats", **named),
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
        self.metawin.fill(got["meta"], self.where["strategy"])
        self.say(got["curve"].get("note") or "")      # where a borrowed cosecha came from

    def lower(self, live: bool, family: str, study: str | None = None) -> None:
        """Below the panel: the study page, opened on the origin's study (or its family alone).

        Args:
            live: False in a subclass that shows no study tabs (PORTFOLIOS' archived page
                overrides this method); the live ficha always passes True.
            family: The family tab to open when `study` names none, or is not on this page.
            study: A catalogue key to open directly (`default_study`), None for `family` alone.
        """
        if live and self.page is None:
            self.page = StrategyPage()
            self.page.families.currentChanged.connect(self.describe)
            self.page.offer.jump.connect(self.jump)
            self.family.addWidget(self.page, 1)
        if self.page is not None:
            self.page.setVisible(live)
            if live:
                if study and study in self.page.catalogue:
                    self.page.open_study(study)
                else:
                    self.page.open_family(family)
        self.describe()

    def describe(self, *_: object) -> None:
        """The chosen family's one-line description, above its tabs; the basic panel (general
        strategy data — the price curve and its stats) folds away outside the Ficha (owner,
        2026-09-29): Transferencia's own studies get that space instead, and general data
        stays where it belongs, the Ficha, rather than repeating on every family tab."""
        if self.page is not None:
            bar = self.page.families
            family = bar.tabText(bar.currentIndex()).removesuffix(OFF)
            self.short.setText(f"{family}: {SHORT[family]}" if family in SHORT else "")
            basic = self.split.widget(0)
            basic.setVisible(family == "Ficha")
            self.fold.setVisible(family == "Ficha")

    def jump(self, study: str, go: dict) -> None:
        """«→ abrir en …»: the strategy of the same name in the databank a test lives in,
        opened on that test — the owner's choice, by name (the identity there may differ).

        Args:
            study: The study key to open there.
            go: `/api/study/offer`'s `databank`, `tab`, `strategy`, `identity`.
        """
        SELECTION.choose(databank=go["databank"], strategy=go["strategy"],
                         identity=go["identity"])
        self.fill(self.where["project"], go["strategy"], go["tab"])
        self.page.open_study(study)

    def show_meta(self) -> None:
        """Open the metadata window, or bring it forward when it is already open."""
        if not self.data:
            return self.say("aún leyendo la estrategia…")
        self.metawin.show()
        self.metawin.raise_()
        self.metawin.activateWindow()

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
        folding = self.split.widget(0).isVisible()      # the basic panel's scroll area
        self.split.widget(0).setVisible(not folding)
        self.fold.setText("▸ desplegar panel básico" if folding else "▾ plegar panel básico")
