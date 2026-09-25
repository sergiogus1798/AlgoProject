"""The table of blocks under one palette: what each one is, and the override the reader may set."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHeaderView, QTableWidget, QTableWidgetItem

COLUMNS = ("Bloque", "Forma escrita", "Papeles", "Grupos", "Etiqueta", "Peso")
ROLE_ES = {"signal": "señal", "indicator": "indicador", "level": "nivel"}
# The override cell's choices. "—" is not a weight: it means no override, so the block
# follows whatever the taxonomy says and a later relabelling moves it without a second edit.
WEIGHTS = [("—  taxonomía", None), ("0  fuera", 0), ("1  neutro", 1), ("2  encaja", 2),
           ("3  característico", 3)]
SIZING = (QHeaderView.ResizeToContents, QHeaderView.Stretch, QHeaderView.ResizeToContents,
          QHeaderView.ResizeToContents, QHeaderView.ResizeToContents, QHeaderView.ResizeToContents)
# What the taxonomy says about this block for the family on screen. It is the column that
# makes switching family visible: without it the table looks identical across the three,
# because the vocabulary is the same and only the verdict on each block differs.
LABEL_ES = {None: "— sin etiquetar", 0: "0  fuera", 1: "1  neutro", 2: "2  encaja",
            3: "3  característico"}


class BlockTable(QTableWidget):
    """One row per block, with its resolved switch and an editable override."""

    picked = Signal(str, object)

    def __init__(self) -> None:
        """Build the empty table with its five columns."""
        super().__init__(0, len(COLUMNS))
        self.setHorizontalHeaderLabels(COLUMNS)
        self.verticalHeader().setVisible(False)
        for i, mode in enumerate(SIZING):
            self.horizontalHeader().setSectionResizeMode(i, mode)

    def show_blocks(self, rows: list[tuple[str, dict, dict, object, object]]) -> None:
        """Redraw the whole table.

        Args:
            rows: One tuple per block — its key, its taxonomy row, its resolved switch
                (`use`, `weight`, `why`), the override currently set on it or None, and the
                weight the taxonomy gives it for the family on screen, or None.
        """
        # Down to zero before up again: shrinking a QTableWidget leaves its cell widgets
        # alive and reparented, and the survivor from the previous category paints itself
        # over the first row's name.
        self.clearContents()
        self.setRowCount(0)
        self.setRowCount(len(rows))
        for r, (key, block, state, _, label) in enumerate(rows):
            name = QTableWidgetItem(key)
            if not state["use"]:
                name.setForeground(Qt.GlobalColor.gray)
            name.setToolTip(f"{block['origin']} · {block['category']} · decidido por "
                            f"{state['why']}")
            self.setItem(r, 0, name)
            self.setItem(r, 1, QTableWidgetItem(block["form"]))
            self.setItem(r, 2, QTableWidgetItem(", ".join(ROLE_ES[x] for x in block["roles"])))
            groups = QTableWidgetItem(", ".join(block["groups"]) or "—")
            if block["groups"] and not state["use"]:
                groups.setToolTip("Está en un grupo: una plantilla que ate un hueco ahí lo "
                                  "sortea igual, aunque esta paleta lo apague.")
                groups.setForeground(Qt.GlobalColor.yellow)
            self.setItem(r, 3, groups)
            tag = QTableWidgetItem(LABEL_ES.get(label, str(label)))
            if label is None:
                tag.setForeground(Qt.GlobalColor.gray)
                tag.setToolTip("Nadie ha dicho todavía si este bloque pega con esta familia. "
                               "Mientras siga así, las tres paletas lo tratan igual.")
            self.setItem(r, 4, tag)
        # The weight combos go in only once every item exists. Interleaved with setItem,
        # the first row's widget is laid out against a table that has no columns yet and
        # ends up painted over the name column.
        for r, (key, _, _, override, _label) in enumerate(rows):
            self.setCellWidget(r, 5, self.weight_cell(key, override))

    def weight_cell(self, key: str, override: object) -> QComboBox:
        """The override picker for one row.

        Args:
            key: Block key.
            override: The weight currently forced on it, or None to follow the taxonomy.

        Returns:
            A combo that emits `picked` on every change. Editing here writes the palette,
            never the taxonomy: the labels are somebody else's job and two writers on one
            file is how a column drifts.
        """
        box = QComboBox()
        for text, value in WEIGHTS:
            box.addItem(text, value)
        box.setCurrentIndex(box.findData(override))
        box.currentIndexChanged.connect(lambda _, k=key, b=box: self.picked.emit(k, b.currentData()))
        return box
