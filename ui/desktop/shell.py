"""The window itself: grouped side navigation, the context bar, one zone inside, one status bar."""

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QStackedWidget, QTabBar,
                               QVBoxLayout, QWidget)

from ui.desktop import background, projectflow as flow
from ui.desktop.assets import Assets
from ui.desktop.catalogue import Catalogue
from ui.desktop.chat import Chat
from ui.desktop.cmdpalette import CmdPalette
from ui.desktop.contextbar import ContextBar
from ui.desktop.coverage import Matrix as Coverage
from ui.desktop.criteria.zone import CriteriaZone
from ui.desktop.datazone.zone import DataZone
from ui.desktop.nav import LIBRARY, TIPS, ZONES, sidebar
from ui.desktop.ops.jobsbar import JobsBar
from ui.desktop.ops.ledger import Ledger
from ui.desktop.ops.running import Running
from ui.desktop.palettes import Palettes
from ui.desktop.mt5bridge.zone import VerifyZone
from ui.desktop.portfolios.board import PortfoliosBoard
from ui.desktop.research.zone import ResearchZone
from ui.desktop.selection import SELECTION
from ui.desktop.shellopen import Opens
from ui.desktop.sqxconfig.zone import SqxConfigZone
from ui.desktop.theme import C
from ui.desktop.workspace.gallery import Gallery
from ui.desktop.workspace.zone import WorkspaceZone

class Said(QLabel):
    """The status line: it gives way to the jobs strip instead of widening the window.

    A plain label's minimum width is its whole sentence, and the status row set the window's:
    a long «carga pedida…» beside two job chips made it 1979 px wide on a 1920 screen
    (📓 2026-09-29). The sentence is clipped instead, and the whole of it is on hover.
    """

    def __init__(self) -> None:
        """An empty faint label that may shrink to nothing."""
        super().__init__("", objectName="faint")
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def setText(self, text: str) -> None:
        """Show the sentence and keep all of it in the tooltip."""
        super().setText(text)
        self.setToolTip(text)


