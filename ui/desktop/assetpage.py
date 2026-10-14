"""One instrument's page of the asset zone: costs, windows, Cross Market check, traits, raw file."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

from ui.desktop import client
from ui.desktop.assetcard import AssetCard
from ui.desktop.assetspans import AssetSpans
from ui.desktop.assettraits import LEGEND, TRAITS_HELP, trait, traits_table
from ui.desktop.yamltree import YamlTree

MARKETS_WIDTH = 360   # a name, a date and a button per market (owner, 2026-10-04: 310 boxed it in)
SIDE_WIDTH = 290      # two date selectors side by side, and a column of prose under them
PAGE_HEIGHT = 480     # what a filled page measures: an unread one holds the room until it is shown


class AssetPage(QFrame):
    """One instrument: its costs, its windows, its Cross Market check, its trading character,
    and, on demand, its file."""

    changed = Signal(str)   # the asset written, so the zone recounts and redraws only it
    retired = Signal(str)

    def __init__(self, symbol: str) -> None:
        """Build the page; `Assets` fills it from the daemon when it scrolls into view.

        Args:
            symbol: Asset name.
        """
        super().__init__(objectName="panel")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.symbol = symbol
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 10)
        lay.setSpacing(8)
        self.card, self.spans, self.tree = AssetCard(), AssetSpans(), YamlTree()
        self.raw = QPushButton("Fichero entero")
        self.raw.setCheckable(True)
        self.raw.setToolTip("Todos los valores del fichero del activo, cada uno con su comentario.")
        self.raw.toggled.connect(self.on_raw)
        drop = QPushButton("Retirar")
        drop.setToolTip("Mueve el fichero a assets/symbols/_retired/. Deja de contar para "
                        "`core.assets`, pero no se pierde.")
        drop.clicked.connect(self.on_retire)
        self.card.bar.addWidget(self.raw)
        self.card.bar.addWidget(drop)
        self.tree.setVisible(False)
        self.tree.setMinimumHeight(420)
        self.card.changed.connect(lambda: self.changed.emit(symbol))
        self.spans.changed.connect(lambda: self.changed.emit(symbol))
        self.tree.edited.connect(self.on_edit)
        # Three columns (owner, 2026-10-02): what it costs, where its edge is retested — to the
        # right of the costs — and where it is built, each as narrow as what it holds.
        lay.addWidget(self.card.top)
        body = QHBoxLayout()
        body.setSpacing(12)
        costs, side = QVBoxLayout(), QVBoxLayout()
        for col, parts in ((costs, (self.card, self.spans.ranges)), (side, (self.spans,))):
            col.setSpacing(10)
            for w in parts:
                col.addWidget(w, 0, Qt.AlignmentFlag.AlignLeft)
            col.addStretch()
        self.spans.markets.setFixedWidth(MARKETS_WIDTH)
        self.spans.setFixedWidth(SIDE_WIDTH)
        body.addLayout(costs)
        body.addWidget(self.spans.markets)
        body.addLayout(side)
        # To the right of Tramos, on the width that was left empty (owner, 2026-10-04).
        body.addWidget(self.traits_panel(), 1, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(body)
        lay.addWidget(self.tree)
        self.loaded = False
        self.setMinimumHeight(PAGE_HEIGHT)

    def traits_panel(self) -> QFrame:
        """A tile naming how this asset tends to trade — trend, rango, carry.

        Returns:
            The tile, already filled: the note never changes while the page is open, unlike
            the costs and the windows beside it.
        """
        tile = QFrame(objectName="tile")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        tlay = QVBoxLayout(tile)
        tlay.setContentsMargins(10, 8, 10, 8)
        tlay.setSpacing(4)
        title = QLabel("Características (?)", objectName="h2")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        title.setToolTip(TRAITS_HELP)
        tlay.addWidget(title)
        tlay.addWidget(QLabel(LEGEND, objectName="muted"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.prior = QLabel()
        self.prior.setStyleSheet("font-size: 16px;")
        self.prior.setWordWrap(True)
        self.prior.setToolTip(TRAITS_HELP)
        text = QLabel(trait(self.symbol), objectName="muted")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        text.setWordWrap(True)
        tlay.addWidget(self.prior)
        tlay.addWidget(text)
        return tile

    def refresh(self) -> None:
        """Read this asset again and redraw the three parts (the first read happens when it shows)."""
        self.loaded = True
        self.setMinimumHeight(0)
        shown = self.raw.isChecked()       # the raw file is read only while it is open
        data = client.get(f"asset/{self.symbol}", leaves=str(shown).lower())
        self.card.fill(data)
        self.spans.fill(data)
        if shown:
            self.tree.fill(self.symbol, data["leaves"])
        self.prior.setText(traits_table(data["prior"]))

    def on_raw(self, shown: bool) -> None:
        """Show or hide the raw file; opening it reads its leaves."""
        self.tree.setVisible(shown)
        if shown:
            self.refresh()

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
        ok = QMessageBox.question(  # pyright: ignore[reportCallIssue]  # PySide6 stub lists the deprecated overload that wants buttons
            self, f"Retirar {self.symbol}",
            f"El fichero se mueve a assets/symbols/_retired/{self.symbol}.yaml. Deja de existir "
            "para `core.assets` y para el índice, y ninguna tarea nueva podrá usarlo. Sus tramos "
            "se quedan en _policy.yaml. ¿Lo retiro?")
        if ok == QMessageBox.StandardButton.Yes:
            client.post(f"asset/{self.symbol}/retire", {})
            self.retired.emit(self.symbol)
