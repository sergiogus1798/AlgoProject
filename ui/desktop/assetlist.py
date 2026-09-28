"""The column down the left of the asset zone: every instrument, coloured by what it still needs."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from ui.desktop.assetforms import word as words
from ui.desktop.theme import C


class AssetList(QListWidget):
    """The index of the zone: clicking an asset brings its page into view.

    The shared files moved to Configuración SQX (plan 24, F9) and the retired shelf is not
    shown (encargo 22 §8.1); `/api/assets` still reports the retired ones.
    """

    opened = Signal(str)   # asset name

    def __init__(self) -> None:
        """Build the list and turn a selection into one signal."""
        super().__init__()
        self.setMinimumWidth(150)
        self.setMaximumWidth(210)
        self.currentItemChanged.connect(self.announce)

    def announce(self) -> None:
        """Say what is now selected, ignoring the headings, which select nothing."""
        item = self.currentItem()
        if item and item.data(Qt.UserRole):
            self.opened.emit(item.data(Qt.UserRole))

    def fill(self, assets: list[dict], keep: str | None) -> None:
        """Rebuild the whole column.

        Args:
            assets: One row per instrument, as `/api/assets` reports them.
            keep: Which entry to leave selected.
        """
        self.blockSignals(True)
        self.clear()
        self.section("ACTIVOS")
        for a in assets:
            # Colour and not a glyph: the window's font has no ⛔ and draws a box, and a
            # box beside an instrument reads as breakage rather than as its state.
            blocked = a["pending"] + a["broken"]
            self.entry(a["symbol"],
                       f"{words(a['class'])} · {a['broker']} · {a['sqx_symbol']}"
                       + ("\nbloquea la autoría: " + ", ".join(map(words, blocked))
                          if blocked else "")
                       + ("\ncifras provisionales: " + ", ".join(map(words, a["provisional"]))
                          if a["provisional"] else ""),
                       C["dead"] if blocked else (C["weak"] if a["provisional"] else ""))
        self.blockSignals(False)
        self.select(keep)

    def section(self, title: str) -> None:
        """A heading that cannot be selected.

        Args:
            title: What the section holds.
        """
        item = QListWidgetItem(title)
        item.setFlags(Qt.NoItemFlags)
        item.setForeground(Qt.GlobalColor.gray)
        self.addItem(item)

    def entry(self, label: str, tip: str, colour: str = "") -> None:
        """One selectable row.

        Args:
            label: The asset's name, which is also what it opens.
            tip: What it is, on hover — including, for an asset, what it still needs.
            colour: Hex colour when the row carries a state: red blocks authoring, amber
                means it works but every figure it produces is provisional.
        """
        item = QListWidgetItem(f"  {label}")
        item.setData(Qt.UserRole, label)
        item.setToolTip(tip)
        if colour:
            item.setForeground(QColor(colour))
        self.addItem(item)

    def select(self, keep: str | None) -> None:
        """Leave one entry selected, falling back to the first asset.

        Args:
            keep: The name to reselect, or None. Row 1 is the first asset: row 0 is the
                heading above it, and a heading cannot be current.
        """
        for i in range(self.count()):
            if self.item(i).data(Qt.UserRole) == keep:
                self.setCurrentRow(i)
                return
        self.setCurrentRow(1)

    def selected(self) -> str | None:
        """The name of whatever is open, or None before anything is."""
        item = self.currentItem()
        return item.data(Qt.UserRole) if item else None
