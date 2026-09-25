"""The catalogue: the list of templates and drafts on the left, one page of detail on the right."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QSplitter, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.detail import Detail
from ui.desktop.theme import C, STATUS_COLOUR, VERDICT_COLOUR


def summary(t: dict) -> str:
    """The one line under a template's name in the list.

    Args:
        t: A catalogue entry.

    Returns:
        Its archetype and where it has run, or the reason the row is odd — an orphan run
        or a folder that is not there.
    """
    if t["orphan"]:
        return "solo en runs.csv — no está en el registro"
    markets = " ".join(f"{r['symbol']}·{r['timeframe']}" for r in t["runs"]) or "sin corridas"
    return f"{t.get('archetype') or 'sin arquetipo'} — {markets}"


class Catalogue(QWidget):
    """The list and the detail page, side by side."""

    def __init__(self) -> None:
        """Build the filter row, the list and the detail page."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)
        lay.addWidget(QLabel("Plantillas", objectName="h1"))

        filters = QHBoxLayout()
        self.search = QLineEdit(placeholderText="Buscar por nombre, arquetipo o activo")
        self.search.textChanged.connect(self.fill)
        filters.addWidget(self.search, 1)
        self.status = QComboBox()
        self.status.addItem("Todos los estados", "")
        self.status.currentIndexChanged.connect(self.fill)
        filters.addWidget(self.status)
        lay.addLayout(filters)

        split = QSplitter(Qt.Horizontal)
        self.list = QListWidget()
        self.list.setMinimumWidth(300)
        self.list.currentItemChanged.connect(self.on_select)
        split.addWidget(self.list)
        self.detail = Detail()
        self.detail.changed.connect(self.reload)
        split.addWidget(self.detail)
        split.setSizes([330, 830])
        lay.addWidget(split, 1)

        self.data: dict = {"templates": [], "drafts": []}

    def reload(self) -> None:
        """Fetch the catalogue and redraw the list, keeping the current selection."""
        keep = self.list.currentItem().data(Qt.UserRole) if self.list.currentItem() else None
        self.data = client.get("templates")
        if self.status.count() == 1:
            for s in self.data["statuses"]:
                self.status.addItem(s, s)
        self.fill()
        if keep:
            self.select(keep)

    def fill(self) -> None:
        """Rebuild the list under the current search text and status filter."""
        term = self.search.text().lower()
        want = self.status.currentData()
        self.list.clear()
        for t in self.data["templates"]:
            haystack = " ".join([t["name"], t.get("archetype", ""),
                                 *(r["symbol"] + r["timeframe"] for r in t["runs"])]).lower()
            if term and term not in haystack:
                continue
            if want and t.get("status") != want:
                continue
            self.add_row(t["name"], summary(t), STATUS_COLOUR.get(t.get("status", ""), C["faint"]),
                         t["name"])
        for d in self.data["drafts"]:
            if term and term not in d["name"].lower():
                continue
            if want:
                continue
            self.add_row(f"{d['name']}  ·  borrador",
                         f"{d.get('archetype', '')} — sin autorar, del chat",
                         VERDICT_COLOUR["weak"], None)

    def add_row(self, title: str, subtitle: str, colour: str, name: str | None) -> None:
        """Put one row in the list.

        Args:
            title: The bold first line.
            subtitle: The muted second line.
            colour: The status colour, shown as the row's left marker.
            name: Template name to open on click, or None for a draft, which has no page
                because there is nothing authored to show yet.
        """
        item = QListWidgetItem()
        item.setData(Qt.UserRole, name)
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(10, 4, 6, 4)
        lay.setSpacing(1)
        head = QLabel(title)
        head.setStyleSheet(f"font-weight:600; border-left:3px solid {colour}; padding-left:8px;")
        lay.addWidget(head)
        sub = QLabel(subtitle, objectName="faint")
        sub.setStyleSheet(f"color:{C['faint']}; padding-left:11px;")
        lay.addWidget(sub)
        # A fixed height rather than sizeHint(): the row is measured before it is laid
        # out, and an unlaid two-line widget reports one line, which overlaps the rows.
        item.setSizeHint(QSize(0, 54))
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)

    def on_select(self, item: QListWidgetItem | None) -> None:
        """Open the selected template's page.

        Args:
            item: The row now current, or None when the list was cleared.
        """
        name = item.data(Qt.UserRole) if item else None
        if name:
            self.detail.load(name)

    def select(self, name: str) -> None:
        """Move the selection to one template by name.

        Args:
            name: Template name; ignored when the filters hide it.
        """
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == name:
                self.list.setCurrentRow(i)
                return
