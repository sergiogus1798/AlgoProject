"""Proyecto: one project's workflow — launchers, rail and funnel; its databanks live in Databanks."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QSizePolicy, QSplitter, QVBoxLayout

from ui.text.numbers import num
from ui.desktop.workspace.advance import Advance
from ui.desktop.workspace.databanks import DatabanksZone
from ui.desktop.workspace.funnel import Funnel
from ui.desktop.workspace.gallery import Gallery
from ui.desktop.workspace.launch import Launcher
from ui.desktop.workspace import railrun
from ui.desktop.workspace.rail import Rail


def scrolled(strip: QFrame) -> QScrollArea:
    """A strip that scrolls instead of imposing its height on the splitter.

    Unwrapped, the rail's three rows of cards asked 476 px and the zone 1,111 px at least:
    on a 1080-px screen the window grew past the bottom edge and cut the databank panel in
    half (owner, 2026-09-28). Wrapped, the splitter can take the rail's height away.
    """
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setWidget(strip)
    return area


class WorkspaceZone(QFrame):
    """Proyecto: title and facts, the two launchers («Lanzar en SQX», «Continuar workflow»),
    then the rail over the funnel in a vertical splitter. It builds and fills the Databanks
    zone too (`databanks`, whose `panel` it exposes: the rail runs on the panel's databank and
    rows). `strategy_chosen(identity)` bubbles up the panel's double click (the shell opens
    Estrategia); `databanks_wanted()` is the drawer's «→ ver en Databanks»."""

    strategy_chosen = Signal(str)
    databanks_wanted = Signal()

    def __init__(self) -> None:
        """Build the strips and the Databanks zone; `fill` loads a project into both."""
        super().__init__()
        self.setObjectName("term")
        self.title = QLabel("")
        self.title.setObjectName("h1")
        self.title.setStyleSheet("font-size: 20px;")
        self.facts = QLabel("")
        self.facts.setObjectName("dim")
        self.facts.setWordWrap(True)
        self.facts.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.rail, self.funnel = Rail(), Funnel()
        self.databanks = DatabanksZone(self.funnel)
        self.panel = self.databanks.panel
        self.launcher = Launcher()   # any task of the project, on its worker (owner, 2026-09-28)
        # F7's «Continuar workflow», with its own databank chooser (owner, 2026-09-28).
        self.advance = Advance().attach(self.panel, self.funnel)
        self.rail.opened.connect(self.show_tab)
        self.rail.drawer.seen.connect(self.see)
        self.panel.strategy_chosen.connect(self.strategy_chosen)
        self.panel.run_tab.connect(
            lambda tab, db, rows: self.panel.say(railrun.panel(self.rail, tab, db, rows)))
        self.dragged = ""      # the project whose split the owner dragged: kept as he left it
        self.rail.loaded.connect(lambda p: QTimer.singleShot(50, lambda: self.size_rail(p)))
        self.rail.loaded.connect(lambda _: self.funnel.name_steps(self.rail.data["steps"]))
        self.rail.finished.connect(self.panel.refresh)
        self.rail.finished.connect(lambda *_: self.funnel.load(self.panel.project)
                                   if self.panel.live else None)
        self.split = QSplitter(Qt.Vertical)
        self.split.setHandleWidth(9)   # the theme paints it: a band to grab, accent on hover
        self.split.splitterMoved.connect(lambda *_: setattr(self, "dragged", self.rail.project))
        for w in (scrolled(self.rail), self.funnel):
            self.split.addWidget(w)
            self.split.setCollapsible(self.split.indexOf(w), False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        lay.addWidget(self.title)
        lay.addWidget(self.facts)
        lay.addWidget(self.launcher)
        lay.addWidget(self.advance)
        lay.addWidget(self.split, 1)

    def fill(self, name: str) -> None:
        """Load one project: its card's facts on top, then the three strips.

        Args:
            name: The project's name, as the gallery sent it; everything is read from the
                daemon.
        """
        p = self.card(name)
        self.title.setText(f"{p.get('symbol') or '?'} · {p.get('timeframe') or '?'}")
        where = p.get("install_label") or p.get("install")
        self.facts.setText(f"{name}   ·   plantilla {p.get('template') or '—'}   ·   "
                           f"{num(p.get('strategies') or 0)} estrategias   ·   "
                           + (f"{p.get('state', '')} en el {where}".strip() if where
                              else "ya no está en ningún install" if p
                              else "sin ficha de la galería todavía"))
        self.launcher.aim(name)
        self.rail.load(name)
        self.funnel.load(name)
        self.databanks.fill(name, p.get("symbol") or "?", p.get("timeframe") or "?")
        self.advance.repoint(name)   # no table modelReset may follow a project change

    def size_rail(self, project: str) -> None:
        """The rail's cards whole when they fit in 70 % of the height; the funnel scrolls.
        Every time the rail lands or the zone shows, until the owner drags the split in this
        project: sized once, while hidden or before the layout, it kept a 95-px band and cut
        the cards (owner, 2026-09-28)."""
        if self.dragged == project or not self.isVisible():
            return
        avail = max(self.split.height(), 300)
        rail = min(self.rail.sizeHint().height() + 8, int(avail * 0.7))
        self.split.setSizes([rail, avail - rail])

    def showEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Size the rail now that the zone has its real height."""
        super().showEvent(event)
        if self.rail.data:
            QTimer.singleShot(50, lambda: self.size_rail(self.rail.project))

    def card(self, name: str) -> dict:
        """The project's card as the gallery in this window already holds it, or {}.

        No request: `/api/projects/all` costs ~12 s cold, past the client's timeout, and the
        gallery fetched it off the GUI thread before any card could be clicked.
        """
        return next((g.rows[name] for g in self.window().findChildren(Gallery)
                     if name in getattr(g, "rows", {})), {})

    def show_tab(self, tab: str, sub: str = "") -> None:
        """Bring one tab of the Databanks panel forward, and one of its sub-panels — the rail's
        click. The zone does not switch: the drawer's «→ ver en Databanks» does (`see`).

        Args:
            tab: The panel's top tab.
            sub: The sub-panel, or '' for the tab's first.
        """
        self.panel.select(tab, sub)

    def set_hidden(self, identities: set[str]) -> None:
        """Hide these strategies' rows in the databank panel (the filters of F6)."""
        self.panel.set_hidden(identities)

    def see(self, tab: str, sub: str) -> None:
        """The drawer's «→ ver en Databanks»: select the step's tab and ask for that zone."""
        self.show_tab(tab, sub)
        self.databanks_wanted.emit()

    def show_databank(self, databank: str) -> None:
        """Bring forward the first tab and sub-panel that read this databank (Ctrl+K's row).

        Args:
            databank: As SQX or the palette spells it; spaces and underscores match.
        """
        same = databank.replace(" ", "_")
        hit = next(((t["tab"], sub["sub"]) for t in self.panel.tabs for sub in t["subs"]
                    if (sub.get("databank") or "").replace(" ", "_") == same), None)
        if hit:
            self.show_tab(*hit)
