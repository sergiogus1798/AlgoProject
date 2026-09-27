"""The window itself: grouped side navigation, the context bar, one zone inside, one status bar."""

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from ui.desktop.assets import Assets
from ui.desktop.catalogue import Catalogue
from ui.desktop.chat import Chat
from ui.desktop.cmdpalette import CmdPalette
from ui.desktop.contextbar import ContextBar
from ui.desktop.coverage import Matrix as Coverage
from ui.desktop.gate import Gate
from ui.desktop.generation import Generation
from ui.desktop.matrix.view import Matrix
from ui.desktop.nav import ZONES, sidebar
from ui.desktop.ops.jobsbar import JobsBar
from ui.desktop.ops.ledger import Ledger
from ui.desktop.ops.pulse import Pulse
from ui.desktop.palettes import Palettes
from ui.desktop.selection import SELECTION
from ui.desktop.soon import ZONES as SOON, page as soon_page
from ui.desktop.studies import Studies
from ui.desktop.studypage.views import PopulationStudy, StrategyPage
from ui.desktop.theme import C
from ui.desktop.workflow.rail import WorkflowRail


class Shell(QWidget):
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
        self.rail = WorkflowRail()
        self.population = Matrix()
        self.popstudy = PopulationStudy()
        self.strategy = StrategyPage()
        self.studies = Studies()
        self.gate = Gate()
        self.pulse = Pulse()
        self.ledger = Ledger()
        self.generation = Generation()
        self.zones = {
            "Cobertura": self.coverage, "Plantillas": self.catalogue, "Nueva plantilla": self.chat,
            "Paletas": self.palettes, "Activos": self.assets, "Workflow": self.rail,
            "Población": self.population, "Estudio de población": self.popstudy,
            "Estrategia": self.strategy, "Estrategias": self.studies, "Puerta IS/OOS": self.gate,
            "Custodio": self.pulse, "Ledger": self.ledger, "Generación": self.generation,
            **{name: soon_page(name) for name in SOON}}
        self.wire()

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.context = ContextBar()
        self.context.zone.connect(self.open_zone)
        self.context.load.loaded.connect(self.data_landed)
        right.addWidget(self.context)
        self.stack = QStackedWidget()
        for name in ZONES:
            self.stack.addWidget(self.zones[name])
        body = QVBoxLayout()
        body.setContentsMargins(24, 14, 24, 8)
        body.addWidget(self.stack, 1)
        right.addLayout(body, 1)
        foot = QHBoxLayout()
        foot.setContentsMargins(24, 0, 24, 8)
        self.status = QLabel("", objectName="faint")
        self.jobs = JobsBar()
        foot.addWidget(self.status)
        foot.addStretch()
        foot.addWidget(self.jobs)
        right.addLayout(foot)
        # The sidebar is built after the stack because opening a zone needs the stack; it is
        # inserted first so it still sits down the left.
        bar, self.nav = sidebar(self.open_zone, self.refresh)
        lay.insertWidget(0, bar)
        lay.addLayout(right, 1)
        self.open_zone(ZONES[0])
        self.refresh()
        # The app's only shortcut. A text field that has the focus keeps Ctrl+K (Qt's «delete
        # to end of line»), the chat's answer box included: the palette never eats typing.
        self.cmdpalette = CmdPalette(self)
        QShortcut(QKeySequence("Ctrl+K"), self, self.cmdpalette.open)

    def wire(self) -> None:
        """Connect the zones that hand the owner on to another zone."""
        self.coverage.picked.connect(self.open_template)
        self.chat.authored.connect(self.catalogue.reload)
        self.population.open_study.connect(lambda key: self.show_study(self.strategy, key))
        self.population.open_population.connect(lambda key: self.show_study(self.popstudy, key))
        self.strategy.population_wanted.connect(lambda key: self.show_study(self.popstudy, key))
        self.rail.open_step.connect(self.open_step)

    def data_landed(self, piece: str) -> None:
        """A piece of the selected databank finished loading: redraw what reads it.

        Args:
            piece: `metrics`, `trades` or `harvest`.
        """
        now = SELECTION.now
        self.population.load(now["project"], now["databank"])
        self.rail.load(now["project"])
        self.strategy.ficha.where = {}          # its sub-tabs read the cosecha: fill again
        if self.strategy.on_ficha():
            self.strategy.ficha.load(self.strategy.where)

    def open_zone(self, name: str) -> None:
        """Switch to a zone by the name the sidebar shows.

        Args:
            name: One of `nav.ZONES`; a desktop launcher opens the window straight on it
                (`bin/algoui --zone Estrategias`).
        """
        self.stack.setCurrentWidget(self.zones[name])
        for zone, b in self.nav.items():
            b.setChecked(zone == name)

    def show_study(self, page: StrategyPage | PopulationStudy, key: str) -> None:
        """Open one study on the strategy page or on the population-study page.

        Args:
            page: `self.strategy` or `self.popstudy`.
            key: Study key.
        """
        page.open_study(key)
        self.open_zone("Estrategia" if page is self.strategy else "Estudio de población")

    def go_to(self, item: dict) -> None:
        """Open what one palette row points at: by zone name and SELECTION, never by stack index.

        Args:
            item: A row as `cmdpalette.CmdPalette.gather` built it; `kind` says which.
        """
        kind, fields = item["kind"], {k: item[k] for k in ("project", "asset", "databank")
                                      if k in item}
        if kind == "zone":
            self.open_zone(item["label"])
        elif kind == "study":
            one = item["one"] and (SELECTION.now["strategy"] or not item["many"])
            self.show_study(self.strategy if one else self.popstudy, item["study"])
        elif kind == "strategy":
            SELECTION.choose(**fields, strategy=item["label"], identity=item["identity"])
            self.open_zone("Estrategia")
        else:
            SELECTION.choose(**fields)
            self.open_zone("Workflow" if kind == "project" else "Población")

    def open_step(self, step: dict) -> None:
        """A workflow step was clicked: its first study on the population, or the matrix.

        Args:
            step: The step as `GET /api/workflow` sent it; `studies` may be empty (SQX steps).
        """
        if step["studies"]:
            self.show_study(self.popstudy, step["studies"][0])
        else:
            self.open_zone("Población")

    def open_template(self, name: str) -> None:
        """Jump from a coverage cell to that template's page.

        Args:
            name: Template name.
        """
        self.open_zone("Plantillas")
        self.catalogue.select(name)

    def refresh(self) -> None:
        """Reload the library views from the daemon and restate what is on screen.

        The study viewer's zones follow SELECTION and read on their own; `Recargar` covers
        the zones that load once.
        """
        for view in (self.coverage, self.catalogue, self.palettes, self.assets, self.studies,
                     self.gate, self.generation):
            view.reload()
        totals = self.coverage.data
        self.status.setText(
            f"registry.csv · runs.csv · library/  —  {len(totals['rows'])} filas × "
            f"{len(totals['columns'])} timeframes  ·  daemon en 127.0.0.1")
        self.status.setStyleSheet(f"color:{C['faint']};")
