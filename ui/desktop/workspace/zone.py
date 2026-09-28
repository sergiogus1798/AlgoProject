"""Proyecto: the three strips of one project — rail, funnel, databank panel (22 §4)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QSplitter, QVBoxLayout

from ui.text.numbers import num
from ui.desktop.workspace.advance import Advance
from ui.desktop.workspace.filters import FiltersStrip
from ui.desktop.workspace.funnel import Funnel
from ui.desktop.workspace.gallery import Gallery
from ui.desktop.workspace.panel import Panel
from ui.desktop.workspace.rail import Rail


class WorkspaceZone(QFrame):
    """The workspace. The strips share a vertical splitter, so the databank panel is resized
    by dragging its top edge; folded, it keeps only its header. `strategy_chosen(identity)`
    bubbles up the panel's double click (the shell opens Estrategia)."""

    strategy_chosen = Signal(str)

    def __init__(self) -> None:
        """Build the three strips; `fill` loads a project into them."""
        super().__init__()
        self.setObjectName("term")
        self.title = QLabel("")
        self.title.setObjectName("h1")
        self.title.setStyleSheet("font-size: 20px;")
        self.facts = QLabel("")
        self.facts.setObjectName("dim")
        self.facts.setWordWrap(True)
        self.facts.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.rail, self.funnel, self.panel = Rail(), Funnel(), Panel()
        # F6's strip, right under the panel's header: it follows the panel's databank itself.
        self.panel.layout().insertWidget(1, FiltersStrip(self.panel, self.funnel))
        # F7's «Continuar workflow», at the end of the panel's header.
        self.panel.layout().itemAt(0).layout().addWidget(Advance().attach(self.panel), 2)
        self.rail.opened.connect(self.show_tab)
        self.panel.strategy_chosen.connect(self.strategy_chosen)
        self.panel.run_tab.connect(self.rail.run_panel)
        self.panel.folded.connect(self.fold)
        self.rail.finished.connect(self.panel.refresh)
        self.rail.finished.connect(lambda *_: self.funnel.load(self.panel.project)
                                   if self.panel.live else None)
        self.split = QSplitter(Qt.Vertical)
        self.split.setHandleWidth(6)
        for w in (self.rail, self.funnel, self.panel):
            self.split.addWidget(w)
            self.split.setCollapsible(self.split.indexOf(w), False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        lay.addWidget(self.title)
        lay.addWidget(self.facts)
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
        self.rail.load(name)
        self.funnel.load(name)
        self.panel.fill(name)
        self.split.setSizes([360, 170, 420])

    def card(self, name: str) -> dict:
        """The project's card as the gallery in this window already holds it, or {}.

        No request: `/api/projects/all` costs ~12 s cold, past the client's timeout, and the
        gallery fetched it off the GUI thread before any card could be clicked.
        """
        return next((g.rows[name] for g in self.window().findChildren(Gallery)
                     if name in getattr(g, "rows", {})), {})

    def show_tab(self, tab: str, sub: str = "") -> None:
        """Open one tab of the databank panel and one of its sub-panels — the rail's click.

        Args:
            tab: The panel's top tab.
            sub: The sub-panel, or '' for the tab's first.
        """
        self.panel.select(tab, sub)

    def set_hidden(self, identities: set[str]) -> None:
        """Hide these strategies' rows in the databank panel (the filters of F6)."""
        self.panel.set_hidden(identities)

    def fold(self, folded: bool) -> None:
        """Give the folded panel's height to the funnel, and take it back on unfolding."""
        sizes = self.split.sizes()
        head = self.panel.fold.sizeHint().height() + 16
        if folded:
            self.split.setSizes([sizes[0], sizes[1] + sizes[2] - head, head])
        else:
            self.split.setSizes([sizes[0], 170, sum(sizes) - sizes[0] - 170])
