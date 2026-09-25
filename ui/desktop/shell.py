"""The window itself: persistent side navigation, one module inside, one status bar."""

from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from ui.desktop.assets import Assets
from ui.desktop.catalogue import Catalogue
from ui.desktop.chat import Chat
from ui.desktop.coverage import Matrix
from ui.desktop.palettes import Palettes
from ui.desktop.soon import ZONES as SOON, page as soon_page
from ui.desktop.studies import Studies
from ui.desktop.theme import C

# The zones of the unified platform, in the order the study fixed them. The three template
# views are built; the rest open a page saying what will live there and how the job is done
# today — reachable rather than greyed out, because a disabled button in Qt never shows its
# tooltip, so five dead entries would explain nothing at all.
ZONES = ["Cobertura", "Plantillas", "Nueva plantilla", "Paletas", "Activos", "Estrategias",
         *SOON]


class Shell(QWidget):
    """The single window. Everything else is a view inside it."""

    def __init__(self) -> None:
        """Build the sidebar, the stack of views and the status bar, and load the data."""
        super().__init__()
        self.setWindowTitle("AlgoProject — Plantillas")
        self.resize(1360, 880)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.matrix = Matrix()
        self.catalogue = Catalogue()
        self.chat = Chat()
        self.palettes = Palettes()
        self.assets = Assets()
        self.studies = Studies()
        self.matrix.picked.connect(self.open_template)
        self.chat.authored.connect(self.catalogue.reload)

        right = QVBoxLayout()
        right.setContentsMargins(24, 20, 24, 14)
        right.setSpacing(12)
        self.stack = QStackedWidget()
        for view in (self.matrix, self.catalogue, self.chat, self.palettes, self.assets,
                     self.studies):
            self.stack.addWidget(view)
        for name in SOON:
            self.stack.addWidget(soon_page(name))
        right.addWidget(self.stack, 1)
        self.status = QLabel("", objectName="faint")
        right.addWidget(self.status)
        # The sidebar is built last because it selects a view, and selecting one needs the
        # stack to exist; it is inserted first so it still sits down the left.
        lay.insertWidget(0, self.sidebar())
        lay.addLayout(right, 1)

        self.refresh()

    def sidebar(self) -> QFrame:
        """The persistent navigation down the left.

        Returns:
            A framed column of buttons, the unbuilt zones present but disabled.
        """
        f = QFrame(objectName="sidebar")
        f.setFixedWidth(208)
        lay = QVBoxLayout(f)
        lay.setContentsMargins(0, 18, 0, 14)
        lay.setSpacing(2)
        brand = QLabel("  AlgoProject")
        brand.setStyleSheet("font-size:16px; font-weight:700; padding:0 16px 14px 16px;")
        lay.addWidget(brand)

        self.nav = []
        for i, name in enumerate(ZONES):
            b = QPushButton(name, objectName="nav")
            b.setCheckable(True)
            if name in SOON:
                b.setProperty("soon", True)
                b.setToolTip(f"{name}: todavía no. Ábrela para ver qué irá ahí y cómo se hace "
                             "hoy mientras tanto.")
            b.clicked.connect(lambda _, n=i: self.go(n))
            lay.addWidget(b)
            self.nav.append(b)
        lay.addStretch()
        reload_btn = QPushButton("Recargar")
        reload_btn.clicked.connect(self.refresh)
        holder = QVBoxLayout()
        holder.setContentsMargins(12, 0, 12, 0)
        holder.addWidget(reload_btn)
        lay.addLayout(holder)
        self.go(0)
        return f

    def go(self, index: int) -> None:
        """Switch to one view.

        Args:
            index: Position in `ZONES`. Every position has a page: the first three are the
                template views, the rest their "not yet" page.
        """
        self.stack.setCurrentIndex(index)
        for i, b in enumerate(self.nav):
            b.setChecked(i == index)

    def open_zone(self, name: str) -> None:
        """Switch to a zone by the name the sidebar shows.

        Args:
            name: One of `ZONES`; a desktop launcher opens the window straight on it.
        """
        self.go(ZONES.index(name))

    def open_template(self, name: str) -> None:
        """Jump from a matrix cell to that template's page.

        Args:
            name: Template name.
        """
        self.go(1)
        self.catalogue.select(name)

    def refresh(self) -> None:
        """Reload every view from the daemon and restate what is on screen."""
        self.matrix.reload()
        self.catalogue.reload()
        self.palettes.reload()
        self.assets.reload()
        self.studies.reload()
        totals = self.matrix.data
        self.status.setText(
            f"registry.csv · runs.csv · library/  —  {len(totals['rows'])} filas × "
            f"{len(totals['columns'])} timeframes  ·  daemon en 127.0.0.1")
        self.status.setStyleSheet(f"color:{C['faint']};")
