"""The asset zone: every instrument as a page of its own, one per row, full width."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QScrollArea, QSplitter, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.assetcard import AssetCard
from ui.desktop.assetforms import NewAssetBox
from ui.desktop.assetlist import AssetList
from ui.desktop.assetspans import AssetSpans
from ui.desktop.assettraits import trait
from ui.desktop.yamltree import YamlTree

TRAITS_WIDTH = 320   # a column of prose, not a table: no point growing past a readable line


class AssetPage(QFrame):
    """One instrument: its costs, its windows, its Cross Market check, its trading character,
    and, on demand, its file."""

    changed = Signal(str)   # the asset written, so the zone recounts and redraws only it
    retired = Signal(str)

    def __init__(self, symbol: str) -> None:
        """Build the page and fill it from the daemon.

        Args:
            symbol: Asset name.
        """
        super().__init__(objectName="panel")
        self.symbol = symbol
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(14)
        self.card, self.spans, self.tree = AssetCard(), AssetSpans(), YamlTree()
        self.raw = QPushButton("Fichero entero")
        self.raw.setCheckable(True)
        self.raw.setToolTip("Todos los valores del fichero del activo, cada uno con su comentario.")
        self.raw.toggled.connect(self.tree.setVisible)
        drop = QPushButton("Retirar")
        drop.setToolTip("Mueve el fichero a assets/symbols/_retired/. Deja de contar para "
                        "`core.assets`, pero no se pierde.")
        drop.clicked.connect(self.on_retire)
        self.card.actions.addWidget(self.raw)
        self.card.actions.addWidget(drop)
        self.tree.setVisible(False)
        self.tree.setMinimumHeight(420)
        self.card.changed.connect(lambda: self.changed.emit(symbol))
        self.spans.changed.connect(lambda: self.changed.emit(symbol))
        self.tree.edited.connect(self.on_edit)
        for w in (self.card, self.spans, self.tree):
            left.addWidget(w)
        left.addStretch()
        lay.addLayout(left, 2)
        lay.addWidget(self.traits_panel(), 1)
        self.refresh()

    def traits_panel(self) -> QFrame:
        """A tile naming how this asset tends to trade — trend, rango, carry.

        Returns:
            The tile, already filled: the note never changes while the page is open, unlike
            the costs and the windows beside it.
        """
        tile = QFrame(objectName="tile")
        tile.setMaximumWidth(TRAITS_WIDTH)
        tlay = QVBoxLayout(tile)
        tlay.setContentsMargins(14, 12, 14, 12)
        tlay.setSpacing(6)
        tlay.addWidget(QLabel("Características", objectName="h2"))
        text = QLabel(trait(self.symbol), objectName="muted")
        text.setWordWrap(True)
        tlay.addWidget(text)
        tlay.addStretch()
        return tile

    def refresh(self) -> None:
        """Read this asset again and redraw the three parts."""
        data = client.get(f"asset/{self.symbol}")
        self.card.fill(data)
        self.spans.fill(data)
        self.tree.fill(self.symbol, data["leaves"])

    def on_edit(self, name: str, path: list, text: str, kind: str) -> None:
        """Write a value the file table changed.

        Args:
            name: The file it belongs to.
            path: The keys leading to it.
            text: What was typed.
            kind: "scalar" or "list".
        """
        client.post("assets/value", {"name": name, "path": path, "text": text, "kind": kind})
        self.changed.emit(self.symbol)

    def on_retire(self) -> None:
        """Withdraw this asset after saying what that does."""
        ok = QMessageBox.question(
            self, f"Retirar {self.symbol}",
            f"El fichero se mueve a assets/symbols/_retired/{self.symbol}.yaml. Deja de existir "
            "para `core.assets` y para el índice, y ninguna tarea nueva podrá usarlo. Sus tramos "
            "se quedan en _policy.yaml. ¿Lo retiro?")
        if ok == QMessageBox.Yes:
            client.post(f"asset/{self.symbol}/retire", {})
            self.retired.emit(self.symbol)


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
        lay.addWidget(QLabel("Activos", objectName="h1"))
        row = QHBoxLayout()
        self.counts = QLabel(objectName="muted")
        self.counts.setToolTip(
            "Bloqueado = algún coste obligatorio sin pactar o el esquema roto: la preflight "
            "sale distinta de 0 y no se autoriza nada. Provisional = hay cifra, se puede "
            "trabajar, y todo resultado con coste arrastra la advertencia.")
        new = QPushButton("Nuevo activo")
        new.clicked.connect(self.on_new)
        row.addWidget(self.counts)
        row.addStretch()
        row.addWidget(new)
        lay.addLayout(row)

        split = QSplitter(Qt.Horizontal)
        self.list = AssetList()
        self.list.opened.connect(self.show_page)
        split.addWidget(self.list)
        self.grid = QGridLayout()
        self.grid.setSpacing(14)
        self.grid.setAlignment(Qt.AlignTop)
        self.grid.setColumnStretch(0, 1)
        holder = QWidget()
        holder.setLayout(self.grid)
        self.area = QScrollArea()
        self.area.setWidget(holder)
        self.area.setWidgetResizable(True)
        self.area.setFrameShape(QScrollArea.NoFrame)
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

    def recount(self) -> None:
        """Read the library's state and say how many assets are blocked or provisional."""
        self.data = client.get("assets")
        blocked = [a["symbol"] for a in self.data["assets"] if a["pending"] or a["broken"]]
        soft = [a for a in self.data["assets"] if a["provisional"] and a["symbol"] not in blocked]
        self.counts.setText(f"{len(self.data['assets'])} activos · {len(blocked)} bloqueados · "
                            f"{len(soft)} sólo con cifras provisionales")

    def show_page(self, symbol: str) -> None:
        """Scroll the grid to one asset's page.

        Args:
            symbol: Asset name picked in the index.
        """
        if symbol in self.pages:
            self.area.verticalScrollBar().setValue(self.pages[symbol].y())

    def on_changed(self, symbol: str) -> None:
        """Redraw the asset just written and the counts, leaving every other page as it is.

        Args:
            symbol: The asset whose file, window or market changed.
        """
        self.pages[symbol].refresh()
        self.recount()
        self.list.blockSignals(True)   # reselecting it must not scroll away from the edit
        self.list.fill(self.data["assets"], symbol)
        self.list.blockSignals(False)

    def on_new(self) -> None:
        """Ask for a new instrument and add it with every cost undecided."""
        box = NewAssetBox(self.data["classes"])
        if not box.exec():
            return
        answer = client.post("assets/new", box.payload())
        if "error" in answer:
            QMessageBox.warning(self, "Ese nombre ya existe", answer["error"])
            return
        self.reload(answer["created"])