class Shell(Opens, QWidget):
    """The single window. Everything else is a view inside it."""

    def __init__(self) -> None:
        """Build every zone, the sidebar, the context bar and the status bar, and wire them."""
        super().__init__()
        self.setWindowTitle("AlgoProject")
        self.resize(1440, 900)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.coverage = Coverage()
        self.catalogue = Catalogue()
        self.chat = Chat()
        self.palettes = Palettes()
        self.assets = Assets()
        self.ledger, self.running = Ledger(), Running()
        self.gallery, self.workspace = Gallery(), WorkspaceZone()
        self.estrategia = flow.StrategyZone()
        self.ficha = self.estrategia.ficha
        self.zones = {
            "Cobertura": self.coverage, "Plantillas": self.catalogue, "Nueva plantilla": self.chat,
            "Paletas": self.palettes, "Activos": self.assets, "Proyectos": self.gallery,
            "Proyecto": self.workspace, "Databanks": self.workspace.databanks,
            "Estrategia": self.estrategia,
            "En marcha": self.running, "Registro de búsquedas": self.ledger,
            "Configuración SQX": SqxConfigZone(), "Datos": DataZone(), "Investigar": ResearchZone(),
            "Portfolios": PortfoliosBoard(), "Verificar": VerifyZone(),
            "Criterios": CriteriaZone()}
        self.wire()

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.readonly = QLabel("Esta máquina no tiene SQX: modo lectura", objectName="readonly")
        self.readonly.hide()
        right.addWidget(self.readonly)
        self.context = ContextBar()
        self.context.zone.connect(self.open_zone)
        self.context.load.loaded.connect(self.data_landed)
        right.addWidget(self.context)
        self.stack = QStackedWidget()
        for name in ZONES:
            self.stack.addWidget(self.zones[name])
        body = QVBoxLayout()
        body.setContentsMargins(24, 14, 24, 8)
        # The library's pages, above whichever of them is open (`nav.LIBRARY`).
        self.library = QTabBar()
        self.library.setExpanding(False)
        for name in LIBRARY:
            self.library.setTabToolTip(self.library.addTab(name), TIPS[name])
        self.library.currentChanged.connect(lambda i: self.open_zone(LIBRARY[i]))
        body.addWidget(self.library)
        body.addWidget(self.stack, 1)
        right.addLayout(body, 1)
        foot = QHBoxLayout()
        foot.setContentsMargins(24, 0, 24, 8)
        self.status = Said()
        self.jobs = JobsBar()
        foot.addWidget(self.status, 1)
        foot.addWidget(self.jobs, 3)     # Ignored width (jobsbar): takes its share, never pushes
        right.addLayout(foot)
        # The sidebar is built after the stack because opening a zone needs the stack; it is
        # inserted first so it still sits down the left.
        # What «Recargar» reloads, by zone name: the zones that load once. Its tooltip is
        # written from these keys, so the button never promises a zone it does not reload.
        self.reloads = {"Cobertura": self.coverage.reload, "Plantillas": self.catalogue.reload,
                        "Paletas": self.palettes.reload, "Activos": self.assets.reload,
                        "Proyectos": self.gallery.load, "En marcha": self.running.reload,
                        "Verificar": self.verify_reload,
                        "Investigar": self.zones["Investigar"].reload}
        bar, self.nav = sidebar(self.open_zone, self.refresh, list(self.reloads))
        lay.insertWidget(0, bar)
        lay.addLayout(right, 1)
        # Each of them is read the first time it is opened, not before the window shows: read
        # all at once they held the window back ~6 s, Activos alone 5 (📓 2026-10-04). The
        # gallery is the exception — Ctrl+K lists its projects — and it reads off the GUI thread.
        self.stale = set(self.reloads) - {"Proyectos"}
        self.gallery.load()
        self.open_zone(ZONES[0])
        self.restate()
        background.get("health", lambda h: "sqx" in h and self.guard(h["sqx"]["installs"]),
                       owner=self)
        # The app's only shortcut. A text field that has the focus keeps Ctrl+K (Qt's «delete
        # to end of line»), the chat's answer box included: the palette never eats typing.
        self.cmdpalette = CmdPalette(self)
        QShortcut(QKeySequence("Ctrl+K"), self, self.cmdpalette.open)

    def verify_reload(self) -> None:
        """Reload Verificar and mark it loaded, so its `showEvent` does not read it a second time."""
        zone = self.zones["Verificar"]
        zone.loaded = True
        zone.reload()

    def wire(self) -> None:
        """Connect the zones that hand the owner on to another zone."""
        self.coverage.picked.connect(self.open_template)
        self.coverage.go.connect(self.open_library)
        self.chat.authored.connect(self.catalogue.reload)
        self.gallery.opened.connect(self.open_project)
        self.workspace.strategy_chosen.connect(self.open_strategy)
        self.workspace.databanks_wanted.connect(lambda: self.open_zone("Databanks"))
        self.zones["Portfolios"].import_requested.connect(self.open_archived)

    def data_landed(self, piece: str) -> None:
        """A piece of the selected databank finished loading: redraw what reads it.

        Args:
            piece: `metrics`, `trades` or `harvest`.
        """
        now = SELECTION.now
        if now["project"] and flow.SHOWN["Proyecto"] == now["project"]:
            self.workspace.fill(now["project"])
        if self.ficha.where and self.ficha.where.get("project") == now["project"]:
            self.ficha.reload()

    def guard(self, installs: dict[str, bool]) -> None:
        """Enter read-only mode when this machine has no SQX install at all.

        Args:
            installs: Role → whether its folder exists, from `/api/health`.

        The only button that reaches SQX today is the load bar's ↻ (a retry queues
        `orderstocsv` on the conductor); the automatic load finds no databank on any install
        and asks nothing. The button is disabled with its reason in its own text, because a
        disabled button never shows its tooltip; no zone is greyed out (encargo 22 §11).
        """
        found = ", ".join(role for role, ok in installs.items() if ok) or "ninguno"
        self.readonly.setToolTip(f"Installs de SQX encontrados en esta máquina: {found}. "
                                 "Se lee todo; nada que llegue a SQX se puede lanzar.")
        if any(installs.values()):
            return
        self.readonly.show()
        self.context.load.again.setEnabled(False)
        self.context.load.again.setText("↻ sin SQX: modo lectura")

    def open_zone(self, name: str) -> None:
        """Switch to a zone by the name the sidebar shows; Proyecto, Databanks and Estrategia
        first catch up with SELECTION when another zone changed it.

        Args:
            name: One of `nav.ZONES`; a desktop launcher opens the window straight on it
                (`bin/algoui --zone Proyectos`).
        """
        name, _, inner = name.partition(" · ")       # «Portfolios · Banco · VE(h)»: a module of the zone
        if inner:
            self.zones[name].open(*inner.split(" · "))
        # Databanks is filled by Proyecto's zone: one project, one fill, both zones.
        flow.catch_up(self, "Proyecto" if name == "Databanks" else name)
        if name in self.stale:           # its first opening, or the first since «Recargar»
            self.stale.discard(name)
            self.reloads[name]()
        self.stack.setCurrentWidget(self.zones[name])
        # A library page with no sidebar button of its own lights the library's.
        lit = name if name in self.nav else LIBRARY[0]
        for zone, b in self.nav.items():
            b.setChecked(zone == lit)
        self.library.setVisible(name in LIBRARY)
        if name in LIBRARY:
            self.library.blockSignals(True)
            self.library.setCurrentIndex(LIBRARY.index(name))
            self.library.blockSignals(False)

    def refresh(self) -> None:
        """Reload the zones that load once (`self.reloads`) and restate what is on screen.

        Proyecto, Databanks and Estrategia follow SELECTION and read on their own.
        """
        self.stale = set(self.reloads)
        self.open_zone(next(n for n in ZONES if self.zones[n] is self.stack.currentWidget()))
        self.restate()

    def restate(self) -> None:
        """Say in the status bar what the library's front page was read from."""
        totals = self.coverage.data
        self.status.setText(
            f"registry.csv · runs.csv · library/  —  {len(totals['rows'])} filas × "
            f"{len(totals['columns'])} timeframes  ·  daemon en 127.0.0.1")
        self.status.setStyleSheet(f"color:{C['faint']};")
