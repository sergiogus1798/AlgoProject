"""The catalogue of the data root as a tree: each branch's size, files, newest write and signed exports."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem

from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C

COLUMNS = ("árbol", "tamaño", "ficheros", "formatos", "última escritura", "exports firmados",
           "última firma")
HELP = ("La carpeta dentro de AlgoData, hasta tres niveles.",
        "Lo que ocupa en disco todo lo que cuelga de ella.",
        "Cuántos ficheros hay debajo, a cualquier profundidad.",
        "Las tres extensiones más frecuentes y cuántos ficheros de cada una.",
        "La fecha del fichero más reciente de debajo. En ámbar si pasa de los días de "
        "«rancio» de perf/config.yaml.",
        "Cuántos manifest.json hay debajo: cada uno firma un export o un informe con la "
        "fecha y el comando que lo produjo. Una carpeta de datos sin firma no se puede "
        "reproducir.",
        "La fecha más reciente que dice un manifest.json de debajo.")


def size(n: float) -> str:
    """Bytes in the unit a person reads them.

    Args:
        n: Bytes.

    Returns:
        «1.6 GB», «356 MB», «54 KB» or «812 B», the figure through `numbers.num`.
    """
    for unit, scale in (("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if n >= scale:
            return num(round(n / scale, 1 if n < 10 * scale else 0), unit)
    return num(n, "B")


def _item(r: dict, stale_days: int) -> QTreeWidgetItem:
    """One branch's row.

    Args:
        r: A row of `/api/data/catalogue`.
        stale_days: The catalogue's threshold for «rancio».

    Returns:
        The item, figures right-aligned, the command of its own manifest on hover.
    """
    cells = (r["branch"].rsplit("/", 1)[-1], size(r["bytes"]), num(r["files"]), r["formats"],
             r["newest"], num(r["exports"]) if r["exports"] else "—", r["signed"] or "—")
    item = QTreeWidgetItem(list(cells))
    for k in (1, 2, 5):
        item.setTextAlignment(k, Qt.AlignRight | Qt.AlignVCenter)
    if r["stale"]:
        item.setForeground(4, QBrush(QColor(C["weak"])))
        item.setToolTip(4, f"Nada escrito en {num(round(r['age_days']))} días: más de "
                           f"{stale_days}, rancio según perf/config.yaml.")
    item.setToolTip(0, f"AlgoData/{r['branch']}"
                       + (f"\nlo produjo: {r['command']}" if r["command"] else ""))
    return item


def build(body: dict) -> QTreeWidget:
    """The whole catalogue, nested by path, biggest first at every level.

    Args:
        body: The `/api/data/catalogue` body.

    Returns:
        The tree, top-level trees shown and their branches folded.
    """
    tree = QTreeWidget()
    tree.setColumnCount(len(COLUMNS))
    tree.setHeaderLabels([label(c) for c in COLUMNS])
    for k, h in enumerate(HELP):
        tree.headerItem().setToolTip(k, h)
    tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
    tree.setUniformRowHeights(True)
    items: dict[str, QTreeWidgetItem] = {}
    for r in sorted(body["rows"], key=lambda r: (r["depth"], -r["bytes"])):
        item = _item(r, body["stale_days"])
        parent = r["branch"].rsplit("/", 1)[0] if r["depth"] > 1 else ""
        (items[parent].addChild if parent in items else tree.addTopLevelItem)(item)
        items[r["branch"]] = item
    return tree
