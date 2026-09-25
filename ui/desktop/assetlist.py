"""The column down the left of the asset zone: the instruments, the shared files, the retired."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from ui.desktop.theme import C

# The four files that decide for every asset at once. They sit in the same list as the
# assets because they are read in the same breath as one: a cost means nothing without the
# class that gives it its unit, and a window means nothing without the policy that names it.
SHARED = {
    "build": ("Doctrina de construcción",
              "Qué FORMA puede tener una estrategia: complejidad, órdenes, salidas, money "
              "management, precisión y cross-checks. Lo que `doctrine.py` escribe en TODAS "
              "las tareas de un proyecto."),
    "classes": ("Clases de coste",
                "Qué campos tiene cada clase, en qué unidad y sobre qué ajuste de SQX. "
                "Cambiarlo revalida los 19 ficheros a la vez."),
    "policy": ("Política y tramos",
               "Qué ES cada tramo, y dónde empieza y acaba en cada activo: los 19 juntos, "
               "para poder compararlos de un vistazo."),
    "markets": ("Universo de retest",
                "Por activo main, en qué otros mercados hay que comprobar que el edge "
                "sobrevive. La lista se fija ANTES de mirar ningún resultado."),
}


class AssetList(QListWidget):
    """What the zone can open, marked with what each entry still needs decided."""

    opened = Signal(str, str)   # kind (asset | shared | retired), name

    def __init__(self) -> None:
        """Build the list and turn a selection into one signal."""
        super().__init__()
        self.setMinimumWidth(250)
        self.currentItemChanged.connect(self.announce)

    def announce(self) -> None:
        """Say what is now selected, ignoring the headings, which select nothing."""
        item = self.currentItem()
        if item and item.data(Qt.UserRole):
            self.opened.emit(*item.data(Qt.UserRole))

    def fill(self, assets: list[dict], retired: list[str], keep: str | None) -> None:
        """Rebuild the whole column.

        Args:
            assets: One row per instrument, as `/api/assets` reports them.
            retired: Names on the retired shelf.
            keep: Which entry to leave selected.
        """
        self.blockSignals(True)
        self.clear()
        self.section("ACTIVOS")
        for a in assets:
            # Colour and not a glyph: the window's font has no ⛔ and draws a box, and a
            # box beside an instrument reads as breakage rather than as its state.
            blocked = a["pending"] or a["broken"]
            self.entry(a["symbol"], ("asset", a["symbol"]),
                       f"{a['class']} · {a['broker']} · {a['sqx_symbol']}"
                       + ("\nbloquea la autoría: " + ", ".join(a["pending"] + a["broken"])
                          if a["pending"] or a["broken"] else "")
                       + ("\ncifras provisionales: " + ", ".join(a["provisional"])
                          if a["provisional"] else ""),
                       C["dead"] if blocked else (C["weak"] if a["provisional"] else ""))
        self.section("COMPARTIDO — decide para todos")
        for name, (label, what) in SHARED.items():
            self.entry(label, ("shared", name), what)
        if retired:
            self.section("RETIRADOS")
            for symbol in retired:
                self.entry(symbol, ("retired", symbol), "Fuera de la librería, no perdido.")
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

    def entry(self, label: str, what: tuple, tip: str, colour: str = "") -> None:
        """One selectable row.

        Args:
            label: What it says.
            what: (kind, name), which decides the page it opens.
            tip: What it is, on hover — including, for an asset, what it still needs.
            colour: Hex colour when the row carries a state: red blocks authoring, amber
                means it works but every figure it produces is provisional.
        """
        item = QListWidgetItem(f"  {label}")
        item.setData(Qt.UserRole, what)
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
            data = self.item(i).data(Qt.UserRole)
            if data and data[1] == keep:
                self.setCurrentRow(i)
                return
        self.setCurrentRow(1)

    def selected(self) -> str | None:
        """The name of whatever is open, or None before anything is."""
        item = self.currentItem()
        return item.data(Qt.UserRole)[1] if item and item.data(Qt.UserRole) else None
