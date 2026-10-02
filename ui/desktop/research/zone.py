"""BIBLIOTECA › Investigar: the four views of the research director in one terminal frame."""

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QLabel, QTabWidget, QVBoxLayout

from ui.desktop.blocks.card import text
from ui.desktop.research.directview import DirectView
from ui.desktop.research.mapview import MapView
from ui.desktop.research.memoryview import MemoryView
from ui.desktop.research.proposalview import ProposalView
from ui.desktop.studypage.net import fetch as daemon_fetch
from ui.desktop.studypage.net import send as daemon_send
from ui.desktop.theme import T

INTRO = ("Dónde investigar y con qué: Python mide los mercados y cuenta lo probado; el director "
         "lee una página, elige una celda y trae tres ideas con sus bloques. Tú vetas y lanzas.")


class ResearchZone(QFrame):
    """Mapa · Memoria · Proponer investigación · Propuesta."""

    def __init__(self, fetch: Callable[..., dict] = daemon_fetch,
                 send: Callable[[str, dict], dict] = daemon_send) -> None:
        """Build the four views; nothing is asked of the daemon until the zone is shown.

        Args:
            fetch: GET a daemon route, never raising; a fake makes every call synchronous.
            send: POST a daemon route, never raising.
        """
        super().__init__()
        self.setObjectName("term")
        self.loaded = False
        sync = fetch is not daemon_fetch
        self.map = MapView(fetch, sync)
        self.memory = MemoryView(fetch, sync)
        self.direct = DirectView(fetch, send, sync)
        self.proposal = ProposalView(fetch, send, sync)
        self.tabs = QTabWidget()
        for name, view in (("Mapa", self.map), ("Memoria", self.memory),
                           ("Proponer investigación", self.direct), ("Propuesta", self.proposal)):
            self.tabs.addTab(view, name)
        self.direct.proposed.connect(self.arrived)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)
        lay.addWidget(QLabel("BIBLIOTECA", objectName="kicker"))
        lay.addWidget(QLabel("Investigar", objectName="h1"))
        lay.addWidget(text(INTRO, T["muted"], 13))
        lay.addWidget(QFrame(objectName="rule"))
        lay.addWidget(self.tabs, 1)

    def showEvent(self, event: object) -> None:
        """Load the four views the first time the zone is shown."""
        super().showEvent(event)
        if not self.loaded:
            self.loaded = True
            self.reload()

    def reload(self) -> None:
        """Read everything again («Recargar»)."""
        for view in (self.map, self.memory, self.direct, self.proposal):
            view.reload()

    def arrived(self) -> None:
        """The director ended: show its proposal."""
        self.proposal.reload()
        self.tabs.setCurrentWidget(self.proposal)
