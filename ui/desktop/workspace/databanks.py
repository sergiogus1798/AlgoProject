"""Databanks: the project's databank panel on the whole height, with its filters strip."""

from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ui.desktop.workspace.filters import FiltersStrip
from ui.desktop.workspace.panel import Panel


class DatabanksZone(QFrame):
    """The Databanks zone: a title line, then the panel (filters, tabs, table, equity).

    Built by Proyecto's `WorkspaceZone`, which fills it with the same project and keeps the
    funnel: the filters strip reloads that funnel even though it lives in the other zone.
    """

    def __init__(self, funnel: QWidget) -> None:
        """Build the panel and mount the filters strip under its header.

        Args:
            funnel: Proyecto's `Funnel`, reloaded after every filter.
        """
        super().__init__()
        self.setObjectName("term")
        self.title = QLabel("")
        self.title.setObjectName("h1")
        self.title.setStyleSheet("font-size: 20px;")
        self.title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.panel = Panel()
        # F6's strip, right under the panel's header: it follows the panel's databank itself.
        self.panel.layout().insertWidget(1, FiltersStrip(self.panel, funnel))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        lay.addWidget(self.title)
        lay.addWidget(self.panel, 1)

    def fill(self, name: str, symbol: str, timeframe: str) -> None:
        """Load one project into the panel.

        Args:
            name: The project's name.
            symbol, timeframe: From the gallery's card, '?' when it has none.
        """
        self.title.setText(f"{name} · {symbol} · {timeframe}")
        self.panel.fill(name)
