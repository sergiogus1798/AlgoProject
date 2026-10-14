"""The asset zone: every instrument as a page of its own, one per row, full width."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui.desktop import client
from ui.desktop.assetforms import NewAssetBox
from ui.desktop.assetlist import AssetList
from ui.desktop.assetpage import AssetPage


class Assets(QWidget):
    """Every instrument the project knows, and what one costs to trade and where it is tested."""

    def __init__(self) -> None:
        """Build the bar, the index down the left and the grid of pages on the right."""
        super().__init__()
        self.data: dict = {"assets": [], "classes": {}}
        self.pages: dict[str, AssetPage] = {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(QLabel("Activos", objectName="h1"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        row = QHBoxLayout()
        self.counts = QLabel(objectName="muted")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.counts.setToolTip(
            "Bloqueado = algún coste obligatorio sin pactar o el esquema roto: la preflight "
            "sale distinta de 0 y no se autoriza nada. Provisional = hay cifra, se puede "
            "trabajar, y todo resultado con coste arrastra la advertencia."
        )
        new = QPushButton("Nuevo activo")
        new.clicked.connect(self.on_new)
        row.addWidget(self.counts)
        row.addStretch()
        row.addWidget(new)
        lay.addLayout(row)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.list = AssetList()
        self.list.opened.connect(self.show_page)
        split.addWidget(self.list)
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid.setColumnStretch(0, 1)
        holder = QWidget()
        holder.setLayout(self.grid)
        self.area = QScrollArea()
        self.area.setWidget(holder)
        self.area.setWidgetResizable(True)
        self.area.verticalScrollBar().valueChanged.connect(self.read_visible)
        self.area.verticalScrollBar().rangeChanged.connect(
            lambda *_: self.read_visible()
        )
        self.area.setFrameShape(QFrame.Shape.NoFrame)
        split.addWidget(self.area)
        split.setStretchFactor(1, 1)
        split.setSizes([170, 1200])
        lay.addWidget(split, 1)

    def reload(self, keep: str | None = None) -> None:
        """Fetch the library, rebuild every page and redraw the index.

        Args:
            keep: Which asset to leave selected, defaulting to whichever is.
        """
        keep = keep or self.list.selected()
        self.recount()
        for page in self.pages.values():
            page.deleteLater()
        self.pages = {}
        for a in self.data["assets"]:
            page = AssetPage(a["symbol"])
            page.changed.connect(self.on_changed)
            page.retired.connect(lambda *_: self.reload())
            self.pages[a["symbol"]] = page
        for i, page in enumerate(self.pages.values()):
            self.grid.addWidget(page, i, 0)
        self.list.fill(self.data["assets"], keep)
        QTimer.singleShot(0, self.read_visible)

    def showEvent(self, event: QShowEvent) -> None:
        """Read what the zone opens on once it is laid out (the page positions exist by then)."""
        super().showEvent(event)
        QTimer.singleShot(0, self.read_visible)

    def read_visible(self) -> None:
        """Read the pages on screen that have not been read: 28 GETs at once cost 2 s."""
        if not self.isVisible():
            return
        top = self.area.verticalScrollBar().value()
        end = top + self.area.viewport().height()
        for page in self.pages.values():
            if not page.loaded and page.y() < end and page.y() + page.height() > top:
                page.refresh()

    def recount(self) -> None:
        """Read the library's state and say how many assets are blocked or provisional."""
        self.data = client.get("assets")
        blocked = [
            a["symbol"] for a in self.data["assets"] if a["pending"] or a["broken"]
        ]
        soft = [
            a
            for a in self.data["assets"]
            if a["provisional"] and a["symbol"] not in blocked
        ]
        self.counts.setText(
            f"{len(self.data['assets'])} activos · {len(blocked)} bloqueados · "
            f"{len(soft)} sólo con cifras provisionales"
        )

    def show_page(self, symbol: str) -> None:
        """Scroll the grid to one asset's page.

        Args:
            symbol: Asset name picked in the index.
        """
        if symbol in self.pages:
            self.area.verticalScrollBar().setValue(self.pages[symbol].y())
            self.read_visible()

    def on_changed(self, symbol: str) -> None:
        """Redraw the asset just written and the counts, leaving every other page as it is.

        Args:
            symbol: The asset whose file, window or market changed.
        """
        self.pages[symbol].refresh()
        self.recount()
        self.list.blockSignals(
            True
        )  # reselecting it must not scroll away from the edit
        self.list.fill(self.data["assets"], symbol)
        self.list.blockSignals(False)

    def on_new(self) -> None:
        """Ask for a new instrument and add it with every cost undecided."""
        box = NewAssetBox(self.data["classes"])
        if not box.exec():
            return
        answer = client.post("assets/new", box.payload())
        if "error" in answer:
            QMessageBox.warning(self, "Ese nombre ya existe", answer["error"])  # pyright: ignore[reportCallIssue]  # PySide6 stub lists the deprecated overload that wants buttons
            return
        self.reload(answer["created"])
